from datetime import datetime
from typing import Annotated, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import config
import schemas
import models
import db

# --- Compatibility Patch for passlib + bcrypt 4.x ---
# Passlib < 1.7.5 issues with bcrypt >= 4.0
import bcrypt
try:
    if not hasattr(bcrypt, '__about__'):
        class About:
            __version__ = bcrypt.__version__
        bcrypt.__about__ = About()
except ImportError:
    pass

# --- Security & CRUD Utilities ---
pwd_context = CryptContext(schemes=["bcrypt","argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=config.TOKEN_URL)

def get_password_hash(password: str) -> str:
    """Hashes a plain password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed one."""
    # This is the line that failed in the logs due to a bad hash format.
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    """Generates a JWT access token with a fixed expiration."""
    to_encode = data.copy()
    expire = datetime.utcnow() + config.ACCESS_TOKEN_EXPIRE_DELTA
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

def get_user_by_email(db_session: Session, email: str) -> Optional[models.User]:
    """CRUD: Retrieves a user by email."""
    # Renamed 'db' parameter to 'db_session' to avoid shadowing the imported 'db' module
    return db_session.query(models.User).filter(models.User.email == email).first()

def create_db_user(db_session: Session, user: schemas.UserCreate) -> models.User:
    """CRUD: Creates a new user."""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email, 
        hashed_password=hashed_password,
        name=user.name,
        phone=user.phone,
        # Ensure the role is valid, default to Student
        role=user.role if user.role in config.ROLES else "Student"
    )
    db_session.add(db_user)
    db_session.commit()
    db_session.refresh(db_user)
    return db_user

def authenticate_user(db_session: Session, email: str, password: str) -> Optional[models.User]:
    """Authenticates a user using email and password."""
    user = get_user_by_email(db_session, email=email)
    if not user or not user.is_active or not verify_password(password, user.hashed_password):
        return None
    return user

# --- Authentication Dependencies ---

def get_current_user(
    db_session: Annotated[Session, Depends(db.get_db)], # Use db.get_db here
    token: Annotated[str, Depends(oauth2_scheme)]
) -> models.User:
    """Decodes the JWT token and fetches the user from the database."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None or role is None:
            raise credentials_exception
        # TokenData object now contains role for clearer dependency checks
        token_data = schemas.TokenData(sub=email, role=role) 
    except JWTError:
        raise credentials_exception
    
    # Pass db_session to the helper function
    user = get_user_by_email(db_session, email=token_data.sub) 
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: Annotated[models.User, Depends(get_current_user)]) -> models.User:
    """Dependency: Ensures the authenticated user is active. Accessible by all roles."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

# --- Role-Specific Dependencies ---

def get_current_active_role(current_user: models.User, required_role: str) -> models.User:
    """Helper function to enforce a specific role."""
    if current_user.role != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required role: {required_role}. Your role: {current_user.role}"
        )
    return current_user

def get_current_active_admin(current_user: Annotated[models.User, Depends(get_current_active_user)]) -> models.User:
    """Dependency: Enforces 'Admin' role."""
    return get_current_active_role(current_user, "Admin")

def get_current_active_seating_manager(current_user: Annotated[models.User, Depends(get_current_active_user)]) -> models.User:
    """Dependency: Enforces 'Seating Manager' role."""
    return get_current_active_role(current_user, "Seating Manager")

def get_current_active_club_coordinator(current_user: Annotated[models.User, Depends(get_current_active_user)]) -> models.User:
    """Dependency: Enforces 'Club Coordinator' role."""
    return get_current_active_role(current_user, "Club Coordinator")

def get_current_active_student(current_user: Annotated[models.User, Depends(get_current_active_user)]) -> models.User:
    """Dependency: Enforces 'Student' role."""
    return get_current_active_role(current_user, "Student")


# --- API Router Definition ---

auth_router = APIRouter(prefix="/auth", tags=["Auth & Users"])

# --- Public Routes ---

@auth_router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db_session: Annotated[Session, Depends(db.get_db)]):
    """Creates a new user account (role is strictly set to Student for public registration)."""
    db_user = get_user_by_email(db_session, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # SECURITY FIX: Forcing role to "Student" for all public registrations 
    # to prevent privilege escalation attempts, regardless of what role was submitted.
    user.role = "Student" 
    
    # Create the user
    created_user = create_db_user(db_session=db_session, user=user)
    
    # Automatically create a student profile if the role is "Student"
    if created_user.role == "Student":
        # Generate a temporary roll number based on user ID
        temp_roll_number = f"STU{created_user.id:05d}"
        
        student = models.Student(
            user_id=created_user.id,
            roll_number=temp_roll_number,
            # Note: Program and branch/year data need proper assignment outside of this router
            program="Not Set", 
            year=1
        )
        db_session.add(student)
        db_session.commit()
    
    return created_user

@auth_router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db_session: Annotated[Session, Depends(db.get_db)]
):
    """Handles user login and returns a JWT access token."""
    user = authenticate_user(db_session, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role} # Embed email (subject) and role in the token
    )
    return {"access_token": access_token, "token_type": "bearer", "user_role": user.role}

# --- General Protected Route (All Active Roles) ---

@auth_router.get("/users/me", response_model=schemas.UserRead)
async def read_users_me(current_user: Annotated[models.User, Depends(get_current_active_user)]):
    """Returns the current authenticated user's information. Accessible by ALL active users."""
    return current_user

# --- Role-Specific Protected Routes (Demonstration) ---

@auth_router.get("/admin/dashboard-access")
async def admin_dashboard_access(current_user: Annotated[models.User, Depends(get_current_active_admin)]):
    """Endpoint only accessible by 'Admin' role users."""
    return {"message": f"Welcome, Admin {current_user.email}! You can now manage the academic calendar and user roles."}

@auth_router.get("/seating-manager/allocation-tool")
async def seating_manager_tool_access(current_user: Annotated[models.User, Depends(get_current_active_seating_manager)]):
    """Endpoint only accessible by 'Seating Manager' role users."""
    return {"message": f"Welcome, Seating Manager {current_user.email}! You have access to the seating allocation module."}

@auth_router.get("/club-coordinator/event-submission")
async def club_coordinator_submission_access(current_user: Annotated[models.User, Depends(get_current_active_club_coordinator)]):
    """Endpoint only accessible by 'Club Coordinator' role users."""
    return {"message": f"Welcome, Club Coordinator {current_user.email}! You can submit event proposals for approval."}

@auth_router.get("/student/schedule")
async def student_schedule_access(current_user: Annotated[models.User, Depends(get_current_active_student)]):
    """Endpoint only accessible by 'Student' role users."""
    return {"message": f"Welcome, Student {current_user.email}! Here is your personalized academic schedule and hall ticket status."}