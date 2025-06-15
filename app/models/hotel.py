from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# Enums
class HotelCategory(str, Enum):
    HOTEL = "hotel"
    APARTMENT = "apartment"
    GUESTHOUSE = "guesthouse"
    VILLA = "villa"
    HOSTEL = "hostel"
    GLAMPING = "glamping"


class HotelStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class HotelSearchRequest(BaseModel):
    query: Optional[str] = Field(
        None, description="Search query for hotel name or location"
    )
    city: Optional[str] = Field(None, description="City to filter hotels")
    category: Optional[HotelCategory] = Field(
        None, description="Hotel category to filter"
    )
    min_price: Optional[float] = Field(None, description="Minimum price per night")
    max_price: Optional[float] = Field(None, description="Maximum price per night")
    min_rating: Optional[float] = Field(None, description="Minimum rating")
    amenities: Optional[List[str]] = Field(
        None, description="List of amenities to filter hotels"
    )
    check_in: Optional[str] = Field(None, description="Check-in date (YYYY-MM-DD)")
    check_out: Optional[str] = Field(None, description="Check-out date (YYYY-MM-DD)")
    guests: Optional[int] = Field(None, description="Number of guests for the booking")
    page: Optional[int] = Field(1, ge=1, description="Page number for pagination")
    limit: Optional[int] = Field(
        10, ge=1, le=100, description="Number of results per page"
    )
    sort_by: Optional[str] = Field("rating", description="Sort by: price, rating, name")
    sort_order: Optional[str] = Field("desc", description="Sort order: asc, desc")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "spa hotel",
                "city": "Warszawa",
                "category": "hotel",
                "min_price": 200,
                "max_price": 1000,
                "min_rating": 4.0,
                "amenities": ["wifi", "spa", "parking"],
                "check_in": "2024-12-25",
                "check_out": "2024-12-28",
                "guests": 2,
                "page": 1,
                "limit": 10,
                "sort_by": "rating",
                "sort_order": "desc",
            }
        }


class HotelCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Hotel name")
    description: Optional[str] = Field(
        None, max_length=2500, description="Hotel description"
    )
    category: HotelCategory = Field(..., description="Hotel category")
    address: str = Field(..., min_length=5, max_length=300, description="Full address")
    city: str = Field(..., min_length=2, max_length=170, description="City name")
    country: str = Field(..., min_length=2, max_length=100, description="Country name")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    price_per_night: float = Field(..., ge=0, description="Base price per night")
    currency: str = Field(
        "PLN", min_length=3, max_length=3, description="Currency code (ISO 4217)"
    )
    max_guests: int = Field(
        2, ge=1, le=20, description="Maximum number of guests per room"
    )
    total_rooms: int = Field(1, ge=1, description="Total number of rooms")
    amenities: Optional[List[str]] = Field(
        None, description="List of amenities offered by the hotel"
    )
    images: List[str] = Field(
        ..., min_length=1, max_length=10, description="List of image URLs"
    )
    contact_phone: Optional[str] = Field(None, description="Contact phone number")
    contact_email: Optional[str] = Field(None, description="Contact email address")
    website: Optional[str] = Field(None, description="Hotel website URL")
    check_in_time: Optional[str] = Field(
        "14:00", description="Default check-in time (HH:MM)"
    )
    check_out_time: Optional[str] = Field(
        "11:00", description="Default check-out time (HH:MM)"
    )
    cancellation_policy: str = Field(
        "Free cancellation up to 24 hours before arrival",
        description="Cancellation policy",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Grand Hotel Warsaw",
                "description": "Luksusowy hotel w sercu Warszawy z widokiem na Wisłę.",
                "category": "hotel",
                "address": "Krakowskie Przedmieście 13, 00-071 Warszawa",
                "city": "Warszawa",
                "country": "Poland",
                "latitude": 52.2394,
                "longitude": 21.0150,
                "price_per_night": 450.00,
                "currency": "PLN",
                "max_guests": 4,
                "total_rooms": 150,
                "amenities": ["wifi", "spa", "parking", "restaurant", "gym", "pool"],
                "images": [
                    "https://example.com/image1.jpg",
                    "https://example.com/image2.jpg",
                ],
                "contact_phone": "+48 22 XXX XXXX",
                "contact_email": "info@grandhotel.pl",
                "website": "https://grandhotel.pl",
                "check_in_time": "15:00",
                "check_out_time": "11:00",
                "cancellation_policy": "Darmowa anulacja do 24 godzin przed przyjazdem",
            }
        }


class HotelUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    category: Optional[HotelCategory] = None
    address: Optional[str] = Field(None, min_length=5, max_length=300)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    country: Optional[str] = Field(None, min_length=2, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    price_per_night: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = None
    max_guests: Optional[int] = Field(None, ge=1, le=20)
    total_rooms: Optional[int] = Field(None, ge=1)
    amenities: Optional[List[str]] = None
    images: Optional[List[str]] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    website: Optional[str] = None
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    cancellation_policy: Optional[str] = None
    status: Optional[HotelStatus] = None


class HotelResponse(BaseModel):
    id: str = Field(..., description="Hotel ID")
    name: str = Field(..., description="Hotel name")
    description: str = Field(..., description="Hotel description")
    category: HotelCategory = Field(..., description="Hotel category")
    address: str = Field(..., description="Full address")
    city: str = Field(..., description="City")
    country: str = Field(..., description="Country")
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")
    price_per_night: float = Field(..., description="Base price per night")
    currency: str = Field(..., description="Currency code")
    max_guests: int = Field(..., description="Maximum guests per room")
    total_rooms: int = Field(..., description="Total number of rooms")
    available_rooms: int = Field(..., description="Currently available rooms")
    amenities: List[str] = Field(..., description="List of amenities")
    images: List[str] = Field(..., description="List of image URLs")
    rating: float = Field(0.0, ge=0, le=5, description="Average rating")
    review_count: int = Field(0, ge=0, description="Number of reviews")
    contact_phone: Optional[str] = Field(None, description="Contact phone number")
    contact_email: Optional[str] = Field(None, description="Contact email")
    website: Optional[str] = Field(None, description="Hotel website")
    check_in_time: str = Field(..., description="Check-in time")
    check_out_time: str = Field(..., description="Check-out time")
    cancellation_policy: str = Field(..., description="Cancellation policy")
    status: HotelStatus = Field(..., description="Hotel status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "hotel123",
                "name": "Grand Hotel Warsaw",
                "description": "Luksusowy hotel w sercu Warszawy z widokiem na Wisłę.",
                "category": "hotel",
                "address": "Krakowskie Przedmieście 13, 00-071 Warszawa",
                "city": "Warszawa",
                "country": "Poland",
                "latitude": 52.2394,
                "longitude": 21.0150,
                "price_per_night": 450.00,
                "currency": "PLN",
                "max_guests": 4,
                "total_rooms": 150,
                "available_rooms": 23,
                "amenities": ["wifi", "spa", "parking", "restaurant"],
                "images": ["https://example.com/image1.jpg"],
                "rating": 4.8,
                "review_count": 1247,
                "contact_phone": "+48 22 XXX XXXX",
                "contact_email": "info@grandhotel.pl",
                "website": "https://grandhotel.pl",
                "check_in_time": "15:00",
                "check_out_time": "11:00",
                "cancellation_policy": "Darmowa anulacja do 24 godzin przed przyjazdem",
                "status": "active",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T14:45:00Z",
            }
        }


class HotelListResponse(BaseModel):
    hotels: List[HotelResponse] = Field(..., description="List of hotels")
    total: int = Field(..., description="Total number of hotels found")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Results per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")

    class Config:
        json_schema_extra = {
            "example": {
                "hotels": [],
                "total": 157,
                "page": 1,
                "limit": 20,
                "total_pages": 8,
                "has_next": True,
                "has_previous": False,
            }
        }


class HotelInDB(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    category: HotelCategory
    address: str
    city: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    price_per_night: float
    currency: str
    max_guests: int
    total_rooms: int
    available_rooms: int
    amenities: List[str]
    images: List[str]
    rating: float = 0.0
    review_count: int = 0
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    website: Optional[str] = None
    check_in_time: str
    check_out_time: str
    cancellation_policy: str
    status: HotelStatus = HotelStatus.ACTIVE
    created_at: datetime
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore"""
        data = self.model_dump()
        data.pop("id", None)  # Firestore handles ID separately
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], doc_id: str = None):
        """Create from Firestore document"""
        if doc_id:
            data["id"] = doc_id
        return cls(**data)

    def to_response(self) -> HotelResponse:
        """Convert to response model"""
        return HotelResponse(**self.model_dump())
