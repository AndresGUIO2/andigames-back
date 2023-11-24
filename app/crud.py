from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import OperationalError
from sqlalchemy import func, desc
from time import sleep
from . import models
from .schemas import UserDetails, UserBase, UserSimple ,UserCreate, UserFollower, UserNicknameUsernameReviews, FollowerDetails, ReviewRead, UserUpdate
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

def get_games_by_similar_title(db: Session, title: str, max_distance: int = 5, limit: int = 10):
    search = title.strip().lower()

    # Simmilar games
    similar_games = db.query(
        models.Game,
        func.levenshtein(func.lower(models.Game.title), search).label('levenshtein_distance')
    ).filter(
        func.levenshtein(func.lower(models.Game.title), search) <= max_distance
    ).limit(limit).all()

    # Calculate developer frequency
    developer_frequency = {}
    for game, _ in similar_games:
        developer_frequency[game.developer] = developer_frequency.get(game.developer, 0) + 1

    # Order by levenshtein distance and developer frequency
    sorted_games = sorted(
        similar_games,
        key=lambda x: (x[1], -developer_frequency[x[0].developer])
    )

    return [game for game, _ in sorted_games]

# Users
# Get one user by nickname
def get_user_no_password(db: Session, nickname: str):
    query =  db.query(models.User).filter(models.User.nickname == nickname).first()
    return query

def get_user_details(db: Session, user_nickname: str) -> UserDetails:
    
    max_retries = 3
    retries = 0
    
    while retries < max_retries:        
        try:
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
        
        except OperationalError:
            retries +=1
            sleep(0.25)
            
    return {"error": "Database error after 3 retries"}

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
    db_user = models.User(nickname=user.nickname, email=user.email, password=user.password, genre=user.genre, about_me=user.about_me, birthdate=user.birthdate, username=user.username)
    db_user.hash_password(user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_data(db: Session, user_nickname: str, user: UserUpdate):
    existing_user = db.query(models.User).filter(models.User.nickname == user_nickname).first()

    if not existing_user:
        return None

    if user.email is not None:
        existing_user.email = user.email
    if user.genre is not None:
        existing_user.genre = user.genre
    if user.about_me is not None:
        existing_user.about_me = user.about_me
    if user.birthdate is not None:
        existing_user.birthdate = user.birthdate
    if user.username is not None:
        existing_user.username = user.username

    db.commit()
    db.refresh(existing_user) 

    return existing_user


def add_follower(db: Session, followerData: UserFollower):
    db_follower = models.User_followers(user_follower_nickname=followerData.user_follower_nickname, user_following_nickname=followerData.user_following_nickname)
    db.add(db_follower)
    db.commit()
    db.refresh(db_follower)
    return db_follower



    