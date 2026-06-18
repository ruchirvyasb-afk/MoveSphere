from database import engine
from models import Base

print("Database URL:", engine.url)

Base.metadata.create_all(bind=engine)

print("Tables created successfully")

print(engine.url)