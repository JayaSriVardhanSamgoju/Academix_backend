from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Annotated

from db import SessionLocal
import models, schemas
import auth_router

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/me")
def get_student_notifications(
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    import json
    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id
    ).order_by(models.Notification.created_at.desc()).all()

    results = []
    for n in notifications:
        # Manual serialization to handle SQLite JSON string quirk
        meta = n.notification_metadata
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}
        elif meta is None:
            meta = {}
        
        results.append({
            "id": n.id,
            "user_id": n.user_id,
            "type": n.type or "info",
            "title": n.title,
            "body": n.body,
            "notification_metadata": meta,
            "is_read": n.is_read,
            "created_at": n.created_at
        })
    
    return results
