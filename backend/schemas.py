from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    phone: str


class UserLogin(BaseModel):
    email: str
    password: str


class PassCreate(BaseModel):
    user_id: int
    pass_type: str


class TicketCreate(BaseModel):
    user_id: int
    source: str
    destination: str


class PaymentCreate(BaseModel):
    user_id: int
    amount: float