from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models
from .schemas import UserDetails, UserBase, UserSimple, UserCreate, UserFollower

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

# Get simmilar titles
def get_games_by_similar_title(db: Session, title: str):
    search = f"%{title.strip().lower()}%"
    return db.query(models.Game).filter(
        models.Game.title.ilike(search)
    ).all()

# Users
# Get one user by nickname
def get_user_no_password(db: Session, nickname: str):
    query = db.query(models.User).filter(models.User.nickname == nickname).first()
    return query

# Get user details
def get_user_details(db: Session, user_nickname: str) -> UserDetails:
    # queries
    followers_query = db.query(models.User_followers).filter(models.User_followers.user_following_nickname == user_nickname).all()
    following_query = db.query(models.User_followers).filter(models.User_followers.user_follower_nickname == user_nickname).all()
    reviews_query = db.query(models.Review.game_id).filter(models.Review.user_nickname == user_nickname).all()
    wishlist_query = db.query(models.Users_wishlist.game_id).filter(models.Users_wishlist.user_nickname == user_nickname).all()

    # 
    followers = [UserSimple(nickname=f.user_follower_nickname) for f in followers_query]
    following = [UserSimple(nickname=f.user_following_nickname) for f in following_query]
    reviews = [review.game_id for review in reviews_query]
    wishlist = [wish.game_id for wish in wishlist_query]

    # Create user details
    user_details = UserDetails(
        followers=followers,
        following=following,
        reviews=reviews,
        wishlist=wishlist
    )
    
    return user_details

# Get user details user included
def get_user_details(db: Session, user_nickname: str) -> UserDetails:
    # queries
    user_query = db.query(models.User).filter(models.User.nickname == user_nickname).first()
    followers_query = db.query(models.User_followers).filter(models.User_followers.user_following_nickname == user_nickname).all()
    following_query = db.query(models.User_followers).filter(models.User_followers.user_follower_nickname == user_nickname).all()
    reviews_query = db.query(models.Review.game_id).filter(models.Review.user_nickname == user_nickname).all()
    wishlist_query = db.query(models.Users_wishlist.game_id).filter(models.Users_wishlist.user_nickname == user_nickname).all()

    # 
    nickname = user_query.nickname
    username = user_query.username
    about_me = user_query.about_me
    followers = [UserSimple(nickname=f.user_follower_nickname) for f in followers_query]
    following = [UserSimple(nickname=f.user_following_nickname) for f in following_query]
    reviews = [review.game_id for review in reviews_query]
    wishlist = [wish.game_id for wish in wishlist_query]

    # Create user details
    user_details = UserDetails(
        nickname=nickname,
        username=username,
        about_me=about_me,
        followers=followers,
        following=following,
        reviews=reviews,
        wishlist=wishlist
    )
    
    return user_details

# Add user to database
def add_user(db: Session, user: UserCreate):
    db_user = models.User(nickname=user.nickname, email=user.email, password=user.password, genre=user.genre, about_me=user.about_me, birthdate=user.birthdate, username=user.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Add follower to a user in database
def add_follower(db: Session, followerData: UserFollower):
    db_follower = models.User_followers(user_follower_nickname=followerData.user_follower_nickname, user_following_nickname=followerData.user_following_nickname)
    db.add(db_follower)
    db.commit()
    db.refresh(db_follower)
    return db_follower

    