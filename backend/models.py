from decimal import Decimal
from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DECIMAL, TIMESTAMP
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy.sql import func

Base = declarative_base()


# ==========================
# USERS TABLE
# ==========================
class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(15))


# ==========================
# BUS PASSES TABLE
# ==========================
class BusPass(Base):
    __tablename__ = "bus_passes"

    pass_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"))
    pass_type: Mapped[str] = mapped_column(String(50))
    issue_date: Mapped[str] = mapped_column(String(50))
    expiry_date: Mapped[str] = mapped_column(String(50))
    qr_code: Mapped[str] = mapped_column(String(255))
    qr_url: Mapped[str] = mapped_column(String(500))
    pdf_url: Mapped[str] = mapped_column(String(500))


# ==========================
# TICKETS TABLE
# ==========================
class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"))
    source: Mapped[str] = mapped_column(String(100))
    destination: Mapped[str] = mapped_column(String(100))
    fare: Mapped[int] = mapped_column(Integer)
    booking_date: Mapped[str] = mapped_column(String(100))
    qr_code: Mapped[str] = mapped_column(String(255))
    qr_url: Mapped[str] = mapped_column(String(500))
    pdf_url: Mapped[str] = mapped_column(String(500))

# ==========================
# PAYMENTS TABLE
# ==========================
class Payment(Base):
    __tablename__ = "payments"

    payment_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"))
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    payment_status: Mapped[str] = mapped_column(String(20))
    payment_date: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())