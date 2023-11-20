from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import games, users

import os

# variables s
from dotenv import load_dotenv

app = FastAPI()

# CORS configuration
origins = {
    "http://localhost",
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(games.router)
#app.include_router(reviews.router)

# Here we load the .env file
load_dotenv()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port= int(os.environ.get("PORT", 8000)))
    print("Hello world")

