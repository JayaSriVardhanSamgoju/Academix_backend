from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Annotated

from db import get_db
import models
import schemas
from auth_router import get_current_active_user, get_current_active_admin, get_current_active_student
from routers.faculty import get_current_faculty

router = APIRouter(
    prefix="/timetable",
    tags=["TimeTable"]
)

# --- Faculty Endpoints ---

@router.get("/faculty/me", response_model=List[schemas.TimeTableEntryRead])
def get_my_timetable(
    current_faculty: models.Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    """
    Get the timetable for the logged-in faculty member.
    """
    entries = db.query(models.TimeTableEntry)\
        .options(joinedload(models.TimeTableEntry.course), 
                 joinedload(models.TimeTableEntry.branch).joinedload(models.Branch.program))\
        .filter(models.TimeTableEntry.faculty_id == current_faculty.id)\
        .all()
    return entries

# --- Student Endpoints ---

@router.get("/student/me", response_model=List[schemas.TimeTableEntryRead])
def get_student_timetable(
    current_student: models.User = Depends(get_current_active_student), # Actually returns User, need to get Student profile
    db: Session = Depends(get_db)
):
    """
    Get the timetable for the logged-in student based on their branch and semester.
    """
    # 1. Get Student Profile
    student = db.query(models.Student).filter(models.Student.user_id == current_student.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
        
    if not student.branch_id or not student.current_semester:
         return [] # Or raise error if strict
         
    # 2. Fetch Timetable for this Branch + Semester
    entries = db.query(models.TimeTableEntry)\
        .options(joinedload(models.TimeTableEntry.course), 
                 joinedload(models.TimeTableEntry.faculty).joinedload(models.Faculty.user))\
        .filter(
            models.TimeTableEntry.branch_id == student.branch_id,
            models.TimeTableEntry.semester == student.current_semester
        ).all()
        
    return entries

# --- Admin Endpoints ---

@router.post("/assign", response_model=schemas.TimeTableEntryRead)
def assign_timetable_slot(
    entry: schemas.TimeTableEntryCreate,
    current_admin: models.User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Admin assigns a course to a time slot for a faculty and branch.
    """
    # Check if slot is already occupied for this Faculty
    existing_faculty_slot = db.query(models.TimeTableEntry).filter(
        models.TimeTableEntry.faculty_id == entry.faculty_id,
        models.TimeTableEntry.day_of_week == entry.day_of_week,
        models.TimeTableEntry.period_number == entry.period_number
    ).first()
    
    if existing_faculty_slot:
        raise HTTPException(status_code=400, detail="Faculty is already booked for this slot.")

    # Check if slot is already occupied for this Branch/Sem (Students can't be in two places)
    if entry.branch_id:
        existing_branch_slot = db.query(models.TimeTableEntry).filter(
            models.TimeTableEntry.branch_id == entry.branch_id,
            models.TimeTableEntry.semester == entry.semester,
            models.TimeTableEntry.day_of_week == entry.day_of_week,
            models.TimeTableEntry.period_number == entry.period_number
        ).first()
        if existing_branch_slot:
             raise HTTPException(status_code=400, detail="This Class/Branch already has a class in this slot.")

    db_entry = models.TimeTableEntry(**entry.model_dump())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.get("/", response_model=List[schemas.TimeTableEntryRead])
def get_all_timetable_entries(
    current_admin: models.User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Admin lists all timetable entries.
    """
    return db.query(models.TimeTableEntry)\
             .options(joinedload(models.TimeTableEntry.course), 
                      joinedload(models.TimeTableEntry.faculty).joinedload(models.Faculty.user), 
                      joinedload(models.TimeTableEntry.branch).joinedload(models.Branch.program))\
             .all()

@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timetable_entry(
    entry_id: int,
    current_admin: models.User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Admin deletes a timetable entry.
    """
    entry = db.query(models.TimeTableEntry).filter(models.TimeTableEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    db.delete(entry)
    db.commit()
    return None
