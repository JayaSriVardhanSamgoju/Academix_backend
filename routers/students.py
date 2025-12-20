from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, File, UploadFile
import requests
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Annotated

from db import SessionLocal
import models, schemas
import auth_router
import config

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
        joinedload(models.Student.branch).joinedload(models.Branch.program),
        joinedload(models.Student.enrollments),
        joinedload(models.Student.seat_allocations).joinedload(models.SeatAllocation.room),
        joinedload(models.Student.seat_allocations).joinedload(models.SeatAllocation.seat)
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


from datetime import datetime

@router.get("/me/dashboard-summary")
def get_student_dashboard_summary(
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    Aggregates all student dashboard data into a single response 
    to reduce API calls.
    """
    from sqlalchemy.orm import joinedload
    
    # 1. Profile
    student = db.query(models.Student).options(
        joinedload(models.Student.user),
        joinedload(models.Student.branch).joinedload(models.Branch.program),
        joinedload(models.Student.enrollments)
    ).filter(models.Student.user_id == current_user.id).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # 2. Enrolled Courses
    enrollments = db.query(models.CourseEnrollment).options(joinedload(models.CourseEnrollment.course)).filter(
        models.CourseEnrollment.student_id == student.id,
        models.CourseEnrollment.enrollment_status == "active"
    ).all()
    enrolled_courses_data = [e.course for e in enrollments if e.course]

    # 3. Upcoming Exams
    course_ids = [c.id for c in enrolled_courses_data]
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    exams = db.query(models.Exams).options(joinedload(models.Exams.course)).filter(
        models.Exams.course_id.in_(course_ids),
        models.Exams.exam_date >= today_start
    ).order_by(models.Exams.exam_date).all()

    # 4. Seating
    allocations = db.query(models.SeatAllocation).options(
        joinedload(models.SeatAllocation.room),
        joinedload(models.SeatAllocation.seat)
    ).filter(models.SeatAllocation.student_id == student.id).all()
    
    seating_map = []
    for alloc in allocations:
        seating_map.append({
            "exam_id": alloc.exam_id,
            "room": alloc.room.name if alloc.room else "TBA",
            "seat": alloc.seat.seat_label if alloc.seat else "TBA"
        })

    # 5. Notifications
    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id
    ).order_by(models.Notification.created_at.desc()).limit(10).all()

    # 6. Results
    results = db.query(models.StudentMark).options(joinedload(models.StudentMark.course)).filter(
        models.StudentMark.student_id == student.id
    ).all()
    
    # 7. Timetable (Safe Fallback)
    timetable = []
    try:
        timetable = db.query(models.TimeTableEntry)\
            .options(
                joinedload(models.TimeTableEntry.course),
                joinedload(models.TimeTableEntry.faculty).joinedload(models.Faculty.user),
                joinedload(models.TimeTableEntry.branch).joinedload(models.Branch.program)
            )\
            .filter(
                models.TimeTableEntry.branch_id == student.branch_id,
                models.TimeTableEntry.semester == student.current_semester
            ).all()
    except Exception as e:
        print(f"Error fetching timetable for dashboard: {e}")
        pass

    return {
        "profile": student,
        "enrolled_courses": enrolled_courses_data,
        "upcoming_exams": exams,
        "seating": seating_map,
        "notifications": notifications,
        "results": results,
        "timetable": timetable
    }


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
        joinedload(models.Student.branch).joinedload(models.Branch.program),
        joinedload(models.Student.enrollments),
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


@router.get("/me/results", response_model=List[schemas.StudentMarkRead])
def get_my_results(
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Get the exam results for the current authenticated student."""
    from sqlalchemy.orm import joinedload
    student = db.query(models.Student).filter(models.Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
        
    marks = db.query(models.StudentMark)\
        .options(joinedload(models.StudentMark.course))\
        .filter(models.StudentMark.student_id == student.id)\
        .all()
    return marks


@router.get("/{student_id}", response_model=schemas.StudentRead)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = (
        db.query(models.Student)
        .options(
            joinedload(models.Student.user), 
            joinedload(models.Student.enrollments),
            joinedload(models.Student.seat_allocations).joinedload(models.SeatAllocation.room),
            joinedload(models.Student.seat_allocations).joinedload(models.SeatAllocation.seat)
        )
        .filter(models.Student.id == student_id)
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.put("/{student_id}", response_model=schemas.StudentRead)
def update_student(
    student_id: int, 
    student_update: schemas.StudentUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    student = db.query(models.Student).options(joinedload(models.Student.user)).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # 1. Update User fields FIRST so name/email are correct for notifications
    if student.user:
        if student_update.name is not None:
            student.user.name = student_update.name
        if student_update.email is not None:
            student.user.email = student_update.email
        if student_update.phone is not None:
            student.user.phone = student_update.phone
        if student_update.is_active is not None:
            student.user.is_active = student_update.is_active
    
    # 2. Update Student specific fields
    if student_update.branch_id is not None:
        student.branch_id = student_update.branch_id
    if student_update.current_semester is not None:
        student.current_semester = student_update.current_semester
    if student_update.year is not None:
        student.year = student_update.year

    # 3. Handle Status specific logic (with notifications using updated user info)
    if student_update.academic_status is not None:
        print(f"DEBUG: Updating student {student_id} status from {student.academic_status} to {student_update.academic_status}")
        # Check if status is changing to DETAINED
        if student_update.academic_status == "DETAINED" and student.academic_status != "DETAINED":
            # Prepare notification
            print(f"DEBUG: Triggering detention alert for student {student_id}")
            if student.user:
                print(f"DEBUG: Student user found: {student.user.name}, email: {student.user.email}")
                if student.user.email:
                    def send_detention_alert(sid, sname, semail):
                        print(f"DEBUG: Background task started for student {sid}")
                        try:
                            payload = {
                                "student_id": str(sid),
                                "student_name": sname,
                                "student_email": semail,
                                "reason": "Academic Performance / Attendance Shortage"
                            }
                            print(f"DEBUG: Sending POST to notification service: {payload}")
                            resp = requests.post(f"{config.MAIL_SERVICE_URL}/api/v1/notify/student-detention", json=payload, timeout=10)
                            print(f"DEBUG: Notification service response: {resp.status_code} - {resp.text}")
                        except Exception as e:
                            print(f"CRITICAL ERROR in detention alert background task: {e}")

                    background_tasks.add_task(send_detention_alert, student.id, student.user.name, student.user.email)
                else:
                    print("DEBUG: Student email is missing")
            else:
                print("DEBUG: Student user object is missing")
        
        # Check if status is changing to CREDIT_SHORTAGE
        if student_update.academic_status == "CREDIT_SHORTAGE" and student.academic_status != "CREDIT_SHORTAGE":
            if student.user and student.user.email:
                def send_shortage_alert(sid, sname, semail):
                    try:
                            payload = {
                                "student_id": str(sid),
                                "student_name": sname,
                                "student_email": semail,
                                "current_credits": 0, # Could pass actuals if available
                                "required_credits": 18.0
                            }
                            requests.post(f"{config.MAIL_SERVICE_URL}/api/v1/notify/student-credit-shortage", json=payload, timeout=5)
                    except Exception: pass
                background_tasks.add_task(send_shortage_alert, student.id, student.user.name, student.user.email)

        student.academic_status = student_update.academic_status
    
    db.commit()
    db.refresh(student)
    return student

@router.post("/bulk-import", response_model=schemas.StudentBulkImportResponse)
def bulk_import_students(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_router.get_current_active_user)
):
    """
    Bulk import students from CSV.
    Returns a detailed branch-wise report and fails list.
    """
    if current_user.role != "Admin":
         raise HTTPException(status_code=403, detail="Only admins can perform bulk imports")

    import csv
    import io

    try:
        content = file.file.read().decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {e}")
    
    results = []
    branch_summaries = {}
    total = 0
    success = 0
    failure = 0
    failed_rolls = []

    for i, row in enumerate(csv_reader, 1):
        total += 1
        row_errors = []
        
        # Priority mapping for different CSV headers
        roll_no = row.get("roll_no") or row.get("roll_number") or row.get("Roll No")
        name = row.get("name") or row.get("Name")
        email = row.get("email") or row.get("Email")
        branch_name = row.get("branch") or row.get("program") or row.get("Program") or row.get("Branch") or "General"
        year = row.get("year") or row.get("Year")
        
        if not roll_no: row_errors.append("Missing roll number")
        if not name: row_errors.append("Missing name")
        if not email: row_errors.append("Missing email")
        
        # Check if already exists in DB
        if roll_no:
            existing = db.query(models.Student).filter(models.Student.roll_number == roll_no).first()
            if existing: row_errors.append("Duplicate roll number")
        
        if row_errors:
            failure += 1
            if roll_no: failed_rolls.append(roll_no)
            results.append(schemas.StudentImportRowResult(
                row=i, roll_number=roll_no or "N/A", name=name or "N/A", branch=branch_name, status="failure", errors=row_errors
            ))
            summary = branch_summaries.get(branch_name, {"success": 0, "failure": 0})
            summary["failure"] += 1
            branch_summaries[branch_name] = summary
            continue

        # Find Branch
        branch_obj = db.query(models.Branch).filter(models.Branch.name.ilike(f"%{branch_name}%")).first()
        if not branch_obj:
            branch_obj = db.query(models.Branch).filter(models.Branch.code.ilike(f"%{branch_name}%")).first()

        try:
            # Create User
            new_user = models.User(
                email=email,
                hashed_password=auth_router.get_password_hash("Welcome@123"),
                name=name,
                role="Student"
            )
            db.add(new_user)
            db.flush()

            # Create Student
            new_student = models.Student(
                user_id=new_user.id,
                roll_number=roll_no,
                branch_id=branch_obj.id if branch_obj else None,
                year=int(year) if year and str(year).isdigit() else 1,
                current_semester= ( (int(year) if year and str(year).isdigit() else 1) * 2 ) - 1 # Default to odd sem
            )
            db.add(new_student)
            db.commit()
            
            success += 1
            results.append(schemas.StudentImportRowResult(
                row=i, roll_number=roll_no, name=name, branch=branch_name, status="success", errors=[]
            ))
            summary = branch_summaries.get(branch_name, {"success": 0, "failure": 0})
            summary["success"] += 1
            branch_summaries[branch_name] = summary

        except Exception as e:
            db.rollback()
            failure += 1
            if roll_no: failed_rolls.append(roll_no)
            results.append(schemas.StudentImportRowResult(
                row=i, roll_number=roll_no, name=name, branch=branch_name, status="failure", errors=[str(e)]
            ))
            summary = branch_summaries.get(branch_name, {"success": 0, "failure": 0})
            summary["failure"] += 1
            branch_summaries[branch_name] = summary

    report = [
        schemas.BranchImportSummary(branch_name=name, success_count=s["success"], failure_count=s["failure"])
        for name, s in branch_summaries.items()
    ]

    return {
        "total_processed": total,
        "overall_success": success,
        "overall_failure": failure,
        "branch_wise_report": report,
        "failed_roll_numbers": failed_rolls,
        "details": results
    }

@router.post("/evaluate-promotion-eligibility", response_model=schemas.PromotionCheckResponse)
def check_promotion_eligibility(
    req: schemas.PromotionCheckRequest,
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)], # Admin/Faculty only ideally
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Evaluate student promotion eligibility based on updated results.
    Triggers automatic status update and notifications.
    """
    # 1. Logic Execution: Recalculate Credits
    earned_credits = sum(r.credits for r in req.updated_results if r.is_pass)
    
    CREDIT_THRESHOLD = req.credit_threshold or 18.0
    
    # 2. Determine Status
    new_status = "PROMOTED"
    if earned_credits < CREDIT_THRESHOLD:
        new_status = "CREDIT_SHORTAGE"
        
    action_taken = "Maintained"
    remarks = f"Earned {earned_credits} credits. Threshold: {CREDIT_THRESHOLD}."
    
    if new_status == "CREDIT_SHORTAGE":
        action_taken = "Status Demoted/Probation"
        remarks += " Status revised to CREDIT_SHORTAGE."

    # 3. Database Update
    student = db.query(models.Student).options(joinedload(models.Student.user)).filter(models.Student.roll_number == req.student_id).first()
    
    if student:
        # Update status if changed
        if student.academic_status != new_status:
            # Trigger External Email if it's a shortage
            if new_status == "CREDIT_SHORTAGE" and student.user and student.user.email:
                def send_auto_shortage_alert(sid, sname, semail, cur, req_val):
                    try:
                        payload = {
                            "student_id": str(sid),
                            "student_name": sname,
                            "student_email": semail,
                            "current_credits": float(cur),
                            "required_credits": float(req_val)
                        }
                        requests.post(f"{config.MAIL_SERVICE_URL}/api/v1/notify/student-credit-shortage", json=payload, timeout=5)
                    except Exception: pass
                background_tasks.add_task(send_auto_shortage_alert, student.id, student.user.name, student.user.email, earned_credits, CREDIT_THRESHOLD)

            student.academic_status = new_status
            db.commit()
            
            # 4. Internal Dashboard Notification
            notif_type = "alert" if new_status == "CREDIT_SHORTAGE" else "info"
            notif_title = "Academic Status Update"
            notif_body = f"Your academic status has been updated to: {new_status}. {remarks}"
            
            notification = models.Notification(
                user_id=student.user_id,
                type=notif_type,
                title=notif_title,
                body=notif_body,
                is_read=False
            )
            db.add(notification)
            db.commit()
    
    # 5. Output
    return {
        "student_id": req.student_id,
        "calculated_credits": earned_credits,
        "current_status": new_status,
        "action_taken": action_taken,
        "remarks": remarks
    }
