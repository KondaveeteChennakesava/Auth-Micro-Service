from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging
import hashlib
import base64
import bcrypt as _bcrypt

from config import get_settings
from database import UserDB, TokenBlacklist
from models import UserCreate, UserInDB, TokenData

settings = get_settings()
logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service layer"""

    @staticmethod
    def _normalize_password(password: str) -> str:
        """
        Normalize password for bcrypt by hashing with SHA-256 first.
        """
        password_hash = hashlib.sha256(password.encode('utf-8')).digest()
        normalized = base64.b64encode(password_hash).decode('ascii')

        return normalized

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            normalized = AuthService._normalize_password(plain_password)

            return _bcrypt.checkpw(
                normalized.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}")
            return False

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash (handles passwords of any length)"""
        try:
            logger.info(
                f"Hashing password - original length: {len(password)} chars, {len(password.encode('utf-8'))} bytes")
            normalized = AuthService._normalize_password(password)
            logger.info(
                f"Normalized password length: {len(normalized)} chars, {len(normalized.encode('utf-8'))} bytes")

            salt = _bcrypt.gensalt(rounds=12)
            hashed = _bcrypt.hashpw(normalized.encode('utf-8'), salt)
            logger.info(f"Successfully hashed password")
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Error hashing password: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to hash password: {str(e)}")

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[UserDB]:
        """Get user by username"""
        return db.query(UserDB).filter(UserDB.username == username.lower()).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[UserDB]:
        """Get user by email"""
        return db.query(UserDB).filter(UserDB.email == email.lower()).first()

    @staticmethod
    def create_user(db: Session, user: UserCreate) -> UserDB:
        """Create a new user"""

        if AuthService.get_user_by_username(db, user.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        if AuthService.get_user_by_email(db, user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        hashed_password = AuthService.get_password_hash(user.password)
        db_user = UserDB(
            username=user.username.lower(),
            email=user.email.lower(),
            full_name=user.full_name,
            hashed_password=hashed_password,
            disabled=False
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        logger.info(f"New user created: {user.username}")
        return db_user

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[UserDB]:
        """Authenticate user with username and password"""
        user = AuthService.get_user_by_username(db, username)
        if not user:
            logger.warning(
                f"Failed login attempt for non-existent user: {username}")
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            logger.warning(
                f"Failed login attempt with incorrect password for user: {username}")
            return None
        logger.info(f"Successful login for user: {username}")
        return user

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(
            to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=7)

        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(
            to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> TokenData:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, settings.secret_key,
                                 algorithms=[settings.algorithm])
            username: str = payload.get("sub")
            token_type: str = payload.get("type", "access")

            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return TokenData(username=username, token_type=token_type)
        except JWTError as e:
            logger.error(f"JWT decode error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def is_token_blacklisted(db: Session, token: str) -> bool:
        """Check if token is blacklisted"""
        return db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first() is not None

    @staticmethod
    def blacklist_token(db: Session, token: str) -> None:
        """Add token to blacklist with expiration time"""
        try:
            payload = jwt.decode(token, settings.secret_key,
                                 algorithms=[settings.algorithm])
            exp_timestamp = payload.get("exp")

            if exp_timestamp:
                expires_at = datetime.fromtimestamp(
                    exp_timestamp, tz=timezone.utc)
            else:

                expires_at = datetime.now(timezone.utc) + timedelta(
                    minutes=settings.access_token_expire_minutes
                )

            blacklisted_token = TokenBlacklist(
                token=token,
                blacklisted_on=datetime.now(timezone.utc),
                expires_at=expires_at
            )
            db.add(blacklisted_token)
            db.commit()
            logger.info(f"Token blacklisted, expires at: {expires_at}")
        except Exception as e:
            logger.error(f"Error blacklisting token: {str(e)}")
            db.rollback()
            raise
