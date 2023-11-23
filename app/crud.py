from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from . import models
from .schemas import UserDetails, UserBase, UserSimple ,UserCreate, UserFollower, UserNicknameUsernameReviews, FollowerDetails, ReviewRead
from .models import User

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
def get_games_by_similar_title(db: Session, title: str, max_distance: int = 5):
    search = title.strip().lower()
    
    return db.query(models.Game).filter(
        func.levenshtein(func.lower(models.Game.title), search) <= max_distance
    ).all()

# Users
# Get one user by nickname
def get_user_no_password(db: Session, nickname: str):
    query =  db.query(models.User).filter(models.User.nickname == nickname).first()
    return query

def get_user_details(db: Session, user_nickname: str) -> UserDetails:
    # Obtener información básica del usuario
    user_data = db.query(models.User).filter(models.User.nickname == user_nickname).first()

    followers_query = db.query(models.User_followers.user_follower_nickname)\
                        .filter(models.User_followers.user_following_nickname == user_nickname).all()
    followers = [follower[0] for follower in followers_query]

    following_query = db.query(models.User_followers.user_following_nickname)\
                        .filter(models.User_followers.user_follower_nickname == user_nickname).all()
    following = [following[0] for following in following_query]

    reviews_query = db.query(models.Review.id).filter(models.Review.user_nickname == user_nickname).all()
    reviews = [review[0] for review in reviews_query]

    wishlist_query = db.query(models.Users_wishlist.game_id).filter(models.Users_wishlist.user_nickname == user_nickname).all()
    wishlist = [wishlist[0] for wishlist in wishlist_query]
    
    user_details = UserDetails(
        nickname=user_data.nickname,
        username=user_data.username,
        about_me=user_data.about_me,
        followers=[UserSimple(nickname=f) for f in followers],
        following=[UserSimple(nickname=f) for f in following],
        reviews=reviews,
        wishlist=wishlist
    )
    return user_details

# Get followers and following with details 
def get_user_followers_and_following(db: Session, user_nickname: str) -> FollowerDetails:

    followers_query = db.query(
        models.User_followers.user_follower_nickname, 
        models.User.nickname, 
        models.User.username,
        models.Review.game_id
    ).join(models.User, models.User.nickname == models.User_followers.user_follower_nickname)\
    .outerjoin(models.Review, models.User_followers.user_follower_nickname == models.Review.user_nickname)\
    .filter(models.User_followers.user_following_nickname == user_nickname)\
    .all()

    following_query = db.query(
        models.User_followers.user_following_nickname, 
        models.User.nickname, 
        models.User.username,
        models.Review.game_id
    ).join(models.User, models.User.nickname == models.User_followers.user_following_nickname)\
    .outerjoin(models.Review, models.User_followers.user_following_nickname == models.Review.user_nickname)\
    .filter(models.User_followers.user_follower_nickname == user_nickname)\
    .all()
    
    followers = {}
    following = {}

    for follower_nickname, nickname, username, review_game_id in followers_query:
        if follower_nickname not in followers:
            followers[follower_nickname] = {
                "nickname": nickname,
                "username": username,
                "reviews": []
            }
        if review_game_id:
            followers[follower_nickname]["reviews"].append(review_game_id)

    for following_nickname, nickname, username, review_game_id in following_query:
        if following_nickname not in following:
            following[following_nickname] = {
                "nickname": nickname,
                "username": username,
                "reviews": []
            }
        if review_game_id:
            following[following_nickname]["reviews"].append(review_game_id)

    followers_list = [UserNicknameUsernameReviews(nickname=follower_nickname, username=follower["username"], reviews=[ReviewRead(game_id=review) for review in follower["reviews"]]) for follower_nickname, follower in followers.items()]
    following_list = [UserNicknameUsernameReviews(nickname=following_nickname, username=following["username"], reviews=[ReviewRead(game_id=review) for review in following["reviews"]]) for following_nickname, following in following.items()]
    
    return FollowerDetails(followers=followers_list, following=following_list)
    
# Add user to database
def add_user(db: Session, user: UserCreate):
    user.hash_password(user.password)
    
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



    