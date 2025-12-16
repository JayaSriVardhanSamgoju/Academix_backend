from sqlalchemy.orm import Session
import db
import models

def seed_academic_data():
    session = db.SessionLocal()
    try:
        print("Seeding academic data...")
        
        # 1. Create Programs
        programs_data = [
            {"name": "Bachelors of Technology", "duration_years": 4, "file_prefix": "BTECH"},
            {"name": "Masters of Technology", "duration_years": 2, "file_prefix": "MTECH"}
        ]
        
        for p_data in programs_data:
            existing = session.query(models.Program).filter_by(name=p_data["name"]).first()
            if not existing:
                program = models.Program(**p_data)
                session.add(program)
                print(f"Created Program: {p_data['name']}")
            else:
                print(f"Program {p_data['name']} already exists")
        session.commit()
        
        # 2. Create Branches
        btech = session.query(models.Program).filter_by(name="Bachelors of Technology").first()
        mtech = session.query(models.Program).filter_by(name="Masters of Technology").first()
        
        branches_data = []
        if btech:
            branches_data.extend([
                {"name": "Computer Science and Engineering", "code": "CSE", "program_id": btech.id},
                {"name": "Electronics and Communication Engineering", "code": "ECE", "program_id": btech.id},
                {"name": "Mechanical Engineering", "code": "ME", "program_id": btech.id},
                {"name": "Chemical Engineering", "code": "CHE", "program_id": btech.id},
                {"name": "Civil Engineering", "code": "CE", "program_id": btech.id},
                {"name": "Electrical Engineering", "code": "EE", "program_id": btech.id},
            ])
        
        if mtech:
             branches_data.extend([
                {"name": "Computer Science(AI)", "code": "CS", "program_id": mtech.id},
                {"name": "Computer Science(Data Science)", "code": "CS", "program_id": mtech.id},
                {"name": "Computer Science(CyberSecurity)", "code": "CS", "program_id": mtech.id},
                {"name": "Computer Science(Machine Learning)", "code": "CS", "program_id": mtech.id},
                {"name": "Electronics(Embedded Systems)", "code": "ECE", "program_id": mtech.id},
                {"name": "Electronics(VLSI)", "code": "ECE", "program_id": mtech.id},
                {"name": "Mechanical Engineering(Robotics)", "code": "ME", "program_id": mtech.id},
                {"name": "Mechanical Engineering(Automobile)", "code": "ME", "program_id": mtech.id},
                {"name": "Chemical Engineering(Pharmaceutical)", "code": "CHE", "program_id": mtech.id},
                {"name": "Civil Engineering(Highway)", "code": "CE", "program_id": mtech.id},
                {"name": "Civil Engineering(Hydraulic)", "code": "CE", "program_id": mtech.id},
                {"name": "Electrical Engineering(Signal Processing)", "code": "EE", "program_id": mtech.id},
                {"name": "Electrical Engineering(Solar Energy)", "code": "EE", "program_id": mtech.id},
                {"name": "Electrical Engineering(Wireless Communication)", "code": "EE", "program_id": mtech.id},
            ])
            
        for b_data in branches_data:
            existing = session.query(models.Branch).filter_by(program_id=b_data["program_id"], name=b_data["name"]).first()
            if not existing:
                branch = models.Branch(**b_data)
                session.add(branch)
                print(f"Created Branch: {b_data['code']} under Program ID {b_data['program_id']}")
            else:
                 print(f"Branch {b_data['code']} already exists")
        
        session.commit()
        print("Academic data seeding complete.")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error seeding data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    try:
        print("Resetting database schema...")
        db.Base.metadata.drop_all(bind=db.engine)
        db.Base.metadata.create_all(bind=db.engine) # Ensure tables exist
        seed_academic_data()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error during initialization: {e}")
