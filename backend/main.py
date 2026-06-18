from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import qrcode
import os
from fastapi.responses import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from models import Base, User, BusPass, Ticket, Payment
from passlib.context import CryptContext
from schemas import (
    UserCreate,
    UserLogin,
    PassCreate,
    TicketCreate,
    PaymentCreate
)

from database import SessionLocal, engine
from s3_utils import upload_file
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

app = FastAPI(
    title="Cloud Bus Pass System API"
)


def ensure_database_schema():
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    schema_updates = {
        "bus_passes": {
            "qr_url": "VARCHAR(500) DEFAULT ''",
            "pdf_url": "VARCHAR(500) DEFAULT ''"
        },
        "tickets": {
            "qr_url": "VARCHAR(500) DEFAULT ''",
            "pdf_url": "VARCHAR(500) DEFAULT ''"
        }
    }

    with engine.begin() as connection:
        for table_name, columns in schema_updates.items():
            existing_columns = {
                column["name"]
                for column in inspector.get_columns(table_name)
            }

            for column_name, column_definition in columns.items():
                if column_name not in existing_columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            f"ADD COLUMN {column_name} {column_definition}"
                        )
                    )


@app.on_event("startup")
def startup():
    ensure_database_schema()


def upload_or_local_url(local_file, s3_file, local_url):
    try:
        return upload_file(local_file, s3_file)
    except Exception:
        return local_url


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )

# CORS Configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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

    qr.save(str(path))

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
    password=hash_password(user.password),
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
        User.email == user.email
    ).first()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(
    status_code=401,
    detail="Invalid credentials"
)
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
    request: Request,
    db: Session = Depends(get_db)
):

    latest_payment = db.query(Payment).filter(
        Payment.user_id == pass_data.user_id,
        Payment.payment_status == "SUCCESS"
    ).order_by(
        Payment.payment_id.desc()
    ).first()

    if not latest_payment:
        raise HTTPException(
            status_code=400,
            detail="Please complete payment before generating bus pass"
        )

    issue_date = datetime.now().date()
    if pass_data.pass_type == "daily":
        expiry_date = issue_date + timedelta(days=1)
    elif pass_data.pass_type == "weekly":
        expiry_date = issue_date + timedelta(days=7)
    elif pass_data.pass_type == "monthly":
        expiry_date = issue_date + timedelta(days=30)
    else:
        expiry_date = issue_date + timedelta(days=30)

    new_pass = BusPass(
        user_id=pass_data.user_id,
        pass_type=pass_data.pass_type,
        issue_date=str(issue_date),
        expiry_date=str(expiry_date),
        qr_code="",
        qr_url="",
        pdf_url=""
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

    # Generate PDF using local QR file
    pdf_path = generate_pass_pdf(new_pass)

    qr_url = upload_or_local_url(
        qr_path,
        f"passes/qr/pass_{new_pass.pass_id}.png",
        str(request.url_for("download_pass_qr", pass_id=new_pass.pass_id))
    )

    pdf_url = upload_or_local_url(
        pdf_path,
        f"passes/pdf/pass_{new_pass.pass_id}.pdf",
        str(request.url_for("download_pass", pass_id=new_pass.pass_id))
    )

    new_pass.qr_url = qr_url
    new_pass.pdf_url = pdf_url

    db.commit()
    db.refresh(new_pass)

    return {
        "message": "Bus Pass Applied Successfully",
        "pass_id": new_pass.pass_id,
        "issue_date": str(issue_date),
        "expiry_date": str(expiry_date),
        "qr_url": qr_url,
        "pdf_url": pdf_url
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
            "qr_code": p.qr_code,
            "qr_url": p.qr_url,
            "pdf_url": p.pdf_url
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
FARE_CHART = {
    ("Mumbai", "Pune"): 250,
    ("Pune", "Mumbai"): 250,

    ("Mumbai", "Nashik"): 180,
    ("Nashik", "Mumbai"): 180,

    ("Pune", "Nashik"): 150,
    ("Nashik", "Pune"): 150,

    ("Mumbai", "Thane"): 50,
    ("Thane", "Mumbai"): 50
}


@app.post("/book-ticket")
def book_ticket(
    ticket_data: TicketCreate,
    request: Request,
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

    route = (
        ticket_data.source,
        ticket_data.destination
    )

    fare = FARE_CHART.get(route)

    if fare is None:
        raise HTTPException(
            status_code=400,
            detail="Route not available"
        )

    new_ticket = Ticket(
        user_id=ticket_data.user_id,
        source=ticket_data.source,
        destination=ticket_data.destination,
        fare=fare,
        booking_date=str(datetime.now()),
        qr_code="",
        qr_url="",
        pdf_url=""
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

    # Generate PDF using local QR image
    pdf_path = generate_ticket_pdf(new_ticket)

    qr_url = upload_or_local_url(
        qr_path,
        f"tickets/qr/ticket_{new_ticket.ticket_id}.png",
        str(request.url_for("download_ticket_qr", ticket_id=new_ticket.ticket_id))
    )

    pdf_url = upload_or_local_url(
        pdf_path,
        f"tickets/pdf/ticket_{new_ticket.ticket_id}.pdf",
        str(request.url_for("download_ticket", ticket_id=new_ticket.ticket_id))
    )

    new_ticket.qr_url = qr_url
    new_ticket.pdf_url = pdf_url

    db.commit()
    db.refresh(new_ticket)

    return {
        "message": "Ticket booked successfully",
        "ticket_id": new_ticket.ticket_id,
        "source": new_ticket.source,
        "destination": new_ticket.destination,
        "fare": fare,
        "qr_url": qr_url,
        "pdf_url": pdf_url
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
            "qr_code": t.qr_code,
            "qr_url": t.qr_url,
            "pdf_url": t.pdf_url
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


@app.get("/download-ticket-qr/{ticket_id}", name="download_ticket_qr")
def download_ticket_qr(ticket_id: int):

    qr_path = f"qr_codes/tickets/ticket_{ticket_id}.png"

    if not os.path.exists(qr_path):
        return {
            "message": "QR code not found"
        }

    return FileResponse(
        path=qr_path,
        media_type="image/png",
        filename=f"ticket_{ticket_id}_qr.png"
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


@app.get("/download-pass-qr/{pass_id}", name="download_pass_qr")
def download_pass_qr(pass_id: int):

    qr_path = f"qr_codes/passes/pass_{pass_id}.png"

    if not os.path.exists(qr_path):
        return {
            "message": "QR code not found"
        }

    return FileResponse(
        path=qr_path,
        media_type="image/png",
        filename=f"pass_{pass_id}_qr.png"
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
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
@app.get("/admin/stats")
def admin_stats(db: Session = Depends(get_db)):

    total_users = db.query(User).count()
    total_passes = db.query(BusPass).count()
    total_tickets = db.query(Ticket).count()

    payments = db.query(Payment).all()

    revenue = sum(float(p.amount) for p in payments)

    return {
        "total_users": total_users,
        "total_passes": total_passes,
        "total_tickets": total_tickets,
        "total_revenue": revenue
    }
@app.get("/verify-ticket/{ticket_id}")
def verify_ticket(ticket_id: int, db: Session = Depends(get_db)):
    
    ticket = db.query(Ticket).filter(
        Ticket.ticket_id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    return {
        "ticket_id": ticket.ticket_id,
        "source": ticket.source,
        "destination": ticket.destination,
        "fare": ticket.fare,
        "status": "VALID"
    }
@app.get("/user/{user_id}/passes")
def get_user_passes(user_id: int, db: Session = Depends(get_db)):
    passes = db.query(BusPass).filter(
        BusPass.user_id == user_id
    ).all()

    return passes
@app.get("/user/{user_id}/tickets")
def get_user_tickets(user_id: int, db: Session = Depends(get_db)):
    tickets = db.query(Ticket).filter(
        Ticket.user_id == user_id
    ).all()

    return tickets
