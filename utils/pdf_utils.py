import PyPDF2
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import base64

def extract_text_from_pdf(filepath):
    """
    Extracts text from a PDF file using PyPDF2.
    """
    try:
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def generate_hall_ticket_buffer(
    student_name, roll_number, course_name, exam_title,
    exam_date, exam_time, room_name, seat_name, qr_base64, exam_type
):
    """
    Generates a visual Hall Ticket PDF in memory.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # --- Header ---
    c.setFont("Helvetica-Bold", 24)
    # Shifted down to avoid overlapping the border (Top is height-40)
    c.drawCentredString(width / 2, height - 80, "MLR Institute of Technology")
    
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 105, "Autonomous Integration | NAAC 'A' Grade")
    
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 140, f"{exam_type} EXAMINATION HALL TICKET")
    
    # Draw simple border
    c.setStrokeColor(colors.black)
    c.rect(40, 40, width - 80, height - 80)
    
    # --- Student Details ---
    y_pos = height - 200 # Shifted body start down
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, y_pos, "Candidate Details:")
    
    c.setFont("Helvetica", 12)
    y_pos -= 25
    c.drawString(60, y_pos, f"Name: {student_name}")
    y_pos -= 20
    c.drawString(60, y_pos, f"Roll Number: {roll_number}")
    y_pos -= 20
    c.drawString(60, y_pos, f"Program: {course_name}")

    # --- Exam Details ---
    y_pos -= 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, y_pos, "Examination Details:")
    
    c.setFont("Helvetica", 12)
    y_pos -= 25
    c.drawString(60, y_pos, f"Exam: {exam_title}")
    y_pos -= 20
    c.drawString(60, y_pos, f"Date: {exam_date}")
    y_pos -= 20
    c.drawString(60, y_pos, f"Time: {exam_time}")
    
    # --- Seating Details (Highlighted) ---
    y_pos -= 50
    c.setFillColor(colors.cyan) # Background highlight
    c.rect(55, y_pos - 60, 400, 80, fill=1, stroke=0) # Widened and taller
    c.setFillColor(colors.black)
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(70, y_pos, "Seating Allocation:")
    
    c.setFont("Helvetica-Bold", 16)
    y_pos -= 35
    c.drawString(80, y_pos, f"Room: {room_name}")
    c.drawString(280, y_pos, f"Seat: {seat_name}") # Shifted Seat significantly to the right
    
    # --- QR Code ---
    # Convert base64 to image
    try:
        if qr_base64:
            # Remove data URL prefix if present
            if "base64," in qr_base64:
                qr_base64 = qr_base64.split("base64,")[1]
            
            qr_data = base64.b64decode(qr_base64)
            qr_image = ImageReader(BytesIO(qr_data))
            
            # Draw QR at bottom right
            c.drawImage(qr_image, width - 200, height - 350, width=150, height=150)
            c.setFont("Helvetica", 10)
            c.drawCentredString(width - 125, height - 365, "Scan to Verify")
    except Exception as e:
        print(f"QR Error: {e}")
        c.drawString(width - 200, height - 300, "[QR Code Error]")

    # --- Instructions ---
    y_pos = 150
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, y_pos, "Instructions:")
    c.setFont("Helvetica", 10)
    y_pos -= 15
    instructions = [
        "1. Candidates must carry this Hall Ticket and ID Card.",
        "2. Report to the exam hall 15 minutes before scheduled time.",
        "3. Electronic gadgets are strictly prohibited.",
        "4. Keep this ticket safe for future reference."
    ]
    for line in instructions:
        c.drawString(60, y_pos, line)
        y_pos -= 15

    c.save()
    buffer.seek(0)
    return buffer
