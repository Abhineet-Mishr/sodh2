from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import get_password_hash, verify_password
from app.core.config import settings
from typing import Optional

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def authenticate(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_user(db: Session, email: str, password: str, security_key: str) -> User:
    db_user = User(
        email=email,
        password_hash=get_password_hash(password),
        security_key_hash=get_password_hash(security_key),
        credits=settings.INITIAL_USER_CREDITS
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
