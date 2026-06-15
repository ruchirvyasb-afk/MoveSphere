from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import qrcode
import os
from fastapi.responses import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from models import User, BusPass, Ticket, Payment
from schemas import (
    UserCreate,
    UserLogin,
    PassCreate,
    TicketCreate,
    PaymentCreate
)

from database import SessionLocal
from models import User, BusPass, Ticket

app = FastAPI(
    title="Cloud Bus Pass System API"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# QR Code Generator
def generate_qr(data, folder, filename):
    os.makedirs(folder, exist_ok=True)

    qr = qrcode.make(data)

    path = f"{folder}/{filename}.png"

    qr.save(path)

    return path
# PDF Generator for Bus Pass
def generate_pass_pdf(bus_pass):

    os.makedirs("pdfs/passes", exist_ok=True)

    pdf_path = f"pdfs/passes/pass_{bus_pass.pass_id}.pdf"

    c = canvas.Canvas(pdf_path)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(200, 800, "BUS PASS")

    c.setFont("Helvetica", 12)

    c.drawString(100, 740, f"Pass ID: {bus_pass.pass_id}")
    c.drawString(100, 710, f"User ID: {bus_pass.user_id}")
    c.drawString(100, 680, f"Pass Type: {bus_pass.pass_type}")
    c.drawString(100, 650, f"Issue Date: {bus_pass.issue_date}")
    c.drawString(100, 620, f"Expiry Date: {bus_pass.expiry_date}")

    if os.path.exists(bus_pass.qr_code):
        qr_img = ImageReader(bus_pass.qr_code)
        c.drawImage(qr_img, 350, 580, width=150, height=150)

    c.save()

    return pdf_path


# PDF Generator for Ticket
def generate_ticket_pdf(ticket):

    os.makedirs("pdfs/tickets", exist_ok=True)

    pdf_path = f"pdfs/tickets/ticket_{ticket.ticket_id}.pdf"

    c = canvas.Canvas(pdf_path)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(200, 800, "BUS TICKET")

    c.setFont("Helvetica", 12)

    c.drawString(100, 740, f"Ticket ID: {ticket.ticket_id}")
    c.drawString(100, 710, f"User ID: {ticket.user_id}")
    c.drawString(100, 680, f"Source: {ticket.source}")
    c.drawString(100, 650, f"Destination: {ticket.destination}")
    c.drawString(100, 620, f"Fare: ₹{ticket.fare}")

    if os.path.exists(ticket.qr_code):
        qr_img = ImageReader(ticket.qr_code)
        c.drawImage(qr_img, 350, 580, width=150, height=150)

    c.save()

    return pdf_path


@app.get("/")
def home():
    return {
        "message": "Backend Running"
    }


# ==========================
# REGISTER USER
# ==========================
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:
        return {
            "message": "Email already registered"
        }

    new_user = User(
        name=user.name,
        email=user.email,
        password=user.password,
        phone=user.phone
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": new_user.user_id
    }


# ==========================
# LOGIN USER
# ==========================
@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):

    db_user = db.query(User).filter(
        User.email == user.email,
        User.password == user.password
    ).first()

    if not db_user:
        return {
            "message": "Invalid credentials"
        }

    return {
        "message": "Login successful",
        "user_id": db_user.user_id,
        "name": db_user.name
    }


# ==========================
# APPLY BUS PASS
# ==========================
@app.post("/apply-pass")
def apply_pass(
    pass_data: PassCreate,
    db: Session = Depends(get_db)
):

    issue_date = datetime.now().date()
    expiry_date = issue_date + timedelta(days=30)

    new_pass = BusPass(
        user_id=pass_data.user_id,
        pass_type=pass_data.pass_type,
        issue_date=str(issue_date),
        expiry_date=str(expiry_date),
        qr_code=""
    )

    db.add(new_pass)
    db.commit()
    db.refresh(new_pass)

    qr_data = f"""
Pass ID: {new_pass.pass_id}
User ID: {new_pass.user_id}
Pass Type: {new_pass.pass_type}
Issue Date: {new_pass.issue_date}
Expiry Date: {new_pass.expiry_date}
"""

    qr_path = generate_qr(
        qr_data,
        "qr_codes/passes",
        f"pass_{new_pass.pass_id}"
    )

    new_pass.qr_code = qr_path

    db.commit()
    db.refresh(new_pass)
    pdf_path = generate_pass_pdf(new_pass)
    return {
    "message": "Bus Pass Applied Successfully",
    "pass_id": new_pass.pass_id,
    "issue_date": str(issue_date),
    "expiry_date": str(expiry_date),
    "qr_code": qr_path,
    "pdf": pdf_path
}

# ==========================
# VIEW ALL PASSES
# ==========================
@app.get("/passes")
def get_passes(db: Session = Depends(get_db)):

    passes = db.query(BusPass).all()

    result = []

    for p in passes:
        result.append({
            "pass_id": p.pass_id,
            "user_id": p.user_id,
            "pass_type": p.pass_type,
            "issue_date": p.issue_date,
            "expiry_date": p.expiry_date,
            "qr_code": p.qr_code
        })

    return result


# ==========================
# VERIFY PASS
# ==========================
@app.get("/verify-pass/{pass_id}")
def verify_pass(pass_id: int, db: Session = Depends(get_db)):

    bus_pass = db.query(BusPass).filter(
        BusPass.pass_id == pass_id
    ).first()

    if not bus_pass:
        return {
            "valid": False,
            "message": "Pass not found"
        }

    return {
        "valid": True,
        "pass_id": bus_pass.pass_id,
        "user_id": bus_pass.user_id,
        "pass_type": bus_pass.pass_type,
        "issue_date": bus_pass.issue_date,
        "expiry_date": bus_pass.expiry_date
    }


# ==========================
# BOOK TICKET
# ==========================
@app.post("/book-ticket")
def book_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db)
):
    latest_payment = db.query(Payment).filter(
        Payment.user_id == ticket_data.user_id,
        Payment.payment_status == "SUCCESS"
    ).order_by(
        Payment.payment_id.desc()
    ).first()

    if not latest_payment:
        raise HTTPException(
            status_code=400,
            detail="Please complete payment before booking ticket"
        )

    fare = 250

    new_ticket = Ticket(
        user_id=ticket_data.user_id,
        source=ticket_data.source,
        destination=ticket_data.destination,
        fare=fare,
        booking_date=str(datetime.now()),
        qr_code=""
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    qr_data = f"""
Ticket ID: {new_ticket.ticket_id}
User ID: {new_ticket.user_id}
Source: {new_ticket.source}
Destination: {new_ticket.destination}
Fare: {new_ticket.fare}
"""

    qr_path = generate_qr(
        qr_data,
        "qr_codes/tickets",
        f"ticket_{new_ticket.ticket_id}"
    )

    new_ticket.qr_code = qr_path

    db.commit()
    db.refresh(new_ticket)
    pdf_path = generate_ticket_pdf(new_ticket)
    return {
    "message": "Ticket booked successfully",
    "ticket_id": new_ticket.ticket_id,
    "fare": fare,
    "qr_code": qr_path,
    "pdf": pdf_path
}


# ==========================
# VIEW ALL TICKETS
# ==========================
@app.get("/tickets")
def get_tickets(db: Session = Depends(get_db)):

    tickets = db.query(Ticket).all()

    result = []

    for t in tickets:
        result.append({
            "ticket_id": t.ticket_id,
            "user_id": t.user_id,
            "source": t.source,
            "destination": t.destination,
            "fare": t.fare,
            "booking_date": t.booking_date,
            "qr_code": t.qr_code
        })

    return result


# ==========================
# VIEW SINGLE USER
# ==========================
@app.get("/user/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.user_id == user_id
    ).first()

    if not user:
        return {
            "message": "User not found"
        }

    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone
    }
    # ==========================
# DOWNLOAD TICKET PDF
# ==========================
@app.get("/download-ticket/{ticket_id}")
def download_ticket(ticket_id: int):

    pdf_path = f"pdfs/tickets/ticket_{ticket_id}.pdf"

    if not os.path.exists(pdf_path):
        return {
            "message": "PDF not found"
        }

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"ticket_{ticket_id}.pdf"
    )
    # ==========================
# DOWNLOAD PASS PDF
# ==========================
@app.get("/download-pass/{pass_id}")
def download_pass(pass_id: int):

    pdf_path = f"pdfs/passes/pass_{pass_id}.pdf"

    if not os.path.exists(pdf_path):
        return {
            "message": "PDF not found"
        }

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"pass_{pass_id}.pdf"
    )
@app.post("/make-payment")
def make_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db)
    ):

    user = db.query(User).filter(
        User.user_id == payment.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    new_payment = Payment(
        user_id=payment.user_id,
        amount=payment.amount,
        payment_status="SUCCESS"
    )

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    return {
        "message": "Payment Successful",
        "payment_id": new_payment.payment_id,
        "amount": float(new_payment.amount),
        "status": new_payment.payment_status
    }
@app.get("/payments")
def get_payments(db: Session = Depends(get_db)):

    payments = db.query(Payment).all()

    return [
        {
            "payment_id": p.payment_id,
            "user_id": p.user_id,
            "amount": float(p.amount),
            "status": p.payment_status,
            "payment_date": p.payment_date
        }
        for p in payments
    ]
@app.get("/admin/payments")
def admin_payments(db: Session = Depends(get_db)):

    payments = db.query(Payment).all()

    return [
        {
            "payment_id": p.payment_id,
            "user_id": p.user_id,
            "amount": float(p.amount),
            "status": p.payment_status,
            "payment_date": p.payment_date
        }
        for p in payments
    ]