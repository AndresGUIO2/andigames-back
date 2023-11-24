from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.crud import get_game, get_game_by_title_exact, get_games_by_similar_title
from ...schemas import GameRead, GameCreate, GameUpdate, GameDetails
from ...dependencies import get_db

router = APIRouter()

#Get one game by id
@router.get("/{game_id}", response_model=GameRead, tags=["Games"])
def read_game(game_id: int, db: Session = Depends(get_db)):
    db_game = get_game(db, game_id=game_id)
    if db_game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return db_game

#Get one game by title
@router.get("/title/{title}", response_model=GameRead, tags=["Games"])
def read_game_by_title(title: str, db: Session = Depends(get_db)):
    db_game = get_game_by_title_exact(db, title=title)
    if db_game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return db_game

#Get games by similar title
@router.get("/games/search/{title}", response_model=List[GameRead], tags=["Games"])
def read_games_by_title(title: str, limit: int = Query(10, alias="limit"), db: Session = Depends(get_db)):
    db_games = get_games_by_similar_title(db, title=title, limit=limit)
    return db_games

