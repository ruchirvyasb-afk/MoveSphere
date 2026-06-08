from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100))
    password = Column(String(255))
    phone = Column(String(15))


class BusPass(Base):
    __tablename__ = "bus_passes"

    pass_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    pass_type = Column(String(50))
    issue_date = Column(String(50))
    expiry_date = Column(String(50))
    qr_code = Column(String(255))


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    source = Column(String(100))
    destination = Column(String(100))
    fare = Column(Integer)
    booking_date = Column(String(100))
    qr_code = Column(String(255))