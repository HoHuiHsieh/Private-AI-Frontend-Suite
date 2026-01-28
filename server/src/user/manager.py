import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import bcrypt
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from config import Config

from . import models
from database import UserDB, RefreshTokenDB
from typing import Any

# Load configuration
config = Config()


class TokenManager:
    """Manager for JWT token operations."""

    def __init__(self):
        """Initialize token manager with configuration."""
        auth_config = config.get_authentication_config()
        self.secret_key = auth_config.secret_key
        self.algorithm = auth_config.algorithm
        self.access_token_expire = auth_config.access_token_expire_time
        self.refresh_token_expire = auth_config.refresh_token_expire_time

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + \
                timedelta(seconds=self.access_token_expire)

        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        encoded_jwt = jwt.encode(
            to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self) -> str:
        """Generate a random refresh token."""
        return secrets.token_urlsafe(32)

    def decode_token(self, token: str) -> Optional[models.TokenData]:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key,
                                 algorithms=[self.algorithm])
            username: str = payload.get("sub")
            scopes: List[str] = payload.get("scopes", [])

            if username is None:
                return None

            return models.TokenData(
                sub=username,
                scopes=scopes,
                exp=payload.get("exp"),
                iat=payload.get("iat")
            )
        except JWTError:
            return None

    def store_refresh_token(
        self,
        db: Session,
        token: str,
        user_id: int,
        expires_delta: Optional[timedelta] = None
    ) -> RefreshTokenDB:
        """Store refresh token in database."""
        if expires_delta:
            expires_at = datetime.utcnow() + expires_delta
        else:
            expires_at = datetime.utcnow() + timedelta(seconds=self.refresh_token_expire)

        db_token = RefreshTokenDB(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
            revoked=False
        )
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
        return db_token

    def get_refresh_token(self, db: Session, token: str) -> Optional[Any]:
        """Get refresh token from database."""
        return db.query(RefreshTokenDB).filter(
            RefreshTokenDB.token == token,
            RefreshTokenDB.revoked == False,
            RefreshTokenDB.expires_at > datetime.utcnow()
        ).first()

    def revoke_refresh_token(self, db: Session, token: str) -> bool:
        """Revoke a refresh token."""
        db_token = db.query(RefreshTokenDB).filter(
            RefreshTokenDB.token == token).first()
        if db_token:
            db_token.revoked = True
            db.commit()
            return True
        return False


class UserManager:
    """Manager for user operations."""

    def __init__(self):
        """Initialize user manager."""
        pass

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash using bcrypt."""
        try:
            password_bytes = plain_password.encode('utf-8')
            hash_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception:
            return False

    def get_password_hash(self, password: str) -> str:
        """Hash a password using bcrypt."""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        return hashed_password

    def get_user(self, db: Session, username: str) -> Optional[models.User]:
        """Get user by username."""
        db_user = db.query(UserDB).filter(UserDB.username == username).first()
        if db_user:
            return self._db_user_to_model(db_user)
        return None

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[models.User]:
        """Get user by ID."""
        db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
        if db_user:
            return self._db_user_to_model(db_user)
        return None

    def get_user_by_email(self, db: Session, email: str) -> Optional[models.User]:
        """Get user by email."""
        db_user = db.query(UserDB).filter(UserDB.email == email).first()
        if db_user:
            return self._db_user_to_model(db_user)
        return None

    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
        """Get list of users with pagination."""
        db_users = db.query(UserDB).offset(skip).limit(limit).all()
        return [self._db_user_to_model(user) for user in db_users]

    def create_user(
        self,
        db: Session,
        username: str,
        email: str,
        fullname: str,
        password: str,
        active: bool = True,
        scopes: Optional[List[str]] = None
    ) -> models.User:
        """Create a new user."""
        hashed_password = self.get_password_hash(password)

        db_user = UserDB(
            username=username,
            email=email,
            fullname=fullname,
            hashed_password=hashed_password,
            active=active,
            scopes=scopes or []
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return self._db_user_to_model(db_user)

    def update_user(
        self,
        db: Session,
        username: str,
        email: Optional[str] = None,
        fullname: Optional[str] = None,
        password: Optional[str] = None,
        active: Optional[bool] = None,
        scopes: Optional[List[str]] = None
    ) -> Optional[models.User]:
        """Update user information."""
        db_user = db.query(UserDB).filter(UserDB.username == username).first()

        if not db_user:
            return None

        if email is not None:
            db_user.email = email
        if fullname is not None:
            db_user.fullname = fullname
        if password is not None:
            db_user.hashed_password = self.get_password_hash(password)
        if active is not None:
            db_user.active = active
        if scopes is not None:
            db_user.scopes = scopes

        db_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_user)

        return self._db_user_to_model(db_user)

    def delete_user(self, db: Session, username: str) -> bool:
        """Delete a user."""
        db_user = db.query(UserDB).filter(UserDB.username == username).first()

        if not db_user:
            return False

        db.delete(db_user)
        db.commit()
        return True

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[models.User]:
        """Authenticate user with email and password."""
        db_user = db.query(UserDB).filter(UserDB.email == email).first()

        if not db_user:
            return None

        if not self.verify_password(password, db_user.hashed_password):
            return None

        return self._db_user_to_model(db_user)

    def _db_user_to_model(self, db_user: UserDB) -> models.User:
        """Convert database user to model user."""
        return models.User(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            fullname=db_user.fullname,
            active=db_user.active,
            scopes=db_user.scopes or [],
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )
