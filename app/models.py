from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Numeric
from sqlalchemy.orm import relationship
from app.database import Base

class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    url = Column(String(24))
    release_date = Column(Date)
    primary_genre = Column(String(32))
    genres = Column(String)
    steam_rating = Column(Numeric(4,2))
    platform_rating = Column(Numeric(2,1))
    publisher = Column(String)
    detected_technologies = Column(String)
    developer = Column(String)

class User(Base):
    __tablename__ = 'users'
    nickname = Column(String(16), primary_key=True)
    email = Column(String(64))
    password = Column(String(72))
    genre = Column(String(1))
    about_me = Column(String(256))
    birth_date = Column(Date)
    username = Column(String(16))

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    user_nickname = Column(String(16), ForeignKey('users.nickname'))
    review_date = Column(Date)
    rating = Column(Numeric(2,1))
    commentary = Column(String(256))

class user_follower(Base):
    __tablename__= 'user_followers'
    id = Column(Integer, primary_key=True)
    user_follower_nickname = Column(String(16), ForeignKey('users.nickname'))
    user_following_nickname = Column(String(16), ForeignKey('users.nickname'))

class user_game(Base):
    __tablename__= 'user_games'
    id = Column(Integer, primary_key=True)
    user_nickname = Column(String(16), ForeignKey('users.nickname'))
    user_game_id = Column(Integer, ForeignKey('games.id'))

class user_wishlist(Base):
    __tablename__= 'user_wishlists'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    user_nickname = Column(String(16), ForeignKey('users.nickname'))
