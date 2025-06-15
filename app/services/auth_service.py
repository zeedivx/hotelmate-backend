from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
from app.models.user import UserInDB, UserRegister, UserResponse
from app.services.firebase_service import firebase_service

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(
        user_id: str, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                hours=settings.JWT_EXPIRATION_HOURS
            )

        to_encode = {
            "sub": user_id,  # subject - user ID
            "exp": expire,  # expiration time
            "iat": datetime.now(timezone.utc),  # issued at
            "type": "access_token",
        }

        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[str]:
        """Verify JWT token and return user_id"""
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")

            if user_id is None or token_type != "access_token":
                return None

            return user_id
        except JWTError:
            return None

    @staticmethod
    async def register_user(user_data: UserRegister) -> UserInDB:
        """Register a new user"""
        # Check if user already exists
        existing_user = await firebase_service.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email już jest zarejestrowany")

        # Hash the password
        hashed_password = AuthService.hash_password(user_data.password)

        # Create user object
        user_in_db = UserInDB(
            name=user_data.name,
            email=str(user_data.email),
            hashed_password=hashed_password,
            created_at=datetime.now(timezone.utc),
            is_active=True,
        )

        # Save to Firestore
        user_id = await firebase_service.create_document(
            settings.USERS_COLLECTION, user_in_db.to_dict()
        )

        user_in_db.id = user_id
        return user_in_db

    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with email and password"""
        # Get user from database
        user_data = await firebase_service.get_user_by_email(email)
        if not user_data:
            return None

        # Create user object
        user = UserInDB.from_dict(user_data, user_data.get("id"))

        # Check if user is active
        if not user.is_active:
            return None

        # Verify password
        if not AuthService.verify_password(password, user.hashed_password):
            return None

        return user

    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[UserInDB]:
        """Get user by ID"""
        user_data = await firebase_service.get_document(
            settings.USERS_COLLECTION, user_id
        )
        if not user_data:
            return None

        return UserInDB.from_dict(user_data, user_id)

    @staticmethod
    def user_to_response(user: UserInDB) -> UserResponse:
        """Convert UserInDB to UserResponse"""
        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @staticmethod
    async def update_user_last_login(user_id: str):
        """Update user's last login timestamp"""
        try:
            await firebase_service.update_document(
                settings.USERS_COLLECTION,
                user_id,
                {"last_login": datetime.now(timezone.utc)},
            )
        except Exception as e:
            # Don't fail login if this fails
            print(f"⚠️ Failed to update last login for user {user_id}: {e}")


# Create service instance
auth_service = AuthService()
