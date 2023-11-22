from pydantic import BaseModel, validator
from typing import List, Optional, Any
from datetime import date

class GameBase(BaseModel):
    title: str
    url: str 
    release_date: str
    primary_genre: str
    genres: str
    steam_rating: float
    publisher: str
    detected_technologies: str
    developer: str

class GameCreate(GameBase):
    platform_rating: float = 0.0
    pass

class GameRead(GameBase):
    id: int
    platform_rating: float

    class Config:
        from_attributes = True

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
    developer: Optional[str]

class GameDetails(GameRead):
    reviews: List['ReviewRead'] = []
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
    pass

    class Config:
        from_attributes = True

class ReviewUpdate(BaseModel):
    game_id: Optional[int]
    user_nickname: Optional[str]
    review_date: Optional[str]
    rating: Optional[float]
    commentary: Optional[str]
    
class FollowerDetails(BaseModel):
    followers : List['UserNicknameUsernameReviews'] = []

class UserBase(BaseModel):
    nickname: str
    email: str
    password: str
    genre: str
    about_me: str
    birthdate: str
    username: str

class UserSimple(BaseModel):
    nickname: str
    
class UserNicknameUsernameReviews(BaseModel):
    nickname: str
    username: str
    reviews: List['ReviewRead'] = []    
    
class UserCreate(BaseModel):
    nickname: str
    email: str
    password: str
    genre: str
    about_me: str
    birthdate: date
    username: str

    @validator('birthdate', pre=True)
    def parse_birthdate(cls, value):
        if isinstance(value, str):
            return date.fromisoformat(value)
        return value
    
class UserRead(UserBase):
    pass

    class Config:
        from_attributes = True

    @validator('birthdate', pre=True)
    def parse_birthdate(cls, value):
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        return value

class UserUpdate(BaseModel):
    nickname: Optional[str]
    email: Optional[str]
    password: Optional[str]
    genre: Optional[str]
    about_me: Optional[str]
    birthdate: Optional[str]
    username: Optional[str]

class UserDetails(BaseModel):
    nickname: Optional[str]
    username: Optional[str]
    about_me: Optional[str]
    followers: List['UserSimple'] = []
    following: List['UserSimple'] = []
    reviews: List['int'] = []
    wishlist: Optional[List['int']] = [] 

    class Config:
        from_attributes = True
        
class UserFollower(BaseModel):
    user_follower_nickname: str
    user_following_nickname: str
