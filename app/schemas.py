from pydantic import BaseModel, validator
from typing import List, Optional, Any
from sqlalchemy import Numeric
from datetime import date
from decimal import Decimal

class GameBase(BaseModel):
    title: str
    url: str 
    release_date: str
    primary_genre: str
    genres: str
    steam_rating: float
    publisher: str
    detected_technologies: str

class GameCreate(GameBase):
    platform_rating: float = 0.0
    pass

class GameRead(GameBase):
    id: int
    title: str
    url: str 
    release_date: str
    primary_genre: str
    genres: str
    steam_rating: float
    platform_rating: float
    publisher: str
    detected_technologies: str

    class Config:
        from_attributes = True     #Allows to parse the date from the database to the model

    #This method is used to parse the date from the database to the model
    @validator('release_date', pre=True)
    def parse_release_date(cls, value):
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        return value

class GameUpdate(BaseModel):
    title: Optional[str]
    url: Optional[str]
    release_date: Optional[str]
    primary_genre: Optional[str]
    genres: Optional[str]
    steam_rating: Optional[float]
    platform_rating: Optional[float]
    publisher: Optional[str]
    detected_technologies: Optional[str]

class GameDetails(GameRead):
    reviews: List['ReviewRead'] = []
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    nickname: str
    email: str
    password: str
    genre: str
    about_me: str
    birth_date: str
    username: str

class UserCreate(UserBase):
    pass 

class UserRead(UserBase):
    nickname: str
    email: str
    genre: str
    about_me: str
    birth_date: str
    username: str

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    nickname: Optional[str]
    email: Optional[str]
    password: Optional[str]
    genre: Optional[str]
    about_me: Optional[str]
    birth_date: Optional[str]
    username: Optional[str]

class UserDetails(UserRead):
    followers: List['UserRead'] = []
    following: List['UserRead'] = []
    reviews: List['ReviewRead'] = []
    games: List['GameRead'] = []
    wishlist: Optional[List['GameRead']] = [] 

    class Config:
        from_attributes = True

class ReviewBase(BaseModel):
    game_id: int
    user_nickname: str
    review_date: str
    rating: float
    commentary: str
    
class ReviewCreate(ReviewBase):
    pass

class ReviewRead(ReviewBase):
    game_id: int
    user_nickname: str
    review_date: str
    rating: float
    commentary: str

    class Config:
        from_attributes = True

class ReviewUpdate(BaseModel):
    game_id: Optional[int]
    user_nickname: Optional[str]
    review_date: Optional[str]
    rating: Optional[float]
    commentary: Optional[str]

