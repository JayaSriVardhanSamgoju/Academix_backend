
import random
from sqlalchemy.orm import Session
from db import SessionLocal, engine
import models

def seed_rooms():
    db = SessionLocal()
    try:
        buildings = ["Main Block", "CSE Block", "ECE Block", "Mech Block", "Library Block", "R&D Block"]
        floors = ["Ground", "1", "2", "3", "4"]
        statuses = ["Active", "Active", "Active", "Active", "Under maintenance"] 
        
        layout_options = [
            {"cap": 30, "layout": "5x6"},
            {"cap": 40, "layout": "5x8"},
            {"cap": 48, "layout": "6x8"},
            {"cap": 60, "layout": "6x10"},
            {"cap": 72, "layout": "6x12"},
            {"cap": 120, "layout": "10x12"},
        ]

        count = 0
        used_names = set()

        while count < 45:
            building = random.choice(buildings)
            floor = random.choice(floors)
            
            b_prefix = building.split()[0]
            if b_prefix == "R&D": b_prefix = "RnD"
            
            f_digit = "0"
            if floor != "Ground":
                f_digit = floor
            
            r_num = random.randint(1, 20)
            
            name = f"{b_prefix}-{f_digit}{r_num:02d}"
            
            if name in used_names:
                continue
                
            used_names.add(name)
            
            config = random.choice(layout_options)
            
            status = random.choice(statuses)
            
            room = models.Room(
                name=name,
                building=building,
                floor=floor,
                capacity=config["cap"],
                layout=config["layout"],
                accessibleSeats=random.randint(0, 4),
                status=status
            )
            
            db.add(room)
            db.commit()
            db.refresh(room)
            
            # Generate Seats for this room
            try:
                rows, cols = map(int, config["layout"].split('x'))
                seats = []
                for r in range(1, rows + 1):
                    for c in range(1, cols + 1):
                        row_label = chr(64 + r) # 1=A, 2=B...
                        seat_label = f"{row_label}{c}"
                        
                        # 10% chance of being accessible if it's a front row
                        is_acc = False
                        if r == 1 and random.random() < 0.2:
                            is_acc = True
                            
                        seats.append(models.RoomSeat(
                            room_id=room.id,
                            seat_label=seat_label,
                            row_number=r,
                            col_number=c,
                            is_accessible=is_acc
                        ))
                
                db.add_all(seats)
                db.commit()
                
            except Exception as e:
                print(f"Error generating seats for {name}: {e}")
                
            count += 1
            if count % 10 == 0:
                print(f"Seeded {count} rooms...")

    except Exception as e:
        print(f"Seeding failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_rooms()
