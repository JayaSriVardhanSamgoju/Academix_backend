from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from db import get_db
from models import Room, RoomSeat
from schemas import RoomCreate, RoomRead, RoomSeatRead

router = APIRouter()

@router.get("/rooms", response_model=list[RoomRead])
def get_rooms(db: Session = Depends(get_db)):
    return db.query(Room).all()

@router.post("/rooms", response_model=RoomRead)
def create_room(room: RoomCreate, db: Session = Depends(get_db)):
    db_room = Room(**room.dict())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)

    # Auto-generate seats based on layout "RxC"
    try:
        layout_str = db_room.layout.lower()  # e.g., "5x6"
        if 'x' in layout_str:
            rows, cols = map(int, layout_str.split('x'))
            seats = []
            for r in range(1, rows + 1):
                for c in range(1, cols + 1):
                    # Labels: A1, A2... B1...
                    row_label = chr(64 + r) # 1=A, 2=B...
                    seat_label = f"{row_label}{c}"
                    seats.append(RoomSeat(
                        room_id=db_room.id,
                        seat_label=seat_label,
                        row_number=r,
                        col_number=c,
                        is_accessible=False
                    ))
            db.add_all(seats)
            db.commit()
    except Exception as e:
        print(f"Error generating seats: {e}")

    return db_room

@router.get("/rooms/{room_id}/seats", response_model=list[RoomSeatRead])
def get_room_seats(room_id: int, db: Session = Depends(get_db)):
    return db.query(RoomSeat).filter(RoomSeat.room_id == room_id).all()
