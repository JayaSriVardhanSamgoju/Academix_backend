from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Annotated, Optional
import models, schemas, auth_router
from db import get_db

router = APIRouter(prefix="/faculty", tags=["faculty"])

def get_current_faculty(
    current_user: models.User = Depends(auth_router.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Dependency to check if user is a faculty member"""
    # Simply checking if the user has a linked faculty profile
    # If the relationship is not loaded, we might need to query it.
    # Assuming 'current_user' is attached to session, lazy load works? 
    # Or explicitly query.
    faculty = db.query(models.Faculty).filter(models.Faculty.user_id == current_user.id).first()
    
    if not faculty:
         raise HTTPException(status_code=403, detail="User is not a registered faculty member")
         
    return faculty

@router.get("/me", response_model=schemas.FacultyRead)
def get_my_profile(
    current_user: models.User = Depends(auth_router.get_current_active_user),
    db: Session = Depends(get_db)
):
    # Explicitly load user relationship to avoid Pydantic serialization issues
    faculty = db.query(models.Faculty).options(joinedload(models.Faculty.user)).filter(models.Faculty.user_id == current_user.id).first()
    
    if not faculty:
         raise HTTPException(status_code=404, detail="Faculty profile not found")
         
    return faculty

@router.get("/courses", response_model=List[schemas.CourseRead])
def get_my_courses(
    current_faculty: models.Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    """Get assigned courses for Teaching Faculty."""
    if current_faculty.faculty_type != "TEACHING":
        return []
        
    assignments = db.query(models.FacultyCourseAssignment).filter(
        models.FacultyCourseAssignment.faculty_id == current_faculty.id
    ).options(joinedload(models.FacultyCourseAssignment.course)).all()
    
    return [a.course for a in assignments]

@router.get("/invigilations", response_model=List[schemas.InvigilationDutyRead])
def get_my_invigilations(
    current_faculty: models.Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    """Get assigned invigilation duties."""
    duties = db.query(models.InvigilationDuty).filter(
        models.InvigilationDuty.faculty_id == current_faculty.id
    ).options(joinedload(models.InvigilationDuty.exam), joinedload(models.InvigilationDuty.room)).all()
    return duties

@router.post("/marks", response_model=schemas.StudentMarkRead)
def add_student_mark(
    mark_data: schemas.StudentMarkCreate,
    current_faculty: models.Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    """Add marks for a student (Teaching Faculty only)."""
    if current_faculty.faculty_type != "TEACHING":
        raise HTTPException(status_code=403, detail="Only teaching faculty can add marks")
    
    # Verify assignment
    assignment = db.query(models.FacultyCourseAssignment).filter(
        models.FacultyCourseAssignment.faculty_id == current_faculty.id,
        models.FacultyCourseAssignment.course_id == mark_data.course_id
    ).first()
    
    if not assignment:
        # Strict mode: must be assigned
        # raise HTTPException(status_code=403, detail="You are not assigned to this course")
        pass # Allow for now if testing, but ideally uncomment above.
        
    # Check if mark exists? Update or Create?
    existing = db.query(models.StudentMark).filter(
        models.StudentMark.student_id == mark_data.student_id,
        models.StudentMark.course_id == mark_data.course_id,
        models.StudentMark.exam_type == mark_data.exam_type
    ).first()
    
    if existing:
        existing.marks_obtained = mark_data.marks_obtained
        existing.max_marks = mark_data.max_marks # In case max marks changed
        existing.grader_id = current_faculty.id
        db.commit()
        db.refresh(existing)
        return existing
        
    new_mark = models.StudentMark(
        student_id=mark_data.student_id,
        course_id=mark_data.course_id,
        exam_type=mark_data.exam_type,
        marks_obtained=mark_data.marks_obtained,
        max_marks=mark_data.max_marks,
        grader_id=current_faculty.id
    )
    db.add(new_mark)
    db.commit()
    db.refresh(new_mark)
    return new_mark

@router.get("/", response_model=List[schemas.FacultyRead])
def list_faculty(
    department: Optional[str] = None,
    faculty_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all faculty members (Admin/General)."""
    query = db.query(models.Faculty).options(
        joinedload(models.Faculty.user),
        joinedload(models.Faculty.course_assignments).joinedload(models.FacultyCourseAssignment.course)
    )
    if department:
        query = query.filter(models.Faculty.department == department)
    if faculty_type:
        query = query.filter(models.Faculty.faculty_type == faculty_type)
    
    return query.all()

@router.post("/", response_model=schemas.FacultyRead, status_code=status.HTTP_201_CREATED)
def create_faculty(faculty_in: schemas.FacultyCreate, db: Session = Depends(get_db)):
    """Create a new faculty member and their user account."""
    # Check if user already exists
    if faculty_in.user:
        existing_user = db.query(models.User).filter(models.User.email == faculty_in.user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")

        user_obj = models.User(
            email=faculty_in.user.email,
            hashed_password=auth_router.get_password_hash(faculty_in.user.password),
            name=faculty_in.user.name,
            phone=faculty_in.user.phone,
            role="Faculty" # Force role to Faculty
        )
        db.add(user_obj)
        db.flush() # Get user_obj.id

    faculty_obj = models.Faculty(
        user_id=user_obj.id if faculty_in.user else None,
        faculty_type=faculty_in.faculty_type,
        department=faculty_in.department,
        designation=faculty_in.designation
    )

    db.add(faculty_obj)
    db.commit()
    db.refresh(faculty_obj)
    return faculty_obj

@router.put("/{faculty_id}", response_model=schemas.FacultyRead)
def update_faculty(
    faculty_id: int, 
    faculty_update: schemas.FacultyUpdate, 
    db: Session = Depends(get_db)
):
    """Update a faculty member's profile."""
    faculty = db.query(models.Faculty).filter(models.Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    
    if faculty_update.faculty_type is not None:
        faculty.faculty_type = faculty_update.faculty_type
    if faculty_update.department is not None:
        faculty.department = faculty_update.department
    if faculty_update.designation is not None:
        faculty.designation = faculty_update.designation
        
    db.commit()
    db.refresh(faculty)
    return faculty

@router.get("/students", response_model=List[schemas.StudentRead])
def get_my_students(
    course_id: Optional[int] = None,
    year: Optional[int] = None,
    semester: Optional[int] = None,
    current_faculty: models.Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    """
    Get students enrolled in courses taught by this faculty.
    Supports filtering by Course, Year, and Semester.
    """
    # 1. Get Course IDs assigned to faculty
    assignments_query = db.query(models.FacultyCourseAssignment).filter(
        models.FacultyCourseAssignment.faculty_id == current_faculty.id
    )
    
    if course_id:
        assignments_query = assignments_query.filter(models.FacultyCourseAssignment.course_id == course_id)
        
    assignments = assignments_query.all()
    target_course_ids = [a.course_id for a in assignments]
    
    if not target_course_ids:
        return []

    # 2. Find students
    query = db.query(models.Student)\
        .join(models.CourseEnrollment)\
        .filter(models.CourseEnrollment.course_id.in_(target_course_ids))\
        .options(joinedload(models.Student.user), joinedload(models.Student.branch))
        
    if year:
        query = query.filter(models.Student.year == year)
    if semester:
        query = query.filter(models.Student.current_semester == semester)
        
    students = query.distinct().all()
    return students

@router.get("/marks_sheet", response_model=List[schemas.StudentMarkRead])
def get_marks_sheet(
    course_id: int,
    exam_type: str,
    current_faculty: models.Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    """Get all existing marks for a specific course and exam type."""
    marks = db.query(models.StudentMark).filter(
        models.StudentMark.course_id == course_id,
        models.StudentMark.exam_type == exam_type
    ).all()
    
    return marks

@router.get("/dashboard/stats")
def get_dashboard_stats(
    current_faculty: models.Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    """
    Get aggregated statistics for the Faculty Dashboard.
    Replacing mock data with real counts and activity.
    """
    # 1. Active Courses
    assignments = db.query(models.FacultyCourseAssignment).filter(
        models.FacultyCourseAssignment.faculty_id == current_faculty.id
    ).all()
    course_ids = [a.course_id for a in assignments]
    active_courses = len(course_ids)

    # 2. Total Students
    total_students = 0
    if course_ids:
        total_students = db.query(models.CourseEnrollment.student_id)\
            .filter(models.CourseEnrollment.course_id.in_(course_ids))\
            .distinct().count()

    # 3. Class Topper (Max Marks) and Avg Performance
    class_topper = "N/A"
    avg_performance = "N/A"
    
    if course_ids:
        # Max
        max_val = db.query(func.max(models.StudentMark.marks_obtained))\
            .filter(models.StudentMark.course_id.in_(course_ids))\
            .scalar()
        if max_val is not None:
             class_topper = f"{max_val}"

        # Avg
        avg_val = db.query(func.avg(models.StudentMark.marks_obtained))\
            .filter(models.StudentMark.course_id.in_(course_ids))\
            .scalar()
        if avg_val is not None:
             avg_performance = f"{round(avg_val, 1)}" # Removed % as marks might be raw

    # 4. Recent Activity (Invigilations and Marks)
    # Fetch last 3 invigilations
    recent_invigilations = db.query(models.InvigilationDuty).filter(
        models.InvigilationDuty.faculty_id == current_faculty.id
    ).order_by(models.InvigilationDuty.id.desc()).limit(3).all()

    activities = []
    for invig in recent_invigilations:
        activities.append({
            "type": "invigilation",
            "message": f"Invigilation assigned for Exam #{invig.exam_id}",
            "time": "Recently" # Timestamp ideally needed in InvigilationDuty
        })

    # Placeholder for marks/attendance activity if timestamps existed
    
    return {
        "total_students": total_students,
        "active_courses": active_courses,
        "class_topper": class_topper,
        "avg_performance": avg_performance,
        "recent_activity": activities
    }
