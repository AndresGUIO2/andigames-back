from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas

# Get one game by id
def get_game(db: Session, game_id: int):
    return db.query(models.Game).filter(models.Game.id == game_id).first()

# def create_game(db: Session, game:schemas.GameCreate):
#     db_game = models.Game(title = game.tittle, genre = game.genre, url = game.url, release_date = game.release_date, 
#                           primary_genre = game.primary_genre, genres = game.genres, steam_rating = game.steam_rating, 
#                           platform_rating = game.platform_rating, publisher = game.publisher, 
#                           detected_technologies = game.detected_technologies, developer = game.developer)
#     db.add(db_game)
#     db.commit()
#     db.refresh(db_game)
#     return db_game

# Get one game by title
def get_game_by_title_exact(db: Session, title: str):
    return db.query(models.Game).filter(models.Game.title == title).first()

# Normalize title
def normalize_title(title: str):
    title = title.translate(str.maketrans('', '', 'string.punctuation'))
    return title

# Get simmilar normalized titles
def get_games_by_similar_title(db: Session, title: str):
    search = f"%{title.strip().lower()}%"
    return db.query(models.Game).filter(
        models.Game.title.ilike(search)
    ).all()

