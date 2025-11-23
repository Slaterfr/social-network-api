from fastapi import FastAPI, Body, Response, status, HTTPException, Depends
from sqlalchemy.orm import Session
from . import models, schemas, utils
from .database import engine, get_db 
from .routers import post, user, auth

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)

@app.get('/')
def root():
    return {'message': 'hello world'}




