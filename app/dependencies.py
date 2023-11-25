from .database import SessionLocal
from .database import AsyncSessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
