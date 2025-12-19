from db import SessionLocal
import models
from sqlalchemy import or_

def inspect():
    db = SessionLocal()
    output = []

    output.append("--- Programs (All) ---")
    progs = db.query(models.Program).all()
    for p in progs:
        output.append(f"ID: {p.id}, Name: {p.name}")

    output.append("\n--- Branches (All) ---")
    branches = db.query(models.Branch).all()
    for b in branches:
        prog_name = b.program.name if b.program else "None"
        output.append(f"ID: {b.id}, Code: {b.code}, Name: {b.name}, Program: {prog_name}")

    output.append("\n--- Courses (Limit 20) ---")
    courses = db.query(models.Course).limit(20).all()
    for c in courses:
        b_code = c.branch.code if c.branch else "None"
        output.append(f"ID: {c.id}, Code: {c.code}, Title: {c.title}, Branch: {b_code}, Sem: {c.semester}")

    db.close()
    
    with open("backend/db_inspection.txt", "w") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    inspect()
