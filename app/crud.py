from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models
from .schemas import UserDetails, UserBase, UserSimple ,UserCreate, UserFollower, FollowerDetails, ReviewRead

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
    # Realizar una consulta unificada
    result = db.query(
        models.User,
        models.User_followers.user_follower_nickname.label('follower_nickname'),
        models.User_followers.user_following_nickname.label('following_nickname'),
        models.Review.game_id.label('review_game_id'),
        models.Users_wishlist.game_id.label('wishlist_game_id')
    ).outerjoin(models.User_followers, models.User.nickname == models.User_followers.user_following_nickname)\
    .outerjoin(models.Review, models.User.nickname == models.Review.user_nickname)\
    .outerjoin(models.Users_wishlist, models.User.nickname == models.Users_wishlist.user_nickname)\
    .filter(models.User.nickname == user_nickname)\
    .all()

    # Procesar los resultados
    followers = set()
    following = set()
    reviews = set()
    wishlist = set()

    user_data = None
    for user, follower_nickname, following_nickname, review_game_id, wishlist_game_id in result:
        if not user_data:
            user_data = user
        if follower_nickname:
            followers.add(follower_nickname)
        if following_nickname:
            following.add(following_nickname)
        if review_game_id:
            reviews.add(review_game_id)
        if wishlist_game_id:
            wishlist.add(wishlist_game_id)

    # Crear UserDetails
    user_details = UserDetails(
        nickname=user_data.nickname,
        username=user_data.username,
        about_me=user_data.about_me,
        followers=[UserSimple(nickname=f) for f in followers],
        following=[UserSimple(nickname=f) for f in following],
        reviews=list(reviews),
        wishlist=list(wishlist)
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

# Get followers and following with details 
def get_user_followers_and_following(db: Session, user_nickname: str) -> FollowerDetails:
    # Consulta unificada para seguidores y usuarios seguidos
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

    # Procesar seguidores
    for follower_nickname, nickname, username, review_game_id in followers_query:
        if follower_nickname not in followers:
            followers[follower_nickname] = {
                "nickname": nickname,
                "username": username,
                "reviews": []
            }
        if review_game_id:
            followers[follower_nickname]["reviews"].append(review_game_id)

    # Procesar seguidos
    for following_nickname, nickname, username, review_game_id in following_query:
        if following_nickname not in following:
            following[following_nickname] = {
                "nickname": nickname,
                "username": username,
                "reviews": []
            }
        if review_game_id:
            following[following_nickname]["reviews"].append(review_game_id)

    # Crear la respuesta final
    follower_details = FollowerDetails(
        followers=list(followers.values()),
        following=list(following.values())
    )

    return follower_details
    
    
    
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

    