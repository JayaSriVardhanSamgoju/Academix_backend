from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import sys
import os

import models
import config
import auth_router as auth
import random
import string

# Setup direct connection
engine = create_engine(config.SQLALCHEMY_DATABASE_URL)
session = Session(bind=engine)

def seed_students():
    try:
        print("Seeding students from provided list...")
        
        # List of students (Roll Number, Name) extracted from the image
        students_data = [
            ("22R21A6701", "AMMAPURAM AKSHITH REDDY"),
            ("22R21A6702", "ANNADI CHANDRA KIRAN REDDY"),
            ("22R21A6703", "A SAI CHARAN"),
            ("22R21A6704", "BOINI PAVAN"),
            ("22R21A6705", "B RAJESH KOUSHIK"),
            ("22R21A6706", "BATHULA POOJITHA"),
            ("22R21A6707", "BHAVANI SAHITH REDDY"),
            ("22R21A6708", "CHILUKALA LAHARIKA"),
            ("22R21A6709", "C SIRI CHANDANA"),
            ("22R21A6710", "D CHANDRA HAS"),
            ("22R21A6711", "DONTHULA MANOGNA"),
            ("22R21A6712", "EJJAGANI SUHAS"),
            ("22R21A6713", "ERUKULLA PREM SAI"),
            ("22R21A6714", "GATTU BALAJI PRASAD"),
            ("22R21A6715", "GOLI SATHWIK"),
            ("22R21A6716", "GUNDALA MANIKANTA"),
            ("22R21A6717", "GUTTI VISISTA"),
            ("22R21A6718", "J HARSHA VARDHAN REDDY"),
            ("22R21A6719", "JEEVANA SRIJA REDDY"),
            ("22R21A6720", "K ANISH ROY"),
            ("22R21A6721", "KAMISHETTI VAMSHI KRISHNA"),
            ("22R21A6722", "KONDAM HIMAVARSHINI"),
            ("22R21A6723", "KOTNAK NAVEEN"),
            ("22R21A6724", "M PAVAN KALYAN"),
            ("22R21A6725", "N RAKESH CHANDRA"),
            ("22R21A6726", "NAGAM SHIVA SAI PRAKASH"),
            ("22R21A6727", "PADALA SAI TEJA"),
            ("22R21A6728", "PEDDINTI HARSHAVARDHAN"),
            ("22R21A6729", "PULI SATHWIK REDDY"),
            ("22R21A6730", "R NANDINI"),
            ("22R21A6731", "RAVIPATI GOWTHAM KRISHNA"),
            ("22R21A6732", "S SAI SREEJA"),
            ("22R21A6733", "S SOWMYA"),
            ("22R21A6734", "SANKITI CHARAN TEJA"),
            ("22R21A6735", "SHAIK MOHAMMAD SAIF ALI"),
            ("22R21A6736", "SOMA ANUSHKA"),
            ("22R21A6737", "SRIRAMOJU ABHINAY"),
            ("22R21A6738", "SURAM PREETHI"),
            ("22R21A6739", "THODUPUNURI ABHILASH"),
            ("22R21A6740", "THOTA ABHIRAM"),
            ("22R21A6741", "VADISALA NITHIN REDDY"),
            ("22R21A6742", "VELISHALA VISHWAK"),
            ("22R21A6743", "YELLU MAHESHWARI"),
            ("22R21A6744", "YERRA ARCHANA"),
            ("22R21A6745", "B CHANDRAKANTH"),
            ("22R21A6746", "BANDARI MANOHAR"),
            ("22R21A6747", "BANDI SAI KUMAR REDDY"),
            ("22R21A6748", "CHENNURI SAI CHARAN"),
            ("22R21A6749", "CHERUKU VISHNU VARDHAN REDDY"),
            ("22R21A6750", "CHINTA SAI KIRAN"),
            ("22R21A6751", "CHINTHALA SHYAMSUNDER REDDY"),
            ("22R21A6752", "DONTHULA MANISH"),
            ("22R21A6753", "DUBASI ABHINAV"),
            ("22R21A6754", "GATTU VISHNUTEJA"),
            ("22R21A6755", "JADI RAKESH"),
            ("22R21A6756", "KANDI SATHWIK REDDY"),
            ("22R21A6757", "KATTA SAKETH"),
            ("22R21A6758", "KETHAVATH KALYAN NAIK"),
            ("22R21A6759", "KODIMYALA ESHWAR"),
            ("22R21A6760", "KOLANU KOUSHIK REDDY"),
            ("22R21A6761", "NALLALA VISHNU VARDHAN REDDY"),
            ("22R21A6762", "PYDI SRIKAR"),
            ("22R21A6763", "R SIDDARTH"),
            ("22R21A6764", "RAVULA VARUN TEJA"),
            ("23R25A6701", "DHARAVATH PRAVEEN"),
            ("23R25A6702", "GADDAM SHANMUKHA CHARI"),
            ("23R25A6703", "KADAMANCHI NITHIN"),
            ("23R25A6704", "KALERU SAI TEJA"),
            ("23R25A6705", "MD IBRAHIM KHALEEL"),
            ("23R25A6706", "MOHAMMAD RAFI"),
            ("23R25A6707", "MOHAN REDDY"),
            ("23R25A6708", "SRIKANTH"),
            ("23R25A6709", "VENKAT SAI"),
            ("23R25A6710", "VARUN KUMAR"),
            ("23R25A6711", "SAI PRASAD"),
            ("23R25A6712", "HARISH KUMAR"),
            ("23R25A6713", "ANIL REDDY"),
            ("23R25A6714", "PAVAN KUMAR REDDY"),
            ("23R25A6715", "MAHESH GOUD"),
            ("23R25A6716", "SURESH BABU"),
            ("23R25A6717", "RAMESH CHANDRA"),
            ("23R25A6718", "NAVYA SRI"),
            ("23R25A6719", "POOJA RANI"),
            ("23R25A6720", "ANUSHA REDDY"),
            ("23R25A6721", "MOHAN KUMAR"),
            ("23R25A6722", "SAI KUMAR"),
            ("23R25A6723", "SRINIVAS REDDY"),
            ("23R25A6724", "VIKAS GOUD"),
            ("23R25A6725", "AKSHAY RAJ"),
            ("23R21A6701", "ANJALI SINGH"),
            ("23R21A6702", "BHARATH KUMAR"),
            ("23R21A6703", "CHANDANA RAO"),
            ("23R21A6704", "DEEPAK REDDY"),
            ("23R21A6705", "ESWARI DEVI"),
            ("23R21A6706", "GANESH PRASAD"),
            ("23R21A6707", "HARITHA CHOWDARY"),
            ("23R21A6708", "INDRAJIT SINGH"),
            ("23R21A6709", "JAGADEESH VARMA"),
            ("23R21A6710", "KAVYA SHREE"),
            ("24R21A6701", "LOKESH BABU"),
            ("24R21A6702", "MADHURI REDDY"),
            ("24R21A6703", "NAVEEN KUMAR"),
            ("24R21A6704", "OOHA CHOWDARY"),
            ("24R21A6705", "PRASANTHI DEVI"),
            ("24R21A6706", "QADIR AHMED"),
            ("24R21A6707", "RAMYA KRISHNA"),
            ("24R21A6708", "SACHIN TEJA"),
            ("24R21A6709", "TANUSHRI PATEL"),
            ("24R21A6710", "UDAY KUMAR"),
            ("24R25A6701", "VARUN REDDY"),
            ("24R25A6702", "WASEEM AKRAM"),
            ("24R25A6703", "XAVIER RAJ"),
            ("24R25A6704", "YADAV SHARMA"),
            ("24R25A6705", "ZAINAB FATIMA"),
            ("24R25A6706", "ANAND RAO"),
            ("24R25A6707", "BINDHU PRIYA"),
            ("24R25A6708", "CHIRANJEEVI GOUD"),
            ("24R25A6709", "DILEEP KUMAR"),
            ("24R25A6710", "EESHA SINGH") ,
            ("24R25A6711", "FARAH KHAN"),
            ("24R25A6712", "GIRISH BABU"),
            ("24R25A6713", "HEMA LATHA"),
            ("24R25A6714", "IQBAL SINGH"),
            ("24R25A6715", "JAYANTHI REDDY"),
            ("24R25A6716", "KARTHIK VADLA"),
            ("24R25A6717", "LALITHA PRIYA"),
            ("24R25A6718", "MANOHAR RAO"),
            ("24R25A6719", "NANDINI DEVI"),
            ("24R25A6720", "OMKAR NATH"),
            ("24R25A6721", "PRANAVI CHOWDARY"),
            ("24R25A6722", "RAJESH KUMAR"),
            ("24R25A6723", "SARANYA SRI"),
            ("24R25A6724", "TARUN TEJA"),
            ("24R25A6725", "UMA MAHESH"),
            ("23R25A6726", "VINAY KUMAR"),
            ("23R25A6727", "SWATHI REDDY"),
            ("23R25A6728", "PREM KUMAR"),
            ("23R25A6729", "SHANTHI PRIYA"),
            ("23R25A6730", "GOPAL KRISHNA"),
            ("23R25A6731", "SINDHUJA RAO"),
            ("23R25A6732", "ARJUN VARMA"),
            ("23R25A6733", "DIVYA BHARATHI"),
            ("23R25A6734", "CHAKRAVARTHY"),
            ("23R25A6735", "MOUNIKA REDDY"),
            ("23R25A6736", "RAMA RAO"),
            ("23R25A6737", "JYOTHI CHOWDARY"),
            ("23R25A6738", "SUDHEER KUMAR"),
            ("23R25A6739", "ANUPAMA SINGH"),
            ("23R25A6740", "BALA KRISHNA"),
            ("23R21A6711", "LAKSHMI DEVI"),
            ("23R21A6712", "MOHAN RAO"),
            ("23R21A6713", "NEHA SHARMA"),
            ("23R21A6714", "PAVAN KUMAR"),
            ("23R21A6715", "RADHIKA GOUD"),
            ("23R21A6716", "SANDEEP REDDY"),
            ("23R21A6717", "TEJASWI CHOWDARY"),
            ("23R21A6718", "VARUN TEJA"),
            ("23R21A6719", "YASHASWINI SINGH"),
            ("23R21A6720", "ZAHIR HUSSAIN"),
            ("23R21A6721", "AKHIL KUMAR"),
            ("23R21A6722", "BHAVANA REDDY"),
            ("23R21A6723", "CHINMAYI RAO"),
            ("23R21A6724", "DEVANSHI SHARMA"),
            ("23R21A6725", "ESHA GUPTA"),
            ("23R21A6726", "GAUTHAM KRISHNA"),
            ("23R21A6727", "HARSHITHA NAIK"),
            ("23R21A6728", "INDRAKSHI DEVI"),
            ("23R21A6729", "JHANSI RANI"),
            ("23R21A6730", "KISHORE KUMAR"),
            ("24R21A6711", "MOHITH REDDY"),
            ("24R21A6712", "NISHA SINGH"),
            ("24R21A6713", "PRASAD GOUD"),
            ("24R21A6714", "RASHMI CHOWDARY"),
            ("24R21A6715", "SAHITHI REDDY"),
            ("24R21A6716", "UDAY BHASKAR"),
            ("24R21A6717", "VANDANA JAIN"),
            ("24R21A6718", "YUKTA BANSAL"),
            ("24R21A6719", "ADITYA VARMA"),
            ("24R21A6720", "BHANU PRAKASH")

    ]

        # Get all branches
        branches = session.query(models.Branch).all()
        if not branches:
            print("No branches found! Run seed_academic_data.py first.")
            return

        for roll_no, name in students_data:
            # Check if student already exists (by roll number)
            existing_student = session.query(models.Student).filter_by(roll_number=roll_no).first()
            if existing_student:
                print(f"Skipping {roll_no} - Already exists")
                continue

            # Create User first (required for Student)
            # Use roll number as email prefix for uniqueness if email not provided
            email = f"{roll_no.lower()}@student.academix.ai"
            
            # Check if user exists
            existing_user = session.query(models.User).filter_by(email=email).first()
            if not existing_user:
                hashed_pw = auth.get_password_hash("password123") # Default password
                new_user = models.User(
                    email=email,
                    hashed_password=hashed_pw,
                    name=name,
                    role="Student",
                    is_active=True
                )
                session.add(new_user)
                session.flush() # Get the ID
                user_id = new_user.id
            else:
                user_id = existing_user.id

            # Randomly assign Branch and Semester (1-8)
            branch = random.choice(branches)
            semester = random.randint(1, 8)
            
            # Create Student
            new_student = models.Student(
                user_id=user_id,
                roll_number=roll_no,
                branch_id=branch.id,
                current_semester=semester,
                year=(semester + 1) // 2 # Approximate year
            )
            session.add(new_student)
            print(f"Added Student: {name} ({roll_no}) -> {branch.code} Sem {semester}")

        session.commit()
        print("Student seeding complete.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error seeding students: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed_students()
