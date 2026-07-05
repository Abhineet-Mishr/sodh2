from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    security_key: str

class UserResponse(BaseModel):
    email: EmailStr
    credits: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
