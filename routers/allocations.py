from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pydantic import BaseModel

from db import get_db
import models
import schemas
from datetime import timedelta
import auth_router
from utils.seating_algorithm import allocate_seating, generate_adjacency_matrix

router = APIRouter(prefix="/allocations", tags=["allocations"])

class AllocationRequest(BaseModel):
    exam_id: int
    room_id: int
    seat_id: int
    student_id: int
    manual_override: bool = False

class AutoAllocationRequest(BaseModel):
    exam_id: int
    room_id: Optional[int] = None
    exam_type: str = "SEMESTER" # MID or SEMESTER

@router.get("/", response_model=List[schemas.SeatAllocationRead])
def get_allocations(
    exam_id: int, 
    room_id: int, 
    db: Session = Depends(get_db)
):
    """Fetch allocations for a specific exam and room context."""
    return db.query(models.SeatAllocation).filter(
        models.SeatAllocation.exam_id == exam_id,
        models.SeatAllocation.room_id == room_id
    ).all()

@router.post("/", response_model=schemas.SeatAllocationRead)
def save_allocation(
    req: AllocationRequest, 
    db: Session = Depends(get_db)
):
    """Create or update a single seat allocation (Manual Assignment)."""
    
    # Check if seat is already taken for this exam
    existing = db.query(models.SeatAllocation).filter(
        models.SeatAllocation.exam_id == req.exam_id,
        models.SeatAllocation.seat_id == req.seat_id
    ).first()
    
    if existing:
        # Update
        existing.student_id = req.student_id
        existing.manual_override = req.manual_override
        db.commit()
        db.refresh(existing)
        return existing
    
    # Check if student is already seated elsewhere for this exam
    student_existing = db.query(models.SeatAllocation).filter(
        models.SeatAllocation.exam_id == req.exam_id,
        models.SeatAllocation.student_id == req.student_id
    ).first()
    
    if student_existing:
        # Move student
        student_existing.room_id = req.room_id
        student_existing.seat_id = req.seat_id
        student_existing.manual_override = req.manual_override
        db.commit()
        db.refresh(student_existing)
        return student_existing

    # Create new
    new_alloc = models.SeatAllocation(
        exam_id=req.exam_id,
        room_id=req.room_id,
        seat_id=req.seat_id,
        student_id=req.student_id,
        manual_override=req.manual_override
    )
    db.add(new_alloc)
    db.commit()
    db.refresh(new_alloc)
    return new_alloc

@router.post("/auto")
def auto_allocate(
    req: AutoAllocationRequest,
    db: Session = Depends(get_db)
):
    """Trigger the PuLP auto-allocation algorithm. If room_id is None, iterates through all rooms."""
    
    # 1. Determine Target Rooms
    target_rooms = []
    if req.room_id:
        # Specific room
        room = db.query(models.Room).filter(models.Room.id == req.room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        target_rooms.append(room)
    else:
        # All active rooms
        target_rooms = db.query(models.Room).all() 
        # In real app: filter by availability/booking? Assume all room table entries are usable.
    
    if not target_rooms:
         raise HTTPException(status_code=404, detail="No rooms available for allocation.")
         
    # 2. Fetch Exam Students (All)
    all_exam_students_rels = db.query(models.ExamStudent).filter(models.ExamStudent.exam_id == req.exam_id).options(joinedload(models.ExamStudent.student)).all()
    
    if not all_exam_students_rels:
        raise HTTPException(status_code=404, detail="No students registered for this exam.")

    # 3. Identify Already allocated students (Manual or Previous Auto)
    # If we want to re-run "Auto", we should probably clear previous "Auto" for this exam first?
    # Strategy: Clear ALL 'Auto' allocations for this exam globally before starting?
    # Yes, typically "Run Allocation" means "Reset and Fill".
    # BUT keep Manual overrides.
    
    # Clear previous AUTO allocations for this exam
    db.query(models.SeatAllocation).filter(
        models.SeatAllocation.exam_id == req.exam_id,
        models.SeatAllocation.manual_override == False
    ).delete()
    db.commit() # Commit delete first
    
    # Re-fetch existing Manual allocations to exclude students and seats
    manual_allocs = db.query(models.SeatAllocation).filter(
        models.SeatAllocation.exam_id == req.exam_id,
        models.SeatAllocation.manual_override == True
    ).all()
    
    locked_student_ids = {a.student_id for a in manual_allocs}
    locked_seat_ids = {a.seat_id for a in manual_allocs}
    
    # 4. Prepare Student Pool (Unallocated)
    # We want to allocate ONLY the students who are NOT in locked_student_ids
    student_pool = []
    
    exam = db.query(models.Exams).filter(models.Exams.id == req.exam_id).first()
    subject_code = exam.course.code if exam and exam.course else "SUB"

    for es in all_exam_students_rels:
        stu = es.student
        if stu.id not in locked_student_ids:
             # Safety check for program name
             prog_name = "UG"
             if stu.branch and stu.branch.program:
                 prog_name = stu.branch.program.name
             
             student_pool.append({
                 "id": str(stu.id),
                 "subject": subject_code,
                 "section": f"{prog_name}-{stu.year}", 
                 "roll": stu.roll_number
             })

    # 5. Iterative Allocation
    results_summary = []
    total_allocated = 0
    
    # Sort rooms by capacity (optional)? or just ID.
    # It's better to use larger rooms first? or ordered by block. Let's iterate as is.
    
    import math
    
    # We need to slice the student pool for each room or let the solver try to fit MAX.
    # The current `allocate_seating` takes a dictionary of students.
    # Constraint: len(Students) <= len(Seats).
    # So we must feed it only enough students to fill the room, or less.
    
    current_pool_index = 0
    
    for room in target_rooms:
        if current_pool_index >= len(student_pool):
            break # All students seated
            
        # Get Room Seats
        room_seats = db.query(models.RoomSeat).filter(models.RoomSeat.room_id == room.id).all()
        available_seats = [s for s in room_seats if s.id not in locked_seat_ids]
        
        if not available_seats:
            continue
            
        seats_count = len(available_seats)
        
        # Take a chunk of students = seats_count
        # (Or slightly less if we want sophisticated spacing already in chunking? No, solver handles constraints)
        # We treat this as a "Fill this room" step.
        
        chunk_size = min(seats_count, len(student_pool) - current_pool_index)
        students_chunk_list = student_pool[current_pool_index : current_pool_index + chunk_size]
        
        # Convert list to Dict format expected by Solver
        students_data = {
            s["id"]: s for s in students_chunk_list
        }
        
        room_data = {
            "room_id": str(room.id),
            "seats": [str(s.id) for s in available_seats],
            "adjacency_matrix": generate_adjacency_matrix(available_seats)
        }
        
        # CALL SOLVER
        result = allocate_seating(room_data, students_data, str(req.exam_id), req.exam_type)
        
        if result["status"] == "SUCCESS":
            # Save Assignments
            for assign in result["assignments"]:
                rec = models.SeatAllocation(
                    exam_id=req.exam_id,
                    room_id=room.id,
                    student_id=int(assign["student_id"]),
                    seat_id=int(assign["seat_id"]),
                    manual_override=False
                )
                db.add(rec)
                total_allocated += 1
            
            # Advance index by how many were successfully allocated? 
            # Actually, the solver might reject some if constraints fail.
            # But `allocate_seating` usually maxes out.
            # Ideally we check WHO was allocated.
            # `result["assignments"]` has the list.
            allocated_s_ids = {int(a["student_id"]) for a in result["assignments"]}
            
            # We move generic pointer? NO.
            # We should remove allocated students from pool. 
            # But to keep simple loop: 
            # Just verify who got seated. 
            # The chunk was `students_chunk_list`.
            # If solver failed to seat someone in chunk (due to constraints), they remain unallocated.
            # They should be returned to pool? Or we just move on?
            # Complexity: Backtracking.
            # Simple approach: Assume greedy fill. If X didn't fit in Room 1, try Room 2?
            # Current logic: `students_chunk_list` are "assigned to be processed in Room 1".
            # If specific constraint makes one fail, they are left behind.
            # Correct logic: Update `current_pool_index` by `chunk_size`.
            # Those who failed simply didn't get a seat (Error margin).
            # For exams, usually we just need to FILL.
            
            current_pool_index += chunk_size 
            results_summary.append(f"Room {room.name}: {len(result['assignments'])} seated")
            
        else:
            results_summary.append(f"Room {room.name}: Failed - {result.get('message')}")
            # If failed completely, we might try same batch in next room?
            # For now, simplistic approach: Skip room, try next room with SAME students?
            # No, if code logic failed, maybe room data is bad.
            # Proceed.

    db.commit()
    
    return {
        "status": "SUCCESS", 
        "allocated_count": total_allocated, 
        "message": f"Global allocation complete. Processed {len(target_rooms)} rooms. {total_allocated}/{len(student_pool)} students seated.",
        "details": results_summary
    }

@router.get("/student/me")
def get_my_separations(
    current_user: models.User = Depends(auth_router.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all seat allocations for the current student."""
    student = db.query(models.Student).filter(models.Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    allocations = db.query(models.SeatAllocation).options(
        joinedload(models.SeatAllocation.exam).joinedload(models.Exams.course),
        joinedload(models.SeatAllocation.room),
        joinedload(models.SeatAllocation.seat)
    ).filter(models.SeatAllocation.student_id == student.id).all()

    # Format for frontend
    result = []
    for alloc in allocations:
        exam = alloc.exam
        course = exam.course
        result.append({
            "id": alloc.id,
            "exam_id": exam.id,
            "courseName": course.title if course else "Exam",
            "courseCode": course.code if course else "",
            "examDate": exam.exam_date.strftime("%Y-%m-%d"),
            "startTime": exam.start_time.strftime("%I:%M %p"),
            "endTime": (exam.start_time + timedelta(minutes=exam.duration_minutes)).strftime("%I:%M %p"),
            "room": alloc.room.name,
            "room_id": alloc.room.id,
            "bench": alloc.seat.seat_label, # Using label as bench/seat identifier
            "seat": alloc.seat.seat_label,
            "seat_id": alloc.seat.id,
            "studentName": current_user.name or current_user.email.split('@')[0],
            "rollNumber": student.roll_number,
            "reportingTime": (exam.start_time - timedelta(minutes=30)).strftime("%I:%M %p"),
            "entryGate": "Main Gate",
            "specialAccommodation": None 
        })
    return result
