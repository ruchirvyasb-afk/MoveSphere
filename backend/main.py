from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from schemas import UserCreate, UserLogin, PassCreate
from database import SessionLocal
from models import User, BusPass

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
        qr_code="QR_PENDING"
    )

    db.add(new_pass)
    db.commit()
    db.refresh(new_pass)

    return {
        "message": "Bus Pass Applied Successfully",
        "pass_id": new_pass.pass_id,
        "issue_date": str(issue_date),
        "expiry_date": str(expiry_date)
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