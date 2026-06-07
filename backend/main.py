from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from schemas import UserCreate, UserLogin

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

@app.get("/")
def home():
    return {
        "message": "Backend Running"
    }

@app.post("/register")
def register(user: UserCreate):
    return {
        "message": "User registered successfully",
        "name": user.name,
        "email": user.email
    }

@app.post("/login")
def login(user: UserLogin):
    return {
        "message": "Login successful",
        "email": user.email,
        "access_token": "dummy_token_123"
    }