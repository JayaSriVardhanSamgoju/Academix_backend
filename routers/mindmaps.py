from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Annotated
import os
import shutil
import uuid

from db import SessionLocal
import models, schemas
import auth_router
from utils.pdf_utils import extract_text_from_pdf
from utils.mind_map_generator import generate_mind_map_json

router = APIRouter(prefix="/mindmaps", tags=["mindmaps"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload")
async def create_mind_map(
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    1. Upload PDF
    2. Extract Text
    3. Generate JSON via Gemini
    4. Save to DB
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Generate a unique temp filename
    file_ext = file.filename.split(".")[-1]
    temp_filename = os.path.join("/tmp", f"temp_{uuid.uuid4()}.{file_ext}")
    
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 1. Extract Text
        text = extract_text_from_pdf(temp_filename)
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")

        # 2. Generate Mind Map
        # Limiting text to prevent context windows issues (handled in generator too)
        mind_map_data = generate_mind_map_json(text)
        
        # 3. Save to DB
        new_map = models.MindMap(
            user_id=current_user.id,
            title=file.filename,
            data=mind_map_data
        )
        db.add(new_map)
        db.commit()
        db.refresh(new_map)
        
        return new_map

    except Exception as e:
        print(f"MindMap Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

@router.post("/generate-from-course/{course_id}")
def generate_mind_map_from_course(
    course_id: int,
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    Generate mind map from Course Syllabus provided by Admin.
    """
    # 1. Fetch Course
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    if not course.syllabus_text:
        raise HTTPException(status_code=400, detail="This course does not have a syllabus defined by the admin.")

    # 2. Check if user already has a map for this course (optional, but good practice to avoid duplicates or overwrite)
    # For now, let's create a new one every time to allow regeneration.

    try:
        # 3. Generate Mind Map
        mind_map_data = generate_mind_map_json(course.syllabus_text)
        
        # 4. Save to DB
        new_map = models.MindMap(
            user_id=current_user.id,
            title=f"{course.title} - Syllabus Map",
            data=mind_map_data
        )
        db.add(new_map)
        db.commit()
        db.refresh(new_map)
        
        return new_map

    except Exception as e:
        print(f"MindMap Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mine")
def get_my_mind_maps(
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    return db.query(models.MindMap).filter(models.MindMap.user_id == current_user.id).order_by(models.MindMap.created_at.desc()).all()

@router.get("/{map_id}")
def get_mind_map(
    map_id: int,
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    # Allow fetching if user owns it
    result = db.query(models.MindMap).filter(models.MindMap.id == map_id, models.MindMap.user_id == current_user.id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Mind Map not found")
    return result

@router.get("/all/admin")
def get_all_mind_maps_admin(
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_admin)],
    db: Session = Depends(get_db)
):
    """
    Admin: Fetch ALL generated mind maps.
    """
    # Join with User to get creator info if needed, but default query loads IDs
    return db.query(models.MindMap).order_by(models.MindMap.created_at.desc()).all()
