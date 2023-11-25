from sqlalchemy.orm import Session, aliased
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import asyncio
from sqlalchemy.exc import OperationalError
from sqlalchemy import func, desc
from time import sleep
from . import models
from .schemas import UserDetails, UserSimple ,UserCreate, UserFollower, UserNicknameUsernameReviews, FollowerDetails, ReviewRead, UserUpdate, GamePrediction, ReviewCreate
import numpy as np
from typing import List

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

async def get_games_by_similar_title(db: AsyncSession, title: str, max_distance: int = 40, limit: int = 10):
    search_words = title.strip().lower().split()

    stmt = select(models.Game)

    # Filter by keyword presence using ILIKE
    for word in search_words:
        stmt = stmt.filter(models.Game.title.ilike(f"%{word}%"))

    # Calculate Levenshtein distance for each word and sum them
    levenshtein_sum = sum(
        func.levenshtein(func.lower(models.Game.title), word) for word in search_words
    )

    # Add the sum as a column to the query
    stmt = stmt.add_columns(
        levenshtein_sum.label('total_levenshtein_distance')
    ).group_by(models.Game.id)

    # Apply having clause to filter games based on cumulative Levenshtein distance
    stmt = stmt.having(levenshtein_sum <= max_distance * len(search_words))

    # Order by the cumulative Levenshtein distance
    stmt = stmt.order_by('total_levenshtein_distance').limit(limit)

    # Execute the query asynchronously
    result = await db.execute(stmt)
    games_with_distances = result.all()

    # Calculate developer frequency
    developer_frequency = {}
    for game_with_distances in games_with_distances:
        game = game_with_distances[0]
        developer_frequency[game.developer] = developer_frequency.get(game.developer, 0) + 1

    # Order primarily by developer frequency, and secondarily by the cumulative Levenshtein distance
    sorted_games = sorted(
        games_with_distances,
        key=lambda game_tuple: (
            -developer_frequency[game_tuple[0].developer],  # Negative for descending order
            game_tuple[-1]  # Cumulative Levenshtein distance
        )
    )

    # Return only the Game objects from the sorted list
    return [game_tuple[0] for game_tuple in sorted_games]


async def get_games_prediction(db: AsyncSession, title: str, max_distance: int = 40, limit: int = 50):
    search_words = title.strip().lower().split()

    # Parte 1: Encontrar títulos de juegos similares
    stmt = select(models.Game.title)

    for word in search_words:
        stmt = stmt.filter(models.Game.title.ilike(f"%{word}%"))

    levenshtein_sum = sum(
        func.levenshtein(func.lower(models.Game.title), word) for word in search_words
    )

    stmt = stmt.add_columns(
        levenshtein_sum.label('total_levenshtein_distance')
    ).group_by(models.Game.title)

    stmt = stmt.having(levenshtein_sum <= max_distance * len(search_words))
    stmt = stmt.order_by('total_levenshtein_distance').limit(limit)

    result = await db.execute(stmt)
    titles = result.scalars().all()

    # Parte 2: Obtener detalles de estos juegos
    games_details_stmt = select(
        models.Game.title,
        models.Game.primary_genre,
        models.Game.genres,
        models.Game.steam_rating,
        models.Game.platform_rating,
        models.Game.publisher,
        models.Game.detected_technologies,
        models.Game.developer,
        models.Award.name.label('award_names')
    ).outerjoin(models.Game_awards, models.Game.id == models.Game_awards.game_id
    ).outerjoin(models.Award, models.Game_awards.award_id == models.Award.id
    ).where(models.Game.title.in_(titles))

    detail_result = await db.execute(games_details_stmt)
    detail_rows = detail_result.all()

    games_temp = {}
    for row in detail_rows:
        if row.title not in games_temp:
            games_temp[row.title] = {
                'title': row.title,
                'primary_genre': row.primary_genre,
                'genres': row.genres,
                'steam_rating': row.steam_rating,
                'platform_rating': row.platform_rating,
                'publisher': row.publisher,
                'detected_technologies': row.detected_technologies,
                'developer': row.developer,
                'award_names': set()
            }
        if row.award_names:
            games_temp[row.title]['award_names'].add(row.award_names)

    games_predictions = [GamePrediction(**game) for game in games_temp.values()]

    return games_predictions



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
                reviews = [review for review in reviews_result.scalars().all()]

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

# Add follower to database
def add_follower(db: Session, followerData: UserFollower):
    db_follower = models.User_followers(user_follower_nickname=followerData.user_follower_nickname, user_following_nickname=followerData.user_following_nickname)
    db.add(db_follower)
    db.commit()
    db.refresh(db_follower)
    return db_follower

async def add_review_by_nickname(db: AsyncSession, review: ReviewCreate, user_nickname: str):
    db_review = models.Review(game_id=review.game_id, user_nickname=user_nickname, review_date=review.review_date, rating=review.rating, commentary=review.commentary)
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    return db_review

#tests
async def get_user_reviews_games(db: AsyncSession, user_nickname: str):

    GameAlias = aliased(models.Game)
    AwardsAlias = aliased(models.Award)

    query = (
        select(
            GameAlias.title,
            GameAlias.primary_genre,
            GameAlias.genres,
            GameAlias.steam_rating,
            GameAlias.platform_rating,
            GameAlias.publisher,
            GameAlias.detected_technologies,
            GameAlias.developer,
            AwardsAlias.name.label('award_names')
        )
        .join(models.Review, models.Review.game_id == GameAlias.id)  # Unir Review con Game
        .outerjoin(models.Game_awards, GameAlias.id == models.Game_awards.game_id)  # Unir Game_awards con Game
        .outerjoin(AwardsAlias, models.Game_awards.award_id == AwardsAlias.id)  # Unir Awards con Game_awards
        .filter(models.Review.user_nickname == user_nickname)  # Filtro para las reseñas del usuario
        .filter(models.Review.rating > 7)  # Filtrar reseñas con calificación alta
    )
        
    result = await db.execute(query)
    rows = result.all()

    games_temp = {}
    for row in rows:
        if row.title not in games_temp:
            games_temp[row.title] = {
                'title': row.title,
                'primary_genre': row.primary_genre,
                'genres': row.genres,
                'steam_rating': row.steam_rating,
                'platform_rating': row.platform_rating,
                'publisher': row.publisher,
                'detected_technologies': row.detected_technologies,
                'developer': row.developer,
                'award_names': set() if row.award_names else set()
            }
        if row.award_names:
            games_temp[row.title]['award_names'].add(row.award_names)


    games_predictions = [GamePrediction(**game) for game in games_temp.values()]
    
    return games_predictions


def create_numpy_array_for_game(game: GamePrediction, genres_mapping, game_engines_mapping, award_categories_mapping):
    # Si la calificación en nuestra plataforma es 0, usa la calificación de Steam
    rating = float(game.steam_rating) 
    rating = rating 
    
    genres_array = np.zeros(len(genres_mapping))
    for genre in game.genres.split(','):
        if genre in genres_mapping:
            genres_array[genres_mapping[genre]] = 1
            
    primary_genres_array = np.zeros(len(genres_mapping))
    if game.primary_genre in genres_mapping:
        primary_genres_array[genres_mapping[game.primary_genre]] = 1
            
    game_engines_array = np.zeros(len(game_engines_mapping))
    for engine in game.detected_technologies:
        if engine in game_engines_mapping:
            game_engines_array[game_engines_mapping[engine]] = 1

    award_categories_array = np.zeros(len(award_categories_mapping))
    for award in game.award_names:
        if award in award_categories_mapping:
            award_categories_array[award_categories_mapping[award]] = 1

    # Concatenar todos los arrays en un único array unidimensional
    game_array = np.concatenate([
        [rating], 
        primary_genres_array, 
        genres_array, 
        game_engines_array, 
        award_categories_array
    ])
    
    return game_array



async def create_numpy_arrays(db: AsyncSession, user_nickname: str):
    # Obtener los juegos reseñados por el usuario
    games1 = await get_user_reviews_games(db, user_nickname)

    all_games = []
    all_games.extend(games1)

    # Obtener y añadir juegos similares
    for game in games1:
        similar_games = await get_games_prediction(db, game.title, 40, 12)
        for similar_game in similar_games:
            if similar_game not in all_games:  # Evitar duplicados
                all_games.append(similar_game)
    
    # Mapeos para géneros, motores de juegos y categorías de premios
    genres = [
        "Early Access", "Sports", "Indie", "Game Development", "Utilities",
        "Massively Multiplayer", "Video Production", "Racing", "Audio Production",
        "Sexual Content", "Gore", "Action", "Free to Play", "Adventure", "RPG",
        "Design & Illustration", "Unknown Genre", "Strategy", "Web Publishing",
        "Violent", "Nudity", "Education", "Simulation", "Casual"
    ]
    genres_mapping = {genre: index for index, genre in enumerate(genres)}
    
    game_engines = [
    "Source2", "Construct", "RPGMaker", "Love2D", "RealVirtuality", "HashLink",
    "RenPy", "C4_Engine", "Phyre", "REDengine", "Flexi", "OGRE", "Unigine",
    "Torque", "Lime_OR_OpenFL", "idTech3", "Wintermute", "idTech4", "Danmakufu",
    "Amazon_Lumberyard", "BlenderGameEngine", "AdventureGameStudio", "Marmalade",
    "idTech6", "AppGameKit", "X-Ray", "Source", "Asura", "ApexEngine", "Phaser",
    "PlayFirstPlayground", "Kex", "Diesel", "TyranoBuilder", "CryEngine", "WolfRPGEditor",
    "XNA", "UbisoftAnvil", "idTech2", "RAGE", "Godot", "Prism3D", "Defold",
    "Infinity", "Aurora", "TelltaleTool", "Virtools", "idTech2_5", "idTech7",
    "VisionaireStudio", "KiriKiri", "Glacier", "Clausewitz", "UbiArtFramework",
    "HaemimontSol", "Frostbite", "Build", "Vision", "FNA", "GoldSource", "NScripter",
    "ChromeEngine", "GameGuru", "Liquid", "4A_Engine", "Snowdrop", "Cocos", "Unity",
    "Bitsquid", "VisualNovelMaker", "Adobe_AIR", "idTech5", "RE_Engine", "MonoGame",
    "Unreal", "GameMaker", "Solar2D", "ClickTeamFusion", "Pico8"
    ]
    game_engines_mapping = {engine: index for index, engine in enumerate(game_engines)}
    
    award_categories = [
    "Best Game Direction", "Best Independent Game", "Best Art Direction",
    "Best Multiplayer Game", "Games for Impact", "Best Narrative",
    "Best Audio Design", "Game of the Year", "Best Score/Music",
    "Best Performance"
    ]
    award_categories_mapping = {category: index for index, category in enumerate(award_categories)}
    
    
    numpy_arrays = [create_numpy_array_for_game(game, genres_mapping, game_engines_mapping, award_categories_mapping).flatten() for game in all_games]

    # Concatenar todos los arrays en un único array bidimensional
    if numpy_arrays:
        combined_array = np.vstack(numpy_arrays)
    else:
        combined_array = np.array([])

    return combined_array
    
    
    