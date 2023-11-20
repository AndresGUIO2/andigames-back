from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from .database import SessionLocal

# Get the database session 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
