from pydantic import BaseModel, EmailStr
from typing import Optional

class PostBase(BaseModel):
    title: str
    content: str
    published : bool = True


class PostCreate(PostBase):
    pass

class PostResponse(BaseModel):
    title : str
    content : str
    published : bool

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    email : EmailStr
    password : str

class UserResponde(BaseModel):
    id: int
    email : EmailStr
    

class UserLogi(BaseModel):
    email : EmailStr
    password : str


class Token(BaseModel):
    access_token : str
    token_type : str

class TokenData(BaseModel):
    id : Optional[int] 