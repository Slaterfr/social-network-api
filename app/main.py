from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models
from app.repository.database import engine
from .routers import post, user, auth, vote, comment, friendship, notification, community

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(vote.router)
app.include_router(comment.router)
app.include_router(friendship.router)
app.include_router(notification.router)
app.include_router(community.router)

@app.get('/')
def root():
    return {'message': 'hello world'}

