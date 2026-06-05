from fastapi import FastAPI
from schemas import UserCreate, UserLogin

app = FastAPI(
    title="Cloud Bus Pass System API"
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
        "email": user.email
    }