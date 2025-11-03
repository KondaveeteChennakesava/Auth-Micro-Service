from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import logging
import time
import asyncio
from collections import defaultdict

from config import get_settings
from database import get_db, init_db, UserDB
from auth_service import AuthService
from models import (
    Token, TokenResponse, User, UserCreate,
    MessageResponse, UserInDB
)
from background_tasks import cleanup_expired_tokens_task, startup_cleanup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/token")

rate_limiter = defaultdict(list)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""

    logger.info("Starting up the application...")
    init_db()
    logger.info("Database initialized")

    await startup_cleanup()

    cleanup_task = asyncio.create_task(cleanup_expired_tokens_task())
    logger.info("Background token cleanup task started")

    yield

    logger.info("Shutting down the application...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        logger.info("Background cleanup task cancelled")
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    description="Authentication microservice with JWT tokens",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def rate_limit_check(request: Request):
    """Simple rate limiting for authentication endpoints"""
    client_ip = request.client.host
    current_time = time.time()

    rate_limiter[client_ip] = [
        timestamp for timestamp in rate_limiter[client_ip]
        if current_time - timestamp < 60
    ]

    if len(rate_limiter[client_ip]) >= settings.rate_limit_per_minute:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )

    rate_limiter[client_ip].append(current_time)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserDB:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if AuthService.is_token_blacklisted(db, token):
        logger.warning("Attempt to use blacklisted token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = AuthService.decode_token(token)
    if token_data.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = AuthService.get_user_by_username(db, token_data.username)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: UserDB = Depends(get_current_user)
) -> UserDB:
    """Ensure user is active"""
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return current_user


@app.post(
    f"{settings.api_v1_prefix}/register",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with username, email, and password"
)
async def register(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        db_user = AuthService.create_user(db, user)
        return User.model_validate(db_user)
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@app.post(
    f"{settings.api_v1_prefix}/login",
    response_model=TokenResponse,
    summary="Login for access token",
    description="Authenticate with username and password to receive access and refresh tokens"
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit_check)
):
    """Login endpoint with rate limiting"""
    user = AuthService.authenticate_user(
        db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    access_token_expires = timedelta(
        minutes=settings.access_token_expire_minutes)

    refresh_token_expires = timedelta(days=settings.refresh_token_expire_days)

    access_token = AuthService.create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    refresh_token = AuthService.create_refresh_token(
        data={"sub": user.username},
        expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@app.post(
    f"{settings.api_v1_prefix}/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Use refresh token to get a new access token"
)
async def refresh_access_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    if AuthService.is_token_blacklisted(db, refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = AuthService.decode_token(refresh_token)

    if token_data.token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Refresh token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = AuthService.get_user_by_username(db, token_data.username)
    if not user or user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled"
        )

    access_token_expires = timedelta(
        minutes=settings.access_token_expire_minutes)

    access_token = AuthService.create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.post(
    f"{settings.api_v1_prefix}/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Logout current user and blacklist the access token"
)
async def logout(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """Logout user and blacklist token"""
    AuthService.blacklist_token(db, token)
    logger.info(f"User {current_user.username} logged out")
    return MessageResponse(
        message="Successfully logged out",
        detail="Token has been revoked"
    )


@app.get(
    f"{settings.api_v1_prefix}/users/me",
    response_model=User,
    summary="Get current user",
    description="Get the current authenticated user's information"
)
async def read_users_me(
    current_user: UserDB = Depends(get_current_active_user)
):
    """Get current user information"""
    return User.model_validate(current_user)


@app.get(
    "/health",
    response_model=MessageResponse,
    summary="Health check",
    description="Check if the service is running and database is accessible"
)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with database connectivity check"""
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return MessageResponse(
            message="healthy",
            detail="Service and database are operational"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )


@app.get(
    "/",
    summary="Root endpoint",
    description="API information"
)
async def root():
    """Root endpoint"""
    return {
        "service": settings.project_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.post(
    f"{settings.api_v1_prefix}/admin/cleanup-tokens",
    response_model=MessageResponse,
    summary="Manual token cleanup",
    description="Manually trigger cleanup of expired tokens from blacklist (admin endpoint)"
)
async def manual_token_cleanup(
    current_user: UserDB = Depends(get_current_active_user)
):
    """Manually trigger token cleanup"""
    try:
        from database import cleanup_expired_tokens
        deleted_count = cleanup_expired_tokens()
        logger.info(f"Manual cleanup: removed {deleted_count} expired tokens")
        return MessageResponse(
            message="Cleanup completed",
            detail=f"Removed {deleted_count} expired tokens from blacklist"
        )
    except Exception as e:
        logger.error(f"Manual cleanup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cleanup failed"
        )
