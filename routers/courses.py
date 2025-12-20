from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import os
import shutil
import requests

import db
import models
import schemas
import auth_router
import config

router = APIRouter(prefix="/courses", tags=["courses"])

# --- Helpers ---

def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

# --- CRUD ---

@router.post("/", response_model=schemas.CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(course_in: schemas.CourseCreate, background_tasks: BackgroundTasks, db_session: Session = Depends(get_db)):
    existing = db_session.query(models.Course).filter(models.Course.code == course_in.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Course code already exists")

    # Verify branch if provided
    if course_in.branch_id:
        branch = db_session.query(models.Branch).filter(models.Branch.id == course_in.branch_id).first()
        if not branch:
             raise HTTPException(status_code=400, detail="Branch not found")

    course = models.Course(
        code=course_in.code,
        name=course_in.title,
        title=course_in.title, # Added to match model
        description=course_in.description,
        credits=course_in.credits,
        branch_id=course_in.branch_id,
        semester=course_in.semester,
        year_level=course_in.year_level or ( (course_in.semester + 1) // 2 if course_in.semester else 1), # Auto-calc year level if missing
        syllabus_text=course_in.syllabus_text
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    # --- Notify Students of New Course ---
    def notify_students_of_new_course(course_obj):
        try:
            # Fetch students in the relevant branch and semester
            students_query = db_session.query(models.User.email).join(models.Student).filter(
                models.Student.branch_id == course_obj.branch_id
            )
            if course_obj.semester:
                students_query = students_query.filter(models.Student.current_semester == course_obj.semester)
            
            student_emails = [email[0] for email in students_query.all() if email[0]]
            
            if student_emails:
                notify_payload = {
                    "course_name": course_obj.title,
                    "semester": f"Semester {course_obj.semester}" if course_obj.semester else "New Semester",
                    "student_emails": student_emails
                }
                requests.post(f"{config.MAIL_SERVICE_URL}/api/v1/notify/course-creation", json=notify_payload, timeout=10)
        except Exception as e:
            print(f"Course creation notification error: {e}")

    background_tasks.add_task(notify_students_of_new_course, course)

    return course

@router.get("/", response_model=List[schemas.CourseRead])
def list_courses(
    branch_id: Optional[int] = None, 
    semester: Optional[int] = None,
    program_id: Optional[int] = None, # Optional legacy filtering if possible, or derive
    db_session: Session = Depends(get_db)
):
    query = db_session.query(models.Course).options(
        joinedload(models.Course.branch).joinedload(models.Branch.program),
        joinedload(models.Course.instructor).joinedload(models.Faculty.user),
        joinedload(models.Course.assignments).joinedload(models.FacultyCourseAssignment.faculty).joinedload(models.Faculty.user)
    )
    
    if branch_id is not None:
        query = query.filter(models.Course.branch_id == branch_id)
    if semester is not None:
        query = query.filter(models.Course.semester == semester)
        
    # If program_id is passed, we need to join Branch to filter
    if program_id is not None:
        query = query.join(models.Branch).filter(models.Branch.program_id == program_id)

    courses = query.all()
    return courses

@router.get("/{course_id}", response_model=schemas.CourseRead)
def get_course(course_id: int, db_session: Session = Depends(get_db)):
    course = db_session.query(models.Course).options(
        joinedload(models.Course.instructor).joinedload(models.Faculty.user),
        joinedload(models.Course.assignments).joinedload(models.FacultyCourseAssignment.faculty).joinedload(models.Faculty.user)
    ).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Adapt to schema
    return {
        "id": course.id,
        "code": course.code,
        "title": course.title,
        "branch_id": course.branch_id,
        "semester": course.semester,
        "year_level": course.year_level,
        "credits": course.credits,
        "is_active": course.is_active,
        "enrolled_count": course.enrolled_count,
        "description": course.description,
        "instructor_id": course.instructor_id,
        "instructor_name": course.instructor_name,
        "syllabus_file_id": getattr(course, 'syllabus_file_id', None),
        "mindmap_id": getattr(course, 'mindmap_id', None),
        "syllabus_text": getattr(course, 'syllabus_text', None),
    }

@router.put("/{course_id}", response_model=schemas.CourseRead)
def update_course(course_id: int, course_update: schemas.CourseUpdate, db_session: Session = Depends(get_db)):
    course = db_session.query(models.Course).options(
        joinedload(models.Course.instructor).joinedload(models.Faculty.user),
        joinedload(models.Course.assignments).joinedload(models.FacultyCourseAssignment.faculty).joinedload(models.Faculty.user)
    ).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    up = course_update
    if up.title is not None:
        course.title = up.title
        course.name = up.title
    if up.branch_id is not None:
        branch = db_session.query(models.Branch).filter(models.Branch.id == up.branch_id).first()
        if not branch:
            raise HTTPException(status_code=404, detail="Branch not found")
        course.branch_id = up.branch_id
    if up.semester is not None:
        course.semester = up.semester
        # Auto update year level if reasonable
        course.year_level = (up.semester + 1) // 2
        
    if up.credits is not None:
        course.credits = up.credits
    if up.instructor_id is not None:
        # Check instructor?
        course.instructor_id = up.instructor_id
    if up.short_description is not None:
        course.description = up.short_description # Map short_description to description
    if up.is_active is not None:
        course.is_active = up.is_active

    db_session.commit()
    db_session.refresh(course)

    # Return adapted
    return {
        "id": course.id,
        "code": course.code,
        "title": course.title,
        "branch_id": course.branch_id,
        "semester": course.semester,
        "year_level": course.year_level,
        "credits": course.credits,
        "is_active": course.is_active,
        "enrolled_count": course.enrolled_count,
        "description": course.description,
        "instructor_id": course.instructor_id,
        "instructor_name": course.instructor_name,
        "syllabus_file_id": course.syllabus_file_id,
        "mindmap_id": getattr(course, 'mindmap_id', None),
    }

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, db_session: Session = Depends(get_db)):
    course = db_session.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db_session.delete(course)
    db_session.commit()
    return

# --- Syllabus Upload ---

SYLLABUS_DIR = os.path.join("/tmp", "storage", "syllabus")
os.makedirs(SYLLABUS_DIR, exist_ok=True)

@router.post("/{course_id}/syllabus", response_model=schemas.CourseRead)
def upload_syllabus(course_id: int, file: UploadFile = FastAPIFile(...), db_session: Session = Depends(get_db), current_user: models.User = Depends(auth_router.get_current_active_user)):
    course = db_session.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Save file to disk
    storage_filename = f"course_{course_id}_syllabus_{file.filename}"
    storage_path = os.path.join(SYLLABUS_DIR, storage_filename)
    with open(storage_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_rec = models.File(
        owner_type="course",
        owner_id=course_id,
        file_name=file.filename,
        storage_path=storage_path,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=None,
    )
    db_session.add(file_rec)
    db_session.flush()

    course.syllabus_file_id = file_rec.id
    db_session.commit()
    db_session.refresh(course)

    return course

@router.get("/{course_id}/syllabus/download")
def download_syllabus(course_id: int, db_session: Session = Depends(get_db)):
    course = db_session.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if syllabus_file_id is set
    syllabus_id = getattr(course, 'syllabus_file_id', None)
    if not syllabus_id:
        raise HTTPException(status_code=404, detail="Syllabus not uploaded")
        
    file_rec = db_session.query(models.File).filter(models.File.id == syllabus_id).first()
    if not file_rec or not os.path.exists(file_rec.storage_path):
        raise HTTPException(status_code=404, detail="File not found on server")
        
    return FileResponse(file_rec.storage_path, filename=file_rec.file_name, media_type=file_rec.mime_type)

# --- Mindmap status (simple) ---
@router.get("/{course_id}/mindmap", response_model=schemas.MindmapRead)
def get_mindmap(course_id: int, db_session: Session = Depends(get_db)):
    course = db_session.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not course.mindmap_id:
        raise HTTPException(status_code=404, detail="Mindmap not generated")
    mindmap = db_session.query(models.MindMap).filter(models.MindMap.id == course.mindmap_id).first()
    if not mindmap:
        raise HTTPException(status_code=404, detail="Mindmap not found")
    return mindmap

# --- Enrollment ---
@router.post("/{course_id}/enroll", response_model=schemas.CourseEnrollmentRead, status_code=status.HTTP_201_CREATED)
def enroll_student(course_id: int, payload: schemas.CourseEnrollmentCreate, background_tasks: BackgroundTasks, db_session: Session = Depends(get_db)):
    course = db_session.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    student = db_session.query(models.Student).filter(models.Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    enrollment = models.CourseEnrollment(
        course_id=course_id,
        student_id=payload.student_id,
        enrollment_status=payload.enrollment_status or "active",
    )
    db_session.add(enrollment)
    
    # Auto-increment enrolled_count
    course.enrolled_count = (course.enrolled_count or 0) + 1

    upcoming_exams = db_session.query(models.Exams).filter(
        models.Exams.course_id == course_id,
        models.Exams.status != "Completed"
    ).all()
    
    for exam in upcoming_exams:
        # Check if already enrolled (unlikely but safe)
        existing_es = db_session.query(models.ExamStudent).filter(
            models.ExamStudent.exam_id == exam.id,
            models.ExamStudent.student_id == payload.student_id
        ).first()
        if not existing_es:
            new_es = models.ExamStudent(
                exam_id=exam.id,
                student_id=payload.student_id
            )
            db_session.add(new_es)
            
    db_session.commit()
    db_session.refresh(enrollment)

    # --- Notify Student & Faculty ---
    def send_enrollment_notification(student_obj, course_obj):
        try:
            # Try to find faculty/instructor details if assigned
            faculty_info = {"id": "", "email": ""}
            if course_obj.instructor_id:
                faculty = db_session.query(models.Faculty).filter(models.Faculty.id == course_obj.instructor_id).first()
                if faculty and faculty.user:
                    faculty_info = {"id": str(faculty.id), "email": faculty.user.email}

            notify_payload = {
                "student_id": student_obj.roll_number,
                "student_name": student_obj.user.name if student_obj.user else "Student",
                "student_email": student_obj.user.email if student_obj.user else "",
                "subject_name": course_obj.title,
                "faculty_id": faculty_info["id"],
                "faculty_email": faculty_info["email"]
            }
            # requests.post(f"{config.MAIL_SERVICE_URL}/api/v1/notify/student-enrollment", json=notify_payload, timeout=5)
            requests.post(f"{config.MAIL_SERVICE_URL}/api/v1/notify/student-enrollment", json=notify_payload, timeout=5)
        except Exception as e:
            print(f"Notification error: {e}")

    background_tasks.add_task(send_enrollment_notification, student, course)

    return enrollment

@router.get("/student/me", response_model=List[schemas.CourseRead])
def get_student_enrollments(
    current_user: models.User = Depends(auth_router.get_current_active_user),
    db_session: Session = Depends(get_db)
):
    try:
        # Find student profile for this user
        student = db_session.query(models.Student).filter(models.Student.user_id == current_user.id).first()
        if not student:
            return [] 
        
        # Query enrollments
        enrollments = db_session.query(models.CourseEnrollment).filter(
            models.CourseEnrollment.student_id == student.id,
            models.CourseEnrollment.enrollment_status == "active"
        ).all()
        
        course_ids = [e.course_id for e in enrollments]
        print(f"DEBUG: Course IDs {course_ids}")
        
        if not course_ids:
            return []
            
        courses = db_session.query(models.Course).options(
            joinedload(models.Course.instructor).joinedload(models.Faculty.user),
            joinedload(models.Course.assignments).joinedload(models.FacultyCourseAssignment.faculty).joinedload(models.Faculty.user)
        ).filter(models.Course.id.in_(course_ids)).all()
        print(f"DEBUG: Found {len(courses)} courses")
        
        result = []
        for c in courses:
            # print(f"DEBUG: Mapping course {c.id}")
            result.append({
                "id": c.id,
                "code": c.code,
                "title": c.name,
                "branch_id": c.branch_id,
                "semester": c.semester,
                "year_level": c.year_level or 1,
                "credits": c.credits,
                "is_active": c.is_active,
                "enrolled_count": c.enrolled_count or 0,
                "description": c.description,
                "instructor_id": c.instructor_id,
                "instructor_name": c.instructor_name,
                "syllabus_file_id": getattr(c, 'syllabus_file_id', None),
                "mindmap_id": getattr(c, 'mindmap_id', None),
            })
        print("DEBUG: Mapping done")
        return result
    except Exception as e:
        print(f"DEBUG CRASH: {e}")
        import traceback
        traceback.print_exc()
        raise e


# --- Bulk Import (init only) ---
IMPORT_DIR = os.path.join("/tmp", "storage", "imports")
os.makedirs(IMPORT_DIR, exist_ok=True)

@router.post("/bulk-import", status_code=status.HTTP_201_CREATED)
def bulk_import_courses(file: UploadFile = FastAPIFile(...), db_session: Session = Depends(get_db), current_user: models.User = Depends(auth_router.get_current_active_user)):
    # Save uploaded file
    storage_filename = f"courses_import_{current_user.id}_{file.filename}"
    storage_path = os.path.join(IMPORT_DIR, storage_filename)
    with open(storage_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_rec = models.File(
        owner_type="course_import",
        owner_id=current_user.id,
        file_name=file.filename,
        storage_path=storage_path,
        mime_type=file.content_type or "text/csv",
        size_bytes=None,
    )
    db_session.add(file_rec)
    db_session.flush()

    job = models.CourseImportJob(
        uploaded_by=current_user.id,
        file_id=file_rec.id,
        status="pending",
        total_rows=0,
        success_count=0,
        failure_count=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    return {"jobId": job.id}

@router.get("/import-jobs", response_model=List[schemas.CourseImportJobRead])
def list_import_jobs(db_session: Session = Depends(get_db), current_user: models.User = Depends(auth_router.get_current_active_admin)):
    jobs = db_session.query(models.CourseImportJob).order_by(models.CourseImportJob.id.desc()).all()
    return jobs
