from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from typing import Annotated, List, Dict, Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from db import get_db
import models
import auth_router
from utils.qr_utils import generate_qr_image_and_payload
from utils.pdf_utils import generate_hall_ticket_buffer

router = APIRouter(prefix="/hall-tickets", tags=["hall-tickets"])


# In-memory storage for reports (In production, move this to Firestore/DB)
DISPATCH_REPORTS = {}

async def generate_and_save_ticket_task(student_data: dict, app_id: str, batch_id: str, is_retry: bool = False):
    """
    Attempts to generate a hall ticket. If it fails, logs the reason.
    If it's a retry, it updates the existing record instead of creating a new one.
    """
    report = DISPATCH_REPORTS.get(batch_id)
    if not report: return

    student_id = student_data.get('student_id', 'UNKNOWN')
    roll_no = student_data.get('roll', 'N/A')
    branch = student_data.get('branch', 'General')

    try:
        # 1. Validation Check
        required_fields = ['student_id', 'roll', 'seat_id', 'room_id', 'exam_id']
        missing = [f for f in required_fields if not student_data.get(f)]
        if missing:
            raise ValueError(f"Data Missing: {', '.join(missing)}")

        # 2. Generate QR Code (Internally)
        try:
            unique_token = f"TOKEN_{student_id}_{uuid.uuid4().hex[:4]}"
            
            # Use the internal utility function directly
            qr_base64, qr_payload = generate_qr_image_and_payload(
                student_id=str(student_id),
                roll_number=str(roll_no),
                seat_id=str(student_data['seat_id']),
                exam_id=str(student_data['exam_id']),
                allocated_room=str(student_data['room_id']), 
                unique_token=unique_token
            )
        except Exception as e:
            raise Exception(f"Internal QR Generation Failed: {str(e)}")

        # 3. Simulate PDF Storage
        target_dir = STORAGE_BASE / app_id / "users" / str(student_id) / "hall_tickets"
        target_dir.mkdir(parents=True, exist_ok=True)
        with open(target_dir / "hall_ticket.pdf", "w") as f:
            f.write(f"Hall Ticket Data | QR Payload: {qr_payload}")

        # 4. Update Report
        status_entry = {"roll": roll_no, "branch": branch, "status": "SUCCESS", "error": None}
        
        if is_retry:
            # Replace the old failed entry
            report["details"] = [d for d in report["details"] if d["roll"] != roll_no]
            report["summary"]["failure_count"] -= 1
        
        report["details"].append(status_entry)
        report["summary"]["success_count"] += 1

    except Exception as e:
        error_msg = str(e)
        if not is_retry:
            report["details"].append({"roll": roll_no, "branch": branch, "status": "FAILED", "error": error_msg})
            report["summary"]["failure_count"] += 1
        else:
            # Update the error message for the retry attempt
            for d in report["details"]:
                if d["roll"] == roll_no:
                    d["error"] = f"Retry Failed: {error_msg}"
        
        # print(f"BATCH ERROR [{batch_id}]: Student {roll_no} -> {error_msg}")

# --- DISPATCH ENDPOINTS ---

@router.post("/dispatch/finalize")
async def finalize_and_dispatch(
    app_id: str, 
    assignments: List[Dict[str, Any]], 
    background_tasks: BackgroundTasks
):
    """
    Start a batch dispatch process for hall tickets.
    """
    batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:4].upper()}"
    
    DISPATCH_REPORTS[batch_id] = {
        "batch_id": batch_id,
        "app_id": app_id,
        "timestamp": datetime.now().isoformat(),
        "original_assignments": assignments, # Store data for potential retries
        "summary": {"total_requested": len(assignments), "success_count": 0, "failure_count": 0},
        "details": []
    }

    for student in assignments:
        background_tasks.add_task(generate_and_save_ticket_task, student, app_id, batch_id)
        
    return {"status": "STARTED", "batch_id": batch_id}

@router.post("/dispatch/{batch_id}/retry")
async def retrigger_failed_dispatch(
    batch_id: str, 
    background_tasks: BackgroundTasks
):
    """
    Finds all students who failed in the given batch and retries only those.
    """
    report = DISPATCH_REPORTS.get(batch_id)
    if not report:
        raise HTTPException(status_code=404, detail="Batch ID not found.")

    failed_rolls = [d["roll"] for d in report["details"] if d["status"] == "FAILED"]
    
    if not failed_rolls:
        return {"message": "No failed tickets to retry in this batch."}

    # Filter original data for only the failed students
    to_retry = [s for s in report["original_assignments"] if s["roll"] in failed_rolls]

    for student in to_retry:
        background_tasks.add_task(generate_and_save_ticket_task, student, report["app_id"], batch_id, is_retry=True)

    return {
        "status": "RETRY_STARTED",
        "retrying_count": len(to_retry),
        "message": f"Attempting to fix {len(to_retry)} failed tickets."
    }

@router.get("/dispatch/{batch_id}/report")
async def get_dispatch_report(batch_id: str):
    """
    Get the status report for a dispatch batch.
    """
    report = DISPATCH_REPORTS.get(batch_id)
    if not report: raise HTTPException(status_code=404, detail="Batch ID not found.")

    branch_map = {}
    for entry in report["details"]:
        br = entry["branch"]
        if br not in branch_map: branch_map[br] = {"success": [], "failed": []}
        if entry["status"] == "SUCCESS": branch_map[br]["success"].append(entry["roll"])
        else: branch_map[br]["failed"].append({"roll": entry["roll"], "reason": entry["error"]})

    return {
        "metadata": report["summary"],
        "branch_wise_status": branch_map
    }

class VerificationRequest(BaseModel):
    raw_payload: str = Field(..., description="The full decoded string from the QR code.")
    invigilator_exam_id: str = Field(..., description="Exam ID configured on scanner.")
    invigilator_room_id: str = Field(None, description="Physical room ID where the scanner is located.")

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
        allocated_room=allocation.room.name,
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
        # Use split(':', 1) to be safer with values containing colons
        # Trim whitespace from the raw payload
        clean_payload = req.raw_payload.strip()
        print(f"DEBUG: Verifying QR Payload: {clean_payload}")
        
        parts = {}
        for p in clean_payload.split('|'):
            if ':' in p:
                key, val = p.split(':', 1)
                parts[key.strip()] = val.strip()
        
        roll_number = parts.get('ROLL')
        exam_id_str = parts.get('EXAM')
        seat_label = parts.get('SEAT')
        scanned_room = parts.get('ROOM') # Extract scanned room from QR payload
        
        # Only ROLL, EXAM, and SEAT are strictly required for identity
        if not roll_number or not exam_id_str or not seat_label:
             print(f"DEBUG: Missing fields in parts: {parts}")
             return {"status": "MISMATCH", "message": "Invalid QR format or missing data"}

        # 2. Check Contexts
        # Check Exam Match
        if exam_id_str != req.invigilator_exam_id:
             return {"status": "MISMATCH", "message": f"Wrong Exam! Ticket for {exam_id_str}"}

        # Check Room Match (Location Security)
        if req.invigilator_room_id and scanned_room != req.invigilator_room_id:
             return {"status": "MISMATCH", "message": f"Wrong Room! Allocated to {scanned_room}"}

        # 3. Verify Database Record
        student = db.query(models.Student).filter(models.Student.roll_number == roll_number).first()
        if not student:
             return {"status": "MISMATCH", "message": "Student not found"}

        allocation = db.query(models.SeatAllocation).filter(
            models.SeatAllocation.exam_id == int(exam_id_str),
            models.SeatAllocation.student_id == student.id
        ).first()

        if not allocation:
             return {"status": "MISMATCH", "message": "No seat allocated"}

        if allocation.seat.seat_label != seat_label:
             return {"status": "MISMATCH", "message": "Seat Mismatch"}

        # 4. Success - Return format expected by scanner_app.py
        return {
            "status": "MATCH",
            "message": "Verified",
            "student_info": {
                "id": parts.get('ID'),
                "roll": roll_number,
                "seat": seat_label,
                "name": student.user.name
            }
        }

    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

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
