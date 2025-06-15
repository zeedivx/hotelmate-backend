from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import UserRegister, UserLogin, TokenResponse, UserResponse
from app.services.auth_service import auth_service
from app.config import settings

router = APIRouter()
security = HTTPBearer()


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserResponse:
    """Get current authenticated user"""
    token = credentials.credentials
    user_id = auth_service.verify_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy token dostępu",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Użytkownik nie został znaleziony",
        )

    return auth_service.user_to_response(user)


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserRegister):
    """
    Register a new user

    - **name**: Full name (minimum 2 characters)
    - **email**: Valid email address
    - **password**: Password (minimum 6 characters)
    """
    try:
        # Register user
        user = await auth_service.register_user(user_data)

        # Create access token
        access_token = auth_service.create_access_token(user.id)

        # Convert to response model
        user_response = auth_service.user_to_response(user)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRATION_HOURS * 3600,  # Convert hours to seconds
            user=user_response,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"❌ Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas rejestracji użytkownika",
        )


@router.post("/login", response_model=TokenResponse)
async def login(user_credentials: UserLogin):
    """
    Login with email and password

    - **email**: Registered email address
    - **password**: User password
    """
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(
            user_credentials.email, user_credentials.password
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nieprawidłowy email lub hasło",
            )

        # Update last login
        await auth_service.update_user_last_login(user.id)

        # Create access token
        access_token = auth_service.create_access_token(user.id)

        # Convert to response model
        user_response = auth_service.user_to_response(user)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
            user=user_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas logowania",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current user information

    Requires valid JWT token in Authorization header
    """
    return current_user


@router.post("/logout")
async def logout():
    """
    Logout user

    Note: Since we're using stateless JWT tokens, logout is handled client-side
    by removing the token from storage
    """
    return {"message": "Wylogowano pomyślnie"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: UserResponse = Depends(get_current_user)):
    """
    Refresh access token

    Requires valid JWT token in Authorization header
    """
    try:
        # Create new access token
        access_token = auth_service.create_access_token(current_user.id)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
            user=current_user,
        )

    except Exception as e:
        print(f"❌ Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas odświeżania tokenu",
        )
