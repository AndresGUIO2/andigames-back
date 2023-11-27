from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Numeric
#from sqlalchemy.orm import relationship
from app.database import Base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Numeric, Date

Base = declarative_base()

class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    url = Column(String(24))
    release_date = Column(Date)
    primary_genre = Column(String(32))
    genres = Column(String)
    steam_rating = Column(Numeric(4,2))
    platform_rating = Column(Numeric(3,1))
    publisher = Column(String)
    detected_technologies = Column(String)
    developer = Column(String)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'primary_genre': self.primary_genre,
            'genres': self.genres,
            'steam_rating': float(self.steam_rating) if self.steam_rating is not None else None,
            'platform_rating': float(self.platform_rating) if self.platform_rating is not None else None,
            'publisher': self.publisher,
            'detected_technologies': self.detected_technologies,
            'developer': self.developer
        }

class User(Base):
    __tablename__ = 'users'
    nickname = Column(String(16), primary_key=True)
    email = Column(String(64))
    password = Column(String(64))
    genre = Column(String(1))
    about_me = Column(String(256))
    birthdate = Column(Date)
    username = Column(String(17))
    
    def verify_password(self, password):
        return pwd_context.verify(password, self.password)
    
    def hash_password(self, plain_password):
        self.password = pwd_context.hash(plain_password)

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    user_nickname = Column(String(16), ForeignKey('users.nickname'))
    review_date = Column(Date)
    rating = Column(Numeric(3,1))
    commentary = Column(String(256))
    
class Award(Base):
    __tablename__ = 'awards'
    id = Column(Integer, primary_key=True)
    name= Column(String(64))
    description = Column(String(256))
    category = Column(String(64))
    
class Game_awards(Base):
    __tablename__ = 'game_awards'
    game_id = Column(Integer, ForeignKey('games.id'), primary_key=True)
    award_id = Column(Integer, ForeignKey('awards.id'), primary_key=True)
    year = Column(Integer)

class User_followers(Base):
    __tablename__= 'user_followers'
    user_follower_nickname = Column(String(16), ForeignKey('users.nickname'), primary_key=True)
    user_following_nickname = Column(String(16), ForeignKey('users.nickname'), primary_key=True)

class Users_wishlist(Base):
    __tablename__= 'users_wishlist'
    game_id = Column(Integer, ForeignKey('games.id'), primary_key=True)
    user_nickname = Column(String(16), ForeignKey('users.nickname'), primary_key=True)
    
class Game_vectors(Base):
    __tablename__ = 'game_vectors'
    game_id = Column(Integer, ForeignKey('games.id'), primary_key=True)
    faiss_index = Column(Integer)
