from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from typing import Annotated
from pydantic import BaseModel, Field

from db import get_db
import models
import auth_router
from utils.qr_utils import generate_qr_image_and_payload
from utils.pdf_utils import generate_hall_ticket_buffer

router = APIRouter(prefix="/hall-tickets", tags=["hall-tickets"])

class VerificationRequest(BaseModel):
    raw_payload: str = Field(..., description="The full decoded string from the QR code.")
    scanner_exam_id: str = Field(..., description="Exam ID configured on scanner.")

@router.get("/{exam_id}/download")
def download_hall_ticket(
    exam_id: int,
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    Generate and download Hall Ticket PDF for the logged-in student and specific exam.
    """
    # 1. Identify Student
    student = db.query(models.Student).options(
        joinedload(models.Student.branch).joinedload(models.Branch.program)
    ).filter(models.Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")

    # 2. Get Exam Details
    exam = db.query(models.Exams).options(joinedload(models.Exams.course)).filter(models.Exams.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")

    # 3. Get Seat Allocation
    allocation = db.query(models.SeatAllocation).options(
        joinedload(models.SeatAllocation.room),
        joinedload(models.SeatAllocation.seat)
    ).filter(
        models.SeatAllocation.exam_id == exam_id,
        models.SeatAllocation.student_id == student.id
    ).first()

    if not allocation:
        raise HTTPException(status_code=404, detail="No seat allocated for this exam yet.")

    # 4. Generate QR Token/Payload
    # In a real system, we might save this token to a DB to track "is_used".
    # Here we generate a stateless signed-like payload.
    # Token = Simple Hash of IDs for now (or UUID).
    import hashlib
    token_source = f"{student.id}-{exam.id}-{allocation.seat.seat_label}"
    unique_token = hashlib.sha256(token_source.encode()).hexdigest()[:10].upper()

    qr_base64, raw_payload = generate_qr_image_and_payload(
        student_id=str(student.roll_number), # Using Roll No as ID in QR for visibility
        roll_number=student.roll_number,
        seat_id=allocation.seat.seat_label,
        exam_id=str(exam.id), # Internal ID
        unique_token=unique_token
    )

    # 5. Generate PDF
    # Priority: Course Title > Course Name > Exam Title > Course Code > "Exam"
    title_text = "Exam"
    if exam.course:
        title_text = exam.course.title or exam.course.name or exam.course.code or "Exam"
    
    # If course missing or title empty, try exam's own title
    if title_text == "Exam" and exam.exam_title:
        title_text = exam.exam_title

    pdf_buffer = generate_hall_ticket_buffer(
        student_name=current_user.name or current_user.email.split('@')[0],
        roll_number=student.roll_number,
        course_name=student.branch.program.name if (student.branch and student.branch.program) else "Academix Program", # Fixed attribute access
        exam_title=title_text,
        exam_date=exam.exam_date.strftime("%Y-%m-%d"),
        exam_time=exam.start_time.strftime("%I:%M %p"),
        room_name=allocation.room.name,
        seat_name=allocation.seat.seat_label,
        qr_base64=qr_base64,
        exam_type=exam.exam_type or "SEMESTER"
    )

    # 6. Return File
    filename = f"HallTicket_{student.roll_number}_{exam.course.code if exam.course else exam_id}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/verify")
def verify_qr_token(
    req: VerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify a scanned QR code.
    Payload Format: ID:STU...|ROLL:...|SEAT:...|EXAM:...|TOKEN:...
    """
    try:
        # 1. Parse Payload
        parts = {p.split(':')[0]: p.split(':')[1] for p in req.raw_payload.split('|') if ':' in p}
        
        roll_number = parts.get('ROLL')
        exam_id_str = parts.get('EXAM')
        seat_label = parts.get('SEAT')
        
        if not roll_number or not exam_id_str or not seat_label:
             return {"status": "FAILURE", "message": "Invalid QR format", "valid": False}

        # 2. Check Exam Context
        # req.scanner_exam_id might be the DB ID or Code. Assuming DB ID for consistency.
        if exam_id_str != req.scanner_exam_id:
             return {"status": "FAILURE", "message": "Exam Mismatch", "valid": False}

        # 3. Verify Database Record
        # Find student by roll number
        student = db.query(models.Student).filter(models.Student.roll_number == roll_number).first()
        if not student:
             return {"status": "FAILURE", "message": "Student not found", "valid": False}

        # Check allocation
        allocation = db.query(models.SeatAllocation).filter(
            models.SeatAllocation.exam_id == int(exam_id_str),
            models.SeatAllocation.student_id == student.id
        ).first()

        if not allocation:
             return {"status": "FAILURE", "message": "No seat allocated for this student", "valid": False}

        # Check Seat Match
        if allocation.seat.seat_label != seat_label:
             return {"status": "FAILURE", "message": "Seat Mismatch (Forged Ticket?)", "valid": False}

        # 4. Success
        return {
            "status": "SUCCESS",
            "message": "Verified",
            "valid": True,
            "student": {
                "name": student.user.name,
                "roll": roll_number
            },
            "seat": seat_label
        }

    except Exception as e:
        return {"status": "ERROR", "message": str(e), "valid": False}

@router.get("/all")
def get_all_hall_tickets(
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    Get all generated hall tickets (seat allocations) for Seating Managers.
    """
    # Verify role (Admin or Seating Manager)
    if current_user.role not in ["Admin", "Seating Manager"]:
         raise HTTPException(status_code=403, detail="Not authorized")

    allocations = db.query(models.SeatAllocation).options(
        joinedload(models.SeatAllocation.student).joinedload(models.Student.user),
        joinedload(models.SeatAllocation.exam).joinedload(models.Exams.course),
        joinedload(models.SeatAllocation.seat),
        joinedload(models.SeatAllocation.room)
    ).all()

    results = []
    for alloc in allocations:
        # Determine status - if allocation exists, it's technically "Generated" or "Ready"
        # We can refine this logic later if we have explicit status flags
        status = "Generated" 
        
        exam_title = "Exam"
        if alloc.exam.course:
            exam_title = alloc.exam.course.title or alloc.exam.course.name
        elif alloc.exam.exam_title:
            exam_title = alloc.exam.exam_title

        results.append({
            "id": alloc.id,
            "name": alloc.student.user.name,
            "roll": alloc.student.roll_number,
            "exam": exam_title,
            "seat": alloc.seat.seat_label,
            "status": status,
            "room_name": alloc.room.name
        })

    return results
