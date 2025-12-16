from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated

from db import SessionLocal
import models, schemas
import auth_router

router = APIRouter(prefix="/students", tags=["students"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schemas.StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(student_in: schemas.StudentCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Student).filter(models.Student.roll_number == student_in.roll_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Roll number already exists")

    user_obj = None
    if student_in.user:
        existing_user = db.query(models.User).filter(models.User.email == student_in.user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")

        user_obj = models.User(
            email=student_in.user.email,
            hashed_password=auth_router.get_password_hash(student_in.user.password),
            name=student_in.user.name,
            phone=student_in.user.phone,
            role=student_in.user.role
        )
        db.add(user_obj)
        db.flush()

    student_obj = models.Student(
        user_id=user_obj.id if user_obj else None,
        roll_number=student_in.roll_number,
        branch_id=student_in.branch_id,
        current_semester=student_in.current_semester,
        year=student_in.year or ( (student_in.current_semester + 1) // 2 if student_in.current_semester else 1)
    )

    db.add(student_obj)
    db.commit()
    db.refresh(student_obj)

    return student_obj


@router.get("/", response_model=List[schemas.StudentRead])
def list_students(
    branch_id: Optional[int] = None,
    current_semester: Optional[int] = None,
    program: Optional[str] = None, # Legacy/Optional
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    from sqlalchemy.orm import joinedload
    query = db.query(models.Student).options(
        joinedload(models.Student.user),
        joinedload(models.Student.branch).joinedload(models.Branch.program)
    )
    if branch_id:
        query = query.filter(models.Student.branch_id == branch_id)
    if current_semester:
        query = query.filter(models.Student.current_semester == current_semester)
    if year:
        query = query.filter(models.Student.year == year)
    
    # If program string is passed, we might need to join Branch/Program or ignore if using branch_id
    if program:
         # Optional: filter by joining Branch -> Program.name if needed.
         pass

    students = query.all()
    return students


# NOTE: /me route MUST come before /{student_id} to avoid FastAPI matching "me" as a student_id parameter
@router.get("/me", response_model=schemas.StudentRead)
def get_current_student(
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Get the current authenticated student's profile"""
    from sqlalchemy.orm import joinedload
    student = db.query(models.Student).options(
        joinedload(models.Student.user),
        joinedload(models.Student.branch).joinedload(models.Branch.program)
    ).filter(models.Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return student

@router.put("/me", response_model=schemas.StudentRead)
def update_current_student(
    student_update: schemas.StudentUpdate,
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Update calculation for current student"""
    from sqlalchemy.orm import joinedload
    student = db.query(models.Student).options(joinedload(models.Student.user)).filter(models.Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Update student fields
    if student_update.branch_id is not None:
        student.branch_id = student_update.branch_id
    if student_update.current_semester is not None:
        student.current_semester = student_update.current_semester
    if student_update.year is not None:
        student.year = student_update.year
    
    # Update user fields if provided (User relation)
    if student.user:
        if student_update.name is not None:
            student.user.name = student_update.name
        if student_update.phone is not None:
            student.user.phone = student_update.phone
        # Students cannot update their own active status
    
    db.commit()
    db.refresh(student)
    return student


@router.get("/{student_id}", response_model=schemas.StudentRead)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = (
        db.query(models.Student)
        .filter(models.Student.id == student_id)
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.put("/{student_id}", response_model=schemas.StudentRead)
def update_student(student_id: int, student_update: schemas.StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Update student fields
    if student_update.branch_id is not None:
        student.branch_id = student_update.branch_id
    if student_update.current_semester is not None:
        student.current_semester = student_update.current_semester
    if student_update.year is not None:
        student.year = student_update.year
    
    # Update user fields if provided
    if student.user:
        if student_update.name is not None:
            student.user.name = student_update.name
        if student_update.phone is not None:
            student.user.phone = student_update.phone
        if student_update.is_active is not None:
            student.user.is_active = student_update.is_active
    
    db.commit()
    db.refresh(student)
    return student
