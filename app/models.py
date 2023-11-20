from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Numeric
#from sqlalchemy.orm import relationship
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
    birthdate = Column(Date)
    username = Column(String(16))

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    user_nickname = Column(String(16), ForeignKey('users.nickname'))
    review_date = Column(Date)
    rating = Column(Numeric(2,1))
    commentary = Column(String(256))

class User_followers(Base):
    __tablename__= 'user_followers'
    user_follower_nickname = Column(String(16), ForeignKey('users.nickname'), primary_key=True)
    user_following_nickname = Column(String(16), ForeignKey('users.nickname'), primary_key=True)

class Users_wishlist(Base):
    __tablename__= 'users_wishlist'
    game_id = Column(Integer, ForeignKey('games.id'), primary_key=True)
    user_nickname = Column(String(16), ForeignKey('users.nickname'), primary_key=True)
