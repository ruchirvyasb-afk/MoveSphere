from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DECIMAL,
    TIMESTAMP
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# ==========================
# USERS TABLE
# ==========================
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100))
    password = Column(String(255))
    phone = Column(String(15))


# ==========================
# BUS PASSES TABLE
# ==========================
class BusPass(Base):
    __tablename__ = "bus_passes"

    pass_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.user_id")
    )

    pass_type = Column(String(50))
    issue_date = Column(String(50))
    expiry_date = Column(String(50))
    qr_code = Column(String(255))


# ==========================
# TICKETS TABLE
# ==========================
class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.user_id")
    )

    source = Column(String(100))
    destination = Column(String(100))
    fare = Column(Integer)
    booking_date = Column(String(100))
    qr_code = Column(String(255))


# ==========================
# PAYMENTS TABLE
# ==========================
class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id")
    )

    amount = Column(
        DECIMAL(10, 2)
    )

    payment_status = Column(
        String(20)
    )

    payment_date = Column(
        TIMESTAMP,
        server_default=func.now()
    )