from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ...crud import get_user_no_password, get_user_details, add_user, add_follower, get_user_followers_and_following
from ...schemas import UserBase, UserRead, UserCreate, UserUpdate, UserDetails, UserFollower, FollowerDetails
from ...dependencies import get_db

router = APIRouter()

#Get one user by nickname
@router.get("/users/{nickname}", response_model=UserRead)
def read_user(nickname: str, db: Session = Depends(get_db)):
    db_user = get_user_no_password(db, nickname=nickname)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

#get user details
@router.get("/users/{nickname}/details", response_model=UserDetails)
def read_user_details(nickname: str, db: Session = Depends(get_db)):
    db_user = get_user_details(db, user_nickname=nickname)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

#get user followers and following
@router.get("/users/{nickname}/followers&Following", response_model=FollowerDetails)
def read_user_followers_and_following(nickname: str, db: Session = Depends(get_db)):
    db_user = get_user_followers_and_following(db, user_nickname=nickname)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


#Add user to database
@router.post("/users/add/", response_model=UserCreate)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_no_password(db, nickname=user_data.nickname)
    if db_user:
        raise HTTPException(status_code=400, detail="Nickname already registered")    
    return add_user(db=db, user=user_data)

#add follower to user followers
@router.post("/users/{nickname}/followers/add/users/{follower}", response_model= UserFollower)
def create_follower(nickname: str, follower: str, db: Session = Depends(get_db)):
    db_user = get_user_no_password(db, nickname=nickname)
    db_follower = get_user_no_password(db, nickname=follower)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db_follower is None:
        raise HTTPException(status_code=404, detail="Follower not found")
    
    user_data : UserFollower = UserFollower(user_follower_nickname=follower, user_following_nickname=nickname)
    
    return add_follower(db=db, followerData=user_data)