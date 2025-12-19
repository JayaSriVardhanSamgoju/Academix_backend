from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import db
import models
import schemas
import auth_router

router = APIRouter(prefix="/programs", tags=["programs"])

def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

# --- Programs ---

@router.post("/", response_model=schemas.ProgramRead, status_code=status.HTTP_201_CREATED)
def create_program(program_in: schemas.ProgramCreate, db_session: Session = Depends(get_db)):
    existing = db_session.query(models.Program).filter(models.Program.name == program_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Program already exists")
    
    program = models.Program(**program_in.dict())
    db_session.add(program)
    db_session.commit()
    db_session.refresh(program)
    return program

@router.get("/", response_model=List[schemas.ProgramRead])
def list_programs(db_session: Session = Depends(get_db)):
    # Optional: Eager load branches
    programs = db_session.query(models.Program).all()
    return programs

# --- Branches ---

@router.post("/{program_id}/branches", response_model=schemas.BranchRead, status_code=status.HTTP_201_CREATED)
def create_branch(program_id: int, branch_in: schemas.BranchCreate, db_session: Session = Depends(get_db)):
    program = db_session.query(models.Program).filter(models.Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
        
    existing = db_session.query(models.Branch).filter(
        models.Branch.program_id == program_id, 
        models.Branch.code == branch_in.code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Branch code already exists in this program")

    branch = models.Branch(
        **branch_in.dict(),
        program_id=program_id
    )
    db_session.add(branch)
    db_session.commit()
    db_session.refresh(branch)
    return branch

@router.get("/{program_id}/branches", response_model=List[schemas.BranchRead])
def list_branches(program_id: int, db_session: Session = Depends(get_db)):
    branches = db_session.query(models.Branch).filter(models.Branch.program_id == program_id).all()
    return branches

@router.get("/branches/all", response_model=List[schemas.BranchRead])
def list_all_branches(db_session: Session = Depends(get_db)):
    return db_session.query(models.Branch).all()
