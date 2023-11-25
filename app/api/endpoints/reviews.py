from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ...crud import add_review_by_nickname
from ...schemas import ReviewCreate
from ...dependencies import get_async_db

router = APIRouter()

@router.post("/reviews/add/{nickname}/")
async def read_reviews(nickname:str, review: ReviewCreate, db: AsyncSession = Depends(get_async_db)):
    db_review = await add_review_by_nickname(db, user_nickname=nickname, review=review)
    if db_review is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_review 
