from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from ...crud import get_user_no_password, get_user_details, add_user, add_follower, get_user_followers_and_following
from ...schemas import UserBase, UserRead, UserCreate, UserUpdate, UserDetails, UserFollower, FollowerDetails, Token
from ...dependencies import get_db 
from ...config import settings
from datetime import datetime, timedelta
from ...models import User
from ...api.auth import create_access_token, get_current_user

router = APIRouter()

#Get one user by nickname
@router.get("/users/{nickname}", 
            response_model=UserRead,
            summary="Obtener un usuario dado su nickname exacto",
            description="Esta ruta te permite obtener un usuario dado su nickname exacto.",
            response_description="Retorna los datos del usuario (excepto la contraseña) con el nickname dado."
)
def read_user(nickname: str, db: Session = Depends(get_db)):
    db_user = get_user_no_password(db, nickname=nickname)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

#get user details
@router.get(
    "/users/{nickname}/details", 
    response_model=UserDetails,
    summary="Obtener los detalles de un usuario",
    description="Esta ruta te permite obtener los detalles de un usuario."
)
def read_user_details(nickname: str, db: Session = Depends(get_db)):
    db_user = get_user_details(db, user_nickname=nickname)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

#get user followers and following
@router.get(
    "/users/{nickname}/followers&Following",
    response_model=FollowerDetails,
    summary="Obtener los seguidores y seguidos de un usuario",
    description="Esta ruta te permite obtener los seguidores y seguidos de un usuario.",
    response_description="Retorna los seguidores y seguidos de un usuario específico"
)
def read_user_followers_and_following(nickname: str, db: Session = Depends(get_db)):
    db_user = get_user_followers_and_following(db, user_nickname=nickname)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post(
    "/users/register/",
    response_model=UserCreate,
    summary="Registrar un nuevo usuario",
    description="Esta ruta te permite registrar un nuevo usuario en la base de datos.",
    response_description="Retorna el username(nickname) del usuario registrado",
)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_no_password(db, nickname=user_data.nickname)
    if db_user:
        raise HTTPException(status_code=400, detail="Nickname already registered")    
    return add_user(db=db, user=user_data.nickname)

#Add follower to user
@router.post(
    "/users/{nickname}/followers/add/users/{follower}", 
    response_model=UserFollower,
    summary="Agregar un seuidor a un usuario, se lleva a cabo por el usuario que sigue",
    description="El usuario que sigue debe estar autenticado para seguir a alguien",
)
def create_follower(nickname: str, follower: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    
    if current_user.nickname != nickname:
        raise HTTPException(status_code=403, detail="User not authorized")
    
    db_user = get_user_no_password(db, nickname=nickname)
    db_follower = get_user_no_password(db, nickname=follower)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db_follower is None:
        raise HTTPException(status_code=404, detail="Follower not found")
    
    user_data : UserFollower = UserFollower(user_follower_nickname=follower, user_following_nickname=nickname)
    
    return add_follower(db=db, followerData=user_data)

#Auth
@router.post("/users/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.nickname == form_data.username).first()
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.time_to_expire)
    access_token = create_access_token(
        data={"sub": user.nickname}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}