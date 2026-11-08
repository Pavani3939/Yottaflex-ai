"""
YottaPay AI – Authentication Router
Demo authentication using JWT.
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode("utf-8")
        return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Demo users (in-memory — replace with DB in production)
# ---------------------------------------------------------------------------
DEMO_PASSWORD_HASH = hash_password("password123")

DEMO_USERS = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@yottapay.ai",
        "role": "admin",
        "hashed_password": DEMO_PASSWORD_HASH,
        "disabled": False,
    },
    "analyst": {
        "username": "analyst",
        "full_name": "Ops Analyst",
        "email": "analyst@yottapay.ai",
        "role": "ops_analyst",
        "hashed_password": DEMO_PASSWORD_HASH,
        "disabled": False,
    },
    "finance": {
        "username": "finance",
        "full_name": "Finance Manager",
        "email": "finance@yottapay.ai",
        "role": "finance_manager",
        "hashed_password": DEMO_PASSWORD_HASH,
        "disabled": False,
    },
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str
    full_name: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserOut(BaseModel):
    username: str
    full_name: str
    email: str
    role: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = DEMO_USERS.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = DEMO_USERS.get(username)
    if user is None or user.get("disabled"):
        raise credentials_exception
    return user


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate and return a JWT access token."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return Token(
        access_token=access_token,
        token_type="bearer",
        username=user["username"],
        role=user["role"],
        full_name=user["full_name"],
    )


@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return UserOut(**{k: current_user[k] for k in ("username", "full_name", "email", "role")})
