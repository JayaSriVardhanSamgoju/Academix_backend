from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Union, Any
from datetime import datetime
import json

# --- User Schemas ---

class UserBase(BaseModel):
    """Base schema for user data (email, role)."""
    email: EmailStr
    role: str = "Student"

class UserCreate(UserBase):
    """Schema for user creation (includes password)."""
    name: Optional[str] = None
    phone: Optional[str] = None
    password: str

class UserRead(UserBase):
    id: int
    name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True
    
class StudentBase(BaseModel):
    roll_number: str
    branch_id: Optional[int] = None
    current_semester: Optional[int] = None
    year: Optional[int] = None # Optional legacy

class StudentCreate(StudentBase):
    user: Optional[UserCreate] = None

class StudentUpdate(BaseModel):
    branch_id: Optional[int] = None
    current_semester: Optional[int] = None
    year: Optional[int] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    academic_status: Optional[str] = None

# --- Program & Branch ---

class BranchBase(BaseModel):
    name: str # e.g. "Computer Science"
    code: str # e.g. "CSE"

class ProgramBase(BaseModel):
    name: str
    duration_years: int
    file_prefix: Optional[str] = None

# 1. Base Read Models (No nested recursion)
class ProgramReadBasic(ProgramBase):
    id: int
    class Config:
        from_attributes = True

class BranchReadBasic(BranchBase):
    id: int
    program_id: int
    class Config:
        from_attributes = True

# 2. Full Read Models (With relationships)

class BranchRead(BranchReadBasic):
    # Include Program details
    program: Optional[ProgramReadBasic] = None

class ProgramRead(ProgramReadBasic):
    # Include list of Branches (basic info only to avoid loop)
    # branches: List[BranchReadBasic] = [] 
    # Actually, let's keep it simple. ProgramRead might not need branches by default unless requested.
    # But for "getPrograms" which might want to show branches? 
    # The user UI "getPrograms" is likely just for dropdowns.
    pass

class BranchCreate(BranchBase):
    pass

class ProgramCreate(ProgramBase):
    pass

# Update: If ProgramRead needs branches, use BranchReadBasic
class ProgramReadWithBranches(ProgramRead):
    branches: List[BranchReadBasic] = []


class StudentRead(StudentBase):
    id: int
    user: Optional[UserRead] = None
    # Use full BranchRead which includes Program
    branch: Optional[BranchRead] = None
    enrolled_courses: int = 0
    academic_status: Optional[str] = "PROMOTED"
    enrollments: List["CourseEnrollmentRead"] = [] # List of actual enrollments
    seat_allocations: List["SeatAllocationRead"] = [] # Allocations

    class Config:
        from_attributes = True

class FileRead(BaseModel):
    id: int
    owner_type: Optional[str] = None
    owner_id: Optional[int] = None
    file_name: str
    storage_path: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None

    class Config:
        from_attributes = True

# --- Mindmap ---
class MindmapRead(BaseModel):
    id: int
    course_id: int
    status: str
    source_syllabus_file_id: Optional[int] = None
    graph_json: Optional[dict] = None
    version: int

    class Config:
        from_attributes = True

# --- Course ---
class CourseBase(BaseModel):
    code: str
    title: str
    branch_id: Optional[int] = None
    semester: int
    year_level: Optional[int] = None
    credits: Optional[int] = None
    instructor_id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = True
    syllabus_text: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    branch_id: Optional[int] = None
    semester: Optional[int] = None
    credits: Optional[int] = None
    instructor_id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    syllabus_file_id: Optional[int] = None

class CourseRead(CourseBase):
    id: int
    syllabus_file_id: Optional[int] = None
    mindmap_id: Optional[int] = None
    enrolled_count: int
    instructor_name: Optional[str] = None
    class Config:
        from_attributes = True

# --- Enrollment ---
class CourseEnrollmentBase(BaseModel):
    course_id: int
    student_id: int
    enrollment_status: Optional[str] = "active"

class CourseEnrollmentCreate(CourseEnrollmentBase):
    pass

class CourseEnrollmentRead(CourseEnrollmentBase):
    id: int
    course: Optional[CourseRead] = None # Include course details
    
    class Config:
        from_attributes = True

# --- Bulk Import ---
class CourseImportJobRead(BaseModel):
    id: int
    uploaded_by: int
    file_id: int
    status: str
    total_rows: int
    success_count: int
    failure_count: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    class Config:
        from_attributes = True

class CourseImportRowRead(BaseModel):
    id: int
    job_id: int
    row_number: int
    raw_course_code: Optional[str] = None
    raw_title: Optional[str] = None
    raw_program_code: Optional[str] = None
    raw_year_level: Optional[int] = None
    raw_credits: Optional[str] = None
    raw_instructor_email: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_course_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- Token Schemas ---

class Token(BaseModel):
    """Schema for the JWT response upon successful login."""
    access_token: str
    token_type: str
    user_role: str


# --- Exam ---

class ExamCreate(BaseModel):
    title: str
    exam_type: str
    course_id: int
    exam_date: str # YYYY-MM-DD
    start_time: str # HH:MM
    duration_minutes: int
    status: str = "upcoming"
    faculty_id: Optional[int] = None

class ExamRead(BaseModel):
    id: int
    title: Optional[str] = None
    courseCode: str
    date: datetime
    start_time: Optional[datetime] = None # Added for explicit time display
    duration: int
    enrolled: int
    seatsAssigned: bool
    status: str
    faculty_id: Optional[int] = None
    faculty: Optional["FacultyRead"] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class TokenData(BaseModel):
    """Schema for data stored within the JWT payload."""
    sub: Optional[str] = None
    role: Optional[str] = None

# --- Room ---
class RoomBase(BaseModel):
    name: str
    building: str
    floor: str
    capacity: int
    layout: str
    accessibleSeats: int
    status: str

class RoomCreate(RoomBase):
    pass

class RoomRead(RoomBase):
    id: int
    class Config:
        from_attributes = True

class RoomSeatRead(BaseModel):
    id: int
    room_id: int
    seat_label: str
    row_number: Optional[int] = None
    col_number: Optional[int] = None
    is_accessible: bool
    
    class Config:
        from_attributes = True

class SeatAllocationRead(BaseModel):
    id: int
    exam_id: int
    student_id: int
    room_id: int
    seat_id: int
    manual_override: bool
    room: Optional["RoomRead"] = None
    seat: Optional["RoomSeatRead"] = None
    
    class Config:
        from_attributes = True

# --- Club Events ---

class ClubEventBase(BaseModel):
    title: str
    description: str
    start_datetime: datetime
    end_datetime: datetime
    venues: str
    attendees: int

class ClubEventCreate(ClubEventBase):
    pass

class ClubEventRead(ClubEventBase):
    id: int
    club_id: int
    status: str
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

# No forward refs needed because we defined Base/Basic classes first

# --- Notifications ---
class NotificationSchemaV2(BaseModel):
    id: int
    user_id: int
    type: Optional[str] = "info"
    title: Optional[str] = "Notification"
    body: Optional[str] = ""
    # DEBUG: Changed to Any to Bypass Initial Validation
    notification_metadata: Any = None 
    is_read: bool 
    created_at: Optional[datetime] = None

    @field_validator('notification_metadata', mode='before')
    @classmethod
    def parse_metadata_v2(cls, v):
        if isinstance(v, str):
            try:
                # print(f"Parsing metadata: {v}") 
                return json.loads(v)
            except ValueError:
                return {}
        return v

    class Config:
        from_attributes = True

# --- Faculty ---
class FacultyBase(BaseModel):
    faculty_type: str # 'TEACHING' or 'NON_TEACHING'
    department: Optional[str] = None
    designation: Optional[str] = None

class FacultyCreate(FacultyBase):
    user: Optional[UserCreate] = None  # Allow creating user along with faculty

class FacultyUpdate(BaseModel):
    faculty_type: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None

class FacultyCourseAssignmentCreate(BaseModel):
    faculty_id: int
    course_id: int

class FacultyCourseAssignmentRead(BaseModel):
    id: int
    faculty_id: int
    course_id: int
    assigned_at: Optional[datetime] = None
    course: Optional[CourseRead] = None
    
    class Config:
        from_attributes = True

class FacultyRead(FacultyBase):
    id: int
    user_id: int
    user: Optional[UserRead] = None
    course_assignments: List["FacultyCourseAssignmentRead"] = []
    
    class Config:
        from_attributes = True

class InvigilationDutyCreate(BaseModel):
    faculty_id: int
    exam_id: int
    room_id: Optional[int] = None
    status: Optional[str] = "assigned"

class ExamReadORM(BaseModel):
    id: int
    title: Optional[str] = None
    course_id: int
    exam_type: Optional[str] = None
    exam_date: datetime
    start_time: datetime
    duration_minutes: int
    status: str
    faculty_id: Optional[int] = None

    class Config:
        from_attributes = True

class InvigilationDutyRead(BaseModel):
    id: int
    faculty_id: int
    exam_id: int
    room_id: Optional[int] = None
    status: str
    
    exam: Optional[ExamReadORM] = None
    room: Optional[RoomRead] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class StudentMarkCreate(BaseModel):
    student_id: int
    course_id: int
    exam_type: str
    marks_obtained: int
    max_marks: int
    grader_id: Optional[int] = None

class StudentMarkRead(BaseModel):
    id: int
    student_id: int
    course_id: int
    exam_type: str
    marks_obtained: int
    max_marks: int
    grader_id: Optional[int]
    course: Optional[CourseRead] = None
    
    class Config:
        from_attributes = True

# --- TimeTable Schemas ---

class TimeTableEntryBase(BaseModel):
    day_of_week: str
    period_number: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    faculty_id: int
    course_id: int
    branch_id: Optional[int] = None
    semester: Optional[int] = None
    academic_year: Optional[int] = None
    room: Optional[str] = None
    class_type: Optional[str] = "Lecture"

class TimeTableEntryCreate(TimeTableEntryBase):
    pass

class TimeTableEntryRead(TimeTableEntryBase):
    id: int
    course: Optional[CourseRead] = None 
    faculty: Optional[FacultyRead] = None
    branch: Optional[BranchRead] = None

    class Config:
        from_attributes = True
# --- Academic Status ---
class SubjectResult(BaseModel):
    subject_id: str 
    subject_name: str
    credits: float
    marks: int
    is_pass: bool

class PromotionCheckRequest(BaseModel):
    student_id: str
    current_year: int
    updated_results: List[SubjectResult]
    credit_threshold: Optional[float] = 18.0 # Customizable threshold

class PromotionCheckResponse(BaseModel):
    student_id: str
    calculated_credits: float
    current_status: str
    action_taken: str
    remarks: str

