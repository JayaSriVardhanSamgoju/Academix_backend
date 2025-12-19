from db import SessionLocal
import models
from sqlalchemy import or_

db = SessionLocal()

print("--- Programs (Matching 'Tech') ---")
progs = db.query(models.Program).filter(models.Program.name.ilike('%Tech%')).all()
for p in progs:
    print(f"ID: {p.id}, Name: {p.name}")

print("\n--- Branches (Matching 'AI' or 'CS') ---")
branches = db.query(models.Branch).filter(
    or_(
        models.Branch.name.ilike('%AI%'), 
        models.Branch.code.ilike('%AI%'),
        models.Branch.code.ilike('%CS%')
    )
).all()

for b in branches:
    prog_name = b.program.name if b.program else "None"
    print(f"ID: {b.id}, Code: {b.code}, Name: {b.name}, Program: {prog_name}")

print("\n--- Courses (Matching 'AI' or 'CS') ---")
courses = db.query(models.Course).filter(
    or_(
        models.Course.title.ilike('%AI%'), 
        models.Course.title.ilike('%Intelligence%'),
        models.Course.code.ilike('%CS%')
    )
).limit(20).all()

for c in courses:
    b_code = c.branch.code if c.branch else "None"
    print(f"ID: {c.id}, Code: {c.code}, Title: {c.title}, Branch: {b_code}, Sem: {c.semester}")

db.close()
