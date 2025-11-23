from .. import models, schemas, utils, oauth2
from fastapi import FastAPI, Body, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from ..database import get_db 

router = APIRouter(
    prefix='/posts',
    tags=['Posts']
)


@router.get('/')
def get_posts(db : Session = Depends(get_db)):
    posts = db.query(models.Posts).all()
    print(posts)
    return posts

@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.PostResponse)
def create_posts(post: schemas.PostCreate, db : Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
   # cur.execute("""INSERT INTO posts(title, content, published) VALUES(%s, %s, %s) RETURNING *""", (post.title, post.content, post.published))
    #new_post = cur.fetchone()
    #conn.commit()
    new_post = models.Posts(**post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    print(current_user.email)
    return new_post


@router.get('/{id}')
def get_post( id:int, db : Session = Depends(get_db)):
    post = db.query(models.Posts).filter(models.Posts.id == id).first()
    print(post)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"couldn't find a post with that id ({id})")
    return {f"post with id of {id}": post }

@router.delete('/{id}')
def delete_post(id:int, db : Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    post = db.query(models.Posts).filter(models.Posts.id == id)

    if post.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"couldn't find a post with that id ({id})")

    post.delete(synchronize_session=False)
    db.commit()
    return {"deleted post"}

@router.put('/{id}')
def update_post(id:int, updated_post : schemas.PostBase, db : Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Posts).filter(models.Posts.id == id)
    post = post_query.first()
    if post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"couldn't find a post with that id ({id})")
    post_query.update(updated_post.dict(), synchronize_session=False)
    db.commit()
    return updated_post