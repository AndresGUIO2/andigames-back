from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ...crud import get_user_no_password, get_user_details, add_user, add_follower, get_user_followers_and_following, update_user_data, create_numpy_arrays, delete_follower, get_all_users
from ...schemas import UserBase, UserRead, UserCreate, UserUpdate, UserDetails, UserFollower, FollowerDetails, Token
from ...dependencies import get_db, get_async_db
from ...config import settings
from datetime import datetime, timedelta
from ...models import User
from ...api.auth import create_access_token, get_current_user
import numpy as np

router = APIRouter()

#Get one user by nickname
@router.get("/users/{nickname}", 
            response_model=UserRead,
            summary="Obtener un usuario dado su nickname exacto",
            description="Esta ruta te permite obtener un usuario dado su nickname exacto.",
            response_description="Retorna los datos del usuario (excepto la contraseña) con el nickname dado.",
            tags=["Users"]
)
async def read_user(nickname: str, db: Session = Depends(get_async_db)):
    db_user = await get_user_no_password(db, nickname=nickname)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

#get all users
async def get_andigames_users(db: AsyncSession = Depends(get_async_db)):
    db_users = await get_all_users(db)
    if db_users is None:
        raise HTTPException(status_code=404, detail="Users not found")
    return db_users

#get user details
@router.get(
    "/users/{nickname}/details", 
    response_model=UserDetails,
    summary="Obtener los detalles de un usuario",
    description="Esta ruta te permite obtener los detalles de un usuario.",
    tags=["Users"]
)
async def read_user_details(nickname: str, db: AsyncSession = Depends(get_async_db)):
    db_user = await get_user_details(db, user_nickname=nickname)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user


#get user followers and following
@router.get(
    "/users/{nickname}/followers&Following",
    response_model=FollowerDetails,
    summary="Obtener los seguidores y seguidos de un usuario",
    description="Esta ruta te permite obtener los seguidores y seguidos de un usuario.",
    response_description="Retorna los seguidores y seguidos de un usuario específico",
    tags=["Users"]
)
def read_user_followers_and_following(nickname: str, db: Session = Depends(get_db)):
    db_user = get_user_followers_and_following(db, user_nickname=nickname)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


#get all users
@router.get(
    "/users",
    response_model=List[UserRead],
    summary="Obtener todos los usuarios",
    description="Esta ruta te permite obtener todos los usuarios.",
    response_description="Retorna todos los usuarios",
    tags=["Users"]
)
async def read_all_users(db: AsyncSession = Depends(get_async_db)):
    db_users = await get_andigames_users(db)
    if db_users is None:
        raise HTTPException(status_code=404, detail="Users not found")
    return db_users


@router.post(
    "/register",
    response_model=str,
    summary="Registrar un nuevo usuario",
    description="Esta ruta te permite registrar un nuevo usuario en la base de datos.",
    response_description="Retorna el username(nickname) del usuario registrado",
    tags=["Users"]
)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.nickname == user_data.nickname).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Nickname already registered")
    
    # It must to be +18 years old
    if (datetime.now().date() - user_data.birthdate).days < 6570:
        raise HTTPException(status_code=400, detail="You must be +18 years old")
    
    # We only accept nicknames with letters, numbers and one underscore and >= 3 characters

    if not user_data.nickname.replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="Nickname must be alphanumeric.")

    # Verifica que haya solo un guión bajo.
    if user_data.nickname.count("_") > 1:
        raise HTTPException(status_code=400, detail="Nickname must contain only one underscore.")

    # Verifica que el apodo tenga al menos tres caracteres.
    if len(user_data.nickname) < 3:
        raise HTTPException(status_code=400, detail="Nickname must be at least 3 characters long.")

    
    # username must to be >= 3 characters
    if len(user_data.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters long")
    
    #password must to be >= 8 characters
    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    
    return add_user(db=db, user=user_data)


@router.put(
    "/users/{nickname}/update",
    response_model=UserUpdate, 
    summary="Actualizar los datos de un usuario necesita autenticación",
    description="Esta ruta te permite actualizar los datos de un usuario. El usuario deberá validar su contraseña actual para realizar la actualización.",
    response_description="Retorna los datos del usuario actualizados",
    tags=["Users"]
)
def update_user(
    nickname: str, 
    user_data: UserUpdate, 
    password: str = Body(...),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    
    print(current_user.nickname)
    
    if current_user.nickname != nickname:
        raise HTTPException(status_code=403, detail="User not authorized")
    
    db_user = db.query(User).filter(User.nickname == nickname).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not db_user.verify_password(password):
        raise HTTPException(status_code=400, detail="Password is incorrect")

    #if password is correct then update user data
    updated_user = update_user_data(db=db, user_nickname=nickname, user=user_data)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return updated_user 


#Add follower to user
@router.post(
    "/users/{nickname}/followers/add/users/{follower}", 
    response_model=UserFollower,
    summary="Agregar un seuidor a un usuario, se lleva a cabo por el usuario que sigue quien debe estar autenticado",
    description="El usuario que sigue debe estar autenticado para seguir a alguien",
    tags=["Users"]
)
def create_follower(nickname: str, follower: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    
    if current_user.nickname != follower:
        raise HTTPException(status_code=403, detail="User not authorized")
    
    db_user = get_user_no_password(db, nickname=nickname)
    db_follower = get_user_no_password(db, nickname=follower)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db_follower is None:
        raise HTTPException(status_code=404, detail="Follower not found")
    
    user_data : UserFollower = UserFollower(user_follower_nickname=follower, user_following_nickname=nickname)
    
    return add_follower(db=db, followerData=user_data)


@router.delete(
    "/users/{nickname}/followers/delete/users/{follower}", 
    response_model=UserFollower,
    summary="Eliminar un seguidor a un usuario, se lleva a cabo por el usuario que sigue quien debe estar autenticado",
    description="El usuario que sigue debe estar autenticado para dejar de seguir a alguien",
    tags=["Users"]
)
async def delete_follower_by_nickname(nickname: str, follower: str, db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):   
    if current_user.nickname != follower:
        raise HTTPException(status_code=403, detail="User not authorized")
    
    db_user = await get_user_no_password(db, nickname=nickname)
    db_follower = await get_user_no_password(db, nickname=follower)
    if db_user is None or db_follower is None:
        raise HTTPException(status_code=404, detail="User or Follower not found")

    user_data = UserFollower(user_follower_nickname=follower, user_following_nickname=nickname)
    deleted_follower = await delete_follower(db, user_data)
    if deleted_follower is None:
        raise HTTPException(status_code=404, detail="Follower relationship not found")

    return deleted_follower

#Auth
@router.post("/token", response_model=Token, tags=["AUTH"])
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
    print(user, access_token)
    # Devuelve el access token, el tipo de token, y el nickname del usuario
    return {"access_token": access_token, "token_type": "bearer", "nickname": user.nickname}


# Tests
# @router.get("/users/{nickname}/game_array", 
#             summary="Obtener el arreglo de juegos de un usuario",
#             description="Esta ruta te permite obtener el arreglo de juegos de un usuario basado en sus reseñas y juegos similares.",
#             response_description="Retorna un arreglo de juegos en formato JSON.",
#             tags=["Users"]
# )
# async def get_user_game_array(nickname: str, db: AsyncSession = Depends(get_async_db)):
#     # Obtén el arreglo de Numpy para el usuario
#     numpy_array = await create_numpy_arrays(db, nickname)

#     # Convierte el arreglo de Numpy a JSON (lista de Python)
#     json_array = numpy_array_to_json(numpy_array)

#     return json_array

# def numpy_array_to_json(array: np.ndarray) -> List:
#     return array.tolist()