from sqlalchemy.orm import Session, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import asyncio
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

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from . import models

async def get_games_by_similar_title(db: AsyncSession, title: str, max_distance: int = 30, limit: int = 10):
    search_words = title.strip().lower().split()
 
    stmt = select(models.Game)

    # Filter by keyword presence using ILIKE
    for word in search_words:
        stmt = stmt.filter(models.Game.title.ilike(f"%{word}%"))

    # Calculate Levenshtein distance for each word and sum them
    levenshtein_sum = sum(
        func.levenshtein(func.lower(models.Game.title), word) for word in search_words
    )

    stmt = stmt.add_columns(
        levenshtein_sum.label('total_levenshtein_distance')
    ).group_by(models.Game.id)

    # Apply having clause to filter games based on cumulative Levenshtein distance
    stmt = stmt.having(levenshtein_sum <= max_distance * len(search_words))

    # Order by the cumulative Levenshtein distance
    stmt = stmt.order_by('total_levenshtein_distance').limit(limit)

    # Execute the query asynchronously
    result =  await db.execute(stmt)
    games_with_distances = result.all()

    # Calculate developer frequency
    developer_frequency = {}
    for game_with_distances in games_with_distances:
        game = game_with_distances[0]
        developer_frequency[game.developer] = developer_frequency.get(game.developer, 0) + 1

    # Order by the cumulative Levenshtein distance and developer frequency
    sorted_games = sorted(
        games_with_distances,
        key=lambda game_tuple: (
            game_tuple[-1],  # Cumulative Levenshtein distance
            -developer_frequency[game_tuple[0].developer]  # Developer frequency
        )
    )

    # Return only the Game objects from the sorted list
    return [game_tuple[0] for game_tuple in sorted_games]


# Users
# Get one user by nickname
async def get_user_no_password(db: AsyncSession, nickname: str):
    query = select(models.User).where(models.User.nickname == nickname)
    result = await db.execute(query)
    user = result.scalars().first()
    print(user)
    return user


async def get_user_details(db: AsyncSession, user_nickname: str) -> UserDetails:
    
    max_retries = 3
    retries = 0
    
    while retries < max_retries:        
        try:
            
            async with db.begin():
                # get user date
                user_query = select(models.User).filter(models.User.nickname == user_nickname)
                user_result = await db.execute(user_query)
                user_data = user_result.scalar_one_or_none()
                
                # Get followers for user data
                followers_query = select(models.User_followers.user_follower_nickname)\
                                    .filter(models.User_followers.user_following_nickname == user_nickname)
                followers_result = await db.execute(followers_query)
                followers = [follower[0] for follower in followers_result.scalars().all()]
                
                # get following for user data
                following_query = select(models.User_followers.user_following_nickname)\
                                    .filter(models.User_followers.user_follower_nickname == user_nickname)
                following_result = await db.execute(following_query)
                following = [following[0] for following in following_result.scalars().all()]

                # Get user reviews
                reviews_query = select(models.Review.id).filter(models.Review.user_nickname == user_nickname)
                reviews_result = await db.execute(reviews_query)
                reviews = [review[0] for review in reviews_result.scalars().all()]

                # get user wishlist
                wishlist_query = select(models.Users_wishlist.game_id)\
                                    .filter(models.Users_wishlist.user_nickname == user_nickname)
                wishlist_result = await db.execute(wishlist_query)
                wishlist = [wishlist[0] for wishlist in wishlist_result.scalars().all()]
                
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
            retries += 1
            await asyncio.sleep(0.25)
            
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



    