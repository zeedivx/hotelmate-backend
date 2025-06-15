from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# Request models (input)
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password")

    class Config:
        json_json_schema_extra = {
            "example": {
                "name": "Jan Kowalski",
                "email": "jan@example.com",
                "password": "securepassword123",
            }
        }


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")

    class Config:
        json_schema_extra = {
            "example": {"email": "jan@example.com", "password": "securepassword123"}
        }


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None

    class Config:
        json_schema_extra = {"example": {"name": "Jan Nowak"}}


# Response models (output)
class UserResponse(BaseModel):
    id: str = Field(..., description="User ID")
    name: str = Field(..., description="Full name")
    is_admin: bool = Field(default=False, description="Is user an admin")
    email: EmailStr = Field(..., description="Email address")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "user123",
                "name": "Jan Kowalski",
                "is_admin": False,
                "email": "jan@example.com",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T14:45:00Z",
            }
        }


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "id": "user123",
                    "name": "Jan Kowalski",
                    "email": "jan@example.com",
                    "created_at": "2024-01-15T10:30:00Z",
                },
            }
        }


# Database model (internal)
class UserInDB(BaseModel):
    id: Optional[str] = None
    name: str
    email: str
    is_admin: bool = False
    hashed_password: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for Firestore"""
        data = self.model_dump()
        data.pop("id", None)  # Firestore handles ID separately
        return data

    @classmethod
    def from_dict(cls, data: dict, doc_id: str = None):
        """Create from Firestore document"""
        if doc_id:
            data["id"] = doc_id
        return cls(**data)
