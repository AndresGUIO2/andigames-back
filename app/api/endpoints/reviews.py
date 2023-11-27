from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ...crud import add_review_by_nickname, get_user_reviews, delete_review, get_user_review
from ...schemas import ReviewCreate
from ...dependencies import get_async_db
from ...models import User
from...api.auth import get_current_user

router = APIRouter()

@router.post("/reviews/add/{nickname}/",
            summary="Añadir una reseña a un usuario",
            description="Esta ruta permite añadir una reseña a un usuario.",
            response_description="Retorna la reseña añadida",
            tags=["Reviews"]
            )
async def read_reviews(nickname:str, review: ReviewCreate, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    if current_user.nickname != nickname:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    db_review = await add_review_by_nickname(db, user_nickname=nickname, review=review)
    if db_review is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_review 


@router.get("/reviews/{nickname}/",
            summary="Obtener las reseñas de un usuario",
            description="Esta ruta te permite obtener las reseñas de un usuario.",
            response_description="Retorna las reseñas de un usuario específico",
            tags=["Reviews"]    
            )
async def read_reviews(nickname:str, db: AsyncSession = Depends(get_async_db)):
    db_reviews = await get_user_reviews(db, user_nickname=nickname)
    if db_reviews is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_reviews


@router.get("/reviews/{nickname}/{id}",
            summary="Obtener una reseña de un usuario",
            description="Esta ruta te permite obtener una reseña de un usuario.",
            response_description="Retorna una reseña de un usuario específico",
            tags=["Reviews"]    
            )
async def read_reviews(id:int, nickname:str, db: AsyncSession = Depends(get_async_db)):
    db_review = await get_user_review(db, user_nickname=nickname, game_id=id)
    if db_review is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_review


@router.delete("/reviews/{nickname}/{id}/delete",
               summary="Eliminar una reseña de un usuario",
                description="Esta ruta permite eliminar una reseña de un usuario.",
                response_description="Retorna la reseña eliminada",
                tags=["Reviews"]
               )
async def delete_review_by_game_id_and_review(id:int, nickname:str, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    if current_user.nickname != nickname:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    review_deleted = await delete_review(db, user_nickname=nickname, game_id=id)
    if not review_deleted:
        raise HTTPException(status_code=404, detail="Review not found")

    return {"detail": "Review deleted successfully"}



@router.put("/reviews/{nickname}/{id}/update",
            summary="Actualizar una reseña de un usuario",
            description="Esta ruta permite actualizar una reseña de un usuario.",
            response_description="Retorna la reseña actualizada",
            tags=["Reviews"]
            )
async def update_review(id:int, nickname:str, review: ReviewCreate, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    if current_user.nickname != nickname:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    db_review = await update_review(db, user_nickname=nickname, review_id=id, review=review)
    if db_review is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_review