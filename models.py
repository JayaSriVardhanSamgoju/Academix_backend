from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db import Base
from sqlalchemy import Text, JSON

class Role(Base):
    __tablename__ = "roles" 

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)

class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False) # e.g. "B.Tech", "M.Tech"
    duration_years = Column(Integer, nullable=False) # e.g. 4
    file_prefix = Column(String(50), nullable=True) 
    
    branches = relationship("Branch", back_populates="program")

class Branch(Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False) # e.g. "Computer Science and Engineering"
    code = Column(String(20), nullable=False) # e.g. "CSE"
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False)

    program = relationship("Program", back_populates="branches")
    students = relationship("Student", back_populates="branch")
    courses = relationship("Course", back_populates="branch")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(150), nullable=True)
    phone = Column(String(15), nullable=True)
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    student = relationship("Student", back_populates="user", uselist=False)
    mindmaps = relationship("MindMap", back_populates="user")
    admin = relationship("Admin", back_populates="user", uselist=False)
    coordinator_profile = relationship("ClubCoordinator", back_populates="user", uselist=False)
    faculty = relationship("Faculty", back_populates="user", uselist=False)

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    phone_number = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True)

    user = relationship("User", back_populates="admin")

class ClubCoordinator(Base):
    __tablename__ = "club_coordinators"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    department = Column(String(100), default="General")
    designation = Column(String(100), default="Faculty Coordinator")
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="coordinator_profile")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    roll_number = Column(String(50), unique=True, nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True) # Linked to Branch
    current_semester = Column(Integer, nullable=True) # e.g. 1-8
    year = Column(Integer) # Keep for year (1st year, etc) if needed, or derive from semester
    academic_status = Column(String(50), default="PROMOTED") # e.g. PROMOTED, CREDIT_SHORTAGE, DETAINED

    branch = relationship("Branch", back_populates="students")
    user = relationship("User", back_populates="student")
    enrollments = relationship("CourseEnrollment", back_populates="student")
    seat_allocations = relationship("SeatAllocation", back_populates="student")

    @property
    def enrolled_courses(self):
        return len([e for e in self.enrollments if e.enrollment_status == "active"])

# Added Course model to support Exams.course_id foreign key and relationship
class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    title = Column(String(100), nullable=False)  # Add this

    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True) # Belongs to a branch
    semester = Column(Integer, nullable=False) # Which semester (1-8)
    year_level = Column(Integer, nullable=True) # Keep for backward compat or broad filtering
    enrolled_count = Column(Integer, default=0)  # Add this
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)  
    credits = Column(Integer, nullable=True)
    syllabus_text = Column(Text, nullable=True) # Added for Mind Map generation
    mindmap_id = Column(Integer, ForeignKey("mindmaps.id"), nullable=True) # Link to generated MindMap
    instructor_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    branch = relationship("Branch", back_populates="courses")
    instructor = relationship("Faculty")
    assignments = relationship("FacultyCourseAssignment", back_populates="course")

    @property
    def instructor_name(self):
        if self.instructor and self.instructor.user:
            return self.instructor.user.name
        
        # Fallback to the first assigned faculty if any
        if self.assignments and self.assignments[0].faculty and self.assignments[0].faculty.user:
            return self.assignments[0].faculty.user.name
            
        return "Not Assigned"

class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    enrollment_status = Column(String(50), default="active")
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())

    course = relationship("Course")
    student = relationship("Student", back_populates="enrollments")



class Exams(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=True) # Added title
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    exam_type = Column(String(50)) # e.g., "MID", "SEM", "LAB"
    exam_date = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(String(50), default="upcoming")
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True) # Primary Assignee/Invigilator
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    course = relationship("Course")
    faculty = relationship("Faculty")

class ExamStudent(Base):
    __tablename__ = "exam_students"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    exam = relationship("Exams")
    student = relationship("Student")

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    building = Column(String(100), nullable=False)
    floor = Column(String(50), nullable=False)
    capacity = Column(Integer, nullable=False)
    layout = Column(String(20), nullable=False)
    accessibleSeats = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)
    seats = relationship("RoomSeat", back_populates="room")
    seat_allocations = relationship("SeatAllocation", back_populates="room")

class RoomSeat(Base):
    __tablename__ = "room_seats"
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    seat_label = Column(String(20), nullable=False)
    row_number = Column(Integer)
    col_number = Column(Integer)
    is_accessible = Column(Boolean, default=False)
    room = relationship("Room", back_populates="seats")
    seat_allocations = relationship("SeatAllocation", back_populates="seat")

class SeatAllocation(Base):
    __tablename__ = "seat_allocations"
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("room_seats.id"), nullable=False)
    manual_override = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    exam = relationship("Exams")
    student = relationship("Student", back_populates="seat_allocations")
    room = relationship("Room", back_populates="seat_allocations")
    seat = relationship("RoomSeat", back_populates="seat_allocations")

class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, nullable=False)
    category = Column(String(100))
    faculty_coordinator = Column(String(150))
    faculty_contact = Column(String(20))
    active_members = Column(Integer, default=0)
    
    # Link to the User (Club Coordinator)
    coordinator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    coordinator = relationship("User")

    events = relationship("ClubEvent", back_populates="club")

class ClubEvent(Base):
    __tablename__ = "club_events"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text)
    status = Column(String(50), default='draft')
    start_datetime = Column(DateTime)
    end_datetime = Column(DateTime)
    venues = Column(Text)
    attendees = Column(Integer)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    club = relationship("Club", back_populates="events")
    creator = relationship("User")
    documents = relationship("EventDocument", back_populates="event")
    registrations = relationship("EventRegistration", back_populates="event")

class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("club_events.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())

    event = relationship("ClubEvent", back_populates="registrations")
    student = relationship("Student")

class EventDocument(Base):
    __tablename__ = "event_documents"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("club_events.id"), nullable=False)
    doc_type = Column(String(100))
    file_url = Column(String(255))
    status = Column(String(50), default='uploaded')
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)

    event = relationship("ClubEvent", back_populates="documents")
    reviewer = relationship("User")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50))
    title = Column(String(150))
    body = Column(Text)
    notification_metadata = Column(JSON)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100))
    entity_type = Column(String(100))
    entity_id = Column(Integer)
    old_value = Column(JSON)
    new_value = Column(JSON)
    reason = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    actor = relationship("User")

class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    owner_type = Column(String(50), nullable=False)
    owner_id = Column(Integer, nullable=False)
    file_name = Column(String(255), nullable=False)
    storage_path = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

class CourseImportJob(Base):
    __tablename__ = "course_import_jobs"
    id = Column(Integer, primary_key=True, index=True)
    uploaded_by = Column(Integer, nullable=False)  # user id
    file_id = Column(Integer, nullable=False)      # file id (from File model)
    status = Column(String(50), default="pending")
    total_rows = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MindMap(Base):
    __tablename__ = "mindmaps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), index=True)
    data = Column(JSON)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="mindmaps")

class Faculty(Base):
    __tablename__ = "faculty"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    faculty_type = Column(String(50), nullable=False) # 'TEACHING' or 'NON_TEACHING'
    department = Column(String(100))
    designation = Column(String(100))
    
    user = relationship("User", back_populates="faculty")
    course_assignments = relationship("FacultyCourseAssignment", back_populates="faculty")
    invigilation_duties = relationship("InvigilationDuty", back_populates="faculty")

class FacultyCourseAssignment(Base):
    __tablename__ = "faculty_course_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    faculty = relationship("Faculty", back_populates="course_assignments")
    course = relationship("Course", back_populates="assignments")

class InvigilationDuty(Base):
    __tablename__ = "invigilation_duties"
    
    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    status = Column(String(50), default="assigned")
    
    faculty = relationship("Faculty", back_populates="invigilation_duties")
    exam = relationship("Exams") 
    room = relationship("Room")

class StudentMark(Base):
    __tablename__ = "student_marks"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    exam_type = Column(String(50), nullable=False) # MID1, MID2, SEM, etc.
    marks_obtained = Column(Integer, nullable=False)
    max_marks = Column(Integer, nullable=False)
    grader_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)
    
    student = relationship("Student")
    course = relationship("Course")
    grader = relationship("Faculty")

class TimeTableEntry(Base):
    __tablename__ = "timetable_entries"

    id = Column(Integer, primary_key=True, index=True)
    day_of_week = Column(String(20), nullable=False) # Monday, Tuesday...
    period_number = Column(Integer, nullable=False) # 1 to 6
    start_time = Column(String(10), nullable=True) # "09:30"
    end_time = Column(String(10), nullable=True) # "10:30"
    
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    
    # Ideally link to a specific Section/Branch. For now, link to Branch to allow filtering.
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True) 
    semester = Column(Integer, nullable=True)
    academic_year = Column(Integer, nullable=True) # e.g. 2024
    room = Column(String(50), nullable=True) # e.g. "A-101"
    class_type = Column(String(20), nullable=True) # "Lecture", "Lab", etc.
    
    faculty = relationship("Faculty")
    course = relationship("Course")
    branch = relationship("Branch")
