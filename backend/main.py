from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import qrcode
import os

from schemas import (
    UserCreate,
    UserLogin,
    PassCreate,
    TicketCreate
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

    return {
        "message": "Bus Pass Applied Successfully",
        "pass_id": new_pass.pass_id,
        "issue_date": str(issue_date),
        "expiry_date": str(expiry_date),
        "qr_code": qr_path
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

    return {
        "message": "Ticket booked successfully",
        "ticket_id": new_ticket.ticket_id,
        "fare": fare,
        "qr_code": qr_path
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