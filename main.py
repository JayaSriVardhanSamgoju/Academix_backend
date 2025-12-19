from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError
import logging
import os
from routers import students, exams, notifications, admin, courses, rooms, allocations, clubs, hall_ticket, calendar, mindmaps, programs, faculty, timetable

# FIX: Changed relative imports (e.g., from .db import ...) to direct imports
# assuming all files (db.py, auth_router.py, etc.) are in the same directory.
import db
import auth_router

# Configure logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# --- Application Setup ---
app = FastAPI(
    title="Academic & Examination Management API",
    description="Integrated platform for academic scheduling, examination, and campus event management.",
    version="1.0.0"
)

# --- CORS Configuration ---
# Modern browsers block "*" when allow_credentials=True.
# We explicitly allow the default Vite dev server port.
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex="https://.*\.railway\.app", # For production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600, # Cache preflight requests for 1 hour
)

# Function to create tables (called on startup)
def create_db_tables():
    """Create all tables defined in models.py if they don't exist."""
    print("Attempting to create database tables...")
    import models 
    db.Base.metadata.create_all(bind=db.engine)

# --- Startup Event ---
@app.on_event("startup")
def on_startup():
    """Handles database connection check and table creation on application start."""
    try:
        create_db_tables()
        print("Database connection successful. Tables checked/created.")
    except SQLAlchemyError as e:
        print(f"FATAL ERROR: Database initialization failed. Check your MySQL connection settings. Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during startup: {e}")

# --- Include Routers with /api prefix ---
app.include_router(auth_router.auth_router, prefix="/api")
app.include_router(students.router, prefix="/api")
app.include_router(exams.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(rooms.router, prefix="/api")
app.include_router(allocations.router, prefix="/api")
app.include_router(clubs.router, prefix="/api", tags=["Clubs"])
app.include_router(hall_ticket.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(mindmaps.router, prefix="/api")
app.include_router(programs.router, prefix="/api")
app.include_router(faculty.router, prefix="/api")
app.include_router(timetable.router, prefix="/api")

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "ACADEMIX AI Backend is running. Access docs at /docs"}