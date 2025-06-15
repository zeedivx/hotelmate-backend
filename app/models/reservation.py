from datetime import datetime, date
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


# Enums
class ReservationStatus(str, Enum):
    PENDING = "pending"  # Oczekująca na potwierdzenie
    CONFIRMED = "confirmed"  # Potwierdzona
    CHECKED_IN = "checked_in"  # Zameldowany
    CHECKED_OUT = "checked_out"  # Wymeldowany
    CANCELLED = "cancelled"  # Anulowana
    NO_SHOW = "no_show"  # Nie stawił się


class PaymentStatus(str, Enum):
    PENDING = "pending"  # Oczekująca
    PAID = "paid"  # Opłacona
    PARTIALLY_PAID = "partially_paid"  # Częściowo opłacona
    REFUNDED = "refunded"  # Zwrócona
    FAILED = "failed"  # Nieudana


class ReservationCreateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "hotel_id": "hotel123",
                "check_in_date": "2024-12-25",
                "check_out_date": "2024-12-28",
                "guests": 2,
                "rooms": 1,
                "guest_name": "Jan Kowalski",
                "guest_email": "jan@example.com",
                "guest_phone": "+48 123 456 789",
                "special_requests": "Late check-in requested",
            }
        }
    )

    hotel_id: str = Field(..., description="Hotel ID")
    check_in_date: date = Field(..., description="Check-in date")
    check_out_date: date = Field(..., description="Check-out date")
    guests: int = Field(..., ge=1, le=10, description="Number of guests")
    rooms: int = Field(1, ge=1, le=5, description="Number of rooms")
    guest_name: str = Field(
        ..., min_length=2, max_length=100, description="Guest full name"
    )
    guest_email: str = Field(..., description="Guest email address")
    guest_phone: str = Field(..., description="Guest phone number")
    special_requests: Optional[str] = Field(
        None, max_length=500, description="Special requests or notes"
    )

    @field_validator("check_in_date")
    @classmethod
    def validate_check_in_date(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Check-in date cannot be in the past")
        return v

    @field_validator("check_out_date")
    @classmethod
    def validate_check_out_date(cls, v: date, info) -> date:
        # Access other field values through info.data
        if hasattr(info, "data") and "check_in_date" in info.data:
            check_in_date = info.data["check_in_date"]
            if v <= check_in_date:
                raise ValueError("Check-out date must be after check-in date")
        return v


class ReservationUpdateRequest(BaseModel):
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    guests: Optional[int] = Field(None, ge=1, le=10)
    rooms: Optional[int] = Field(None, ge=1, le=5)
    guest_name: Optional[str] = Field(None, min_length=2, max_length=100)
    guest_email: Optional[str] = None
    guest_phone: Optional[str] = None
    special_requests: Optional[str] = Field(None, max_length=500)
    status: Optional[ReservationStatus] = None

    @field_validator("check_out_date")
    @classmethod
    def validate_check_out_date(cls, v: Optional[date], info) -> Optional[date]:
        if v is None:
            return v

        if hasattr(info, "data") and "check_in_date" in info.data:
            check_in_date = info.data["check_in_date"]
            if check_in_date and v <= check_in_date:
                raise ValueError("Check-out date must be after check-in date")
        return v


class ReservationSearchRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "confirmed",
                "check_in_from": "2024-12-01",
                "check_in_to": "2024-12-31",
                "page": 1,
                "limit": 10,
                "sort_by": "check_in_date",
                "sort_order": "asc",
            }
        }
    )

    user_id: Optional[str] = Field(None, description="Filter by user ID")
    hotel_id: Optional[str] = Field(None, description="Filter by hotel ID")
    status: Optional[ReservationStatus] = Field(None, description="Filter by status")
    check_in_from: Optional[date] = Field(None, description="Check-in date from")
    check_in_to: Optional[date] = Field(None, description="Check-in date to")
    guest_email: Optional[str] = Field(None, description="Filter by guest email")
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Results per page")
    sort_by: Optional[str] = Field(
        "created_at", description="Sort by: created_at, check_in_date, total_price"
    )
    sort_order: Optional[str] = Field("desc", description="Sort order: asc, desc")


class ReservationResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "reservation123",
                "user_id": "user123",
                "hotel_id": "hotel123",
                "hotel_name": "Grand Hotel Warsaw",
                "hotel_address": "Krakowskie Przedmieście 13, Warszawa",
                "hotel_city": "Warszawa",
                "check_in_date": "2024-12-25",
                "check_out_date": "2024-12-28",
                "nights": 3,
                "guests": 2,
                "rooms": 1,
                "guest_name": "Jan Kowalski",
                "guest_email": "jan@example.com",
                "guest_phone": "+48 123 456 789",
                "special_requests": "Late check-in requested",
                "price_per_night": 450.00,
                "total_price": 1350.00,
                "currency": "PLN",
                "status": "confirmed",
                "payment_status": "paid",
                "confirmation_number": "HM123456789",
                "created_at": "2024-12-01T10:30:00Z",
                "updated_at": "2024-12-01T10:35:00Z",
                "cancelled_at": None,
                "cancellation_reason": None,
            }
        }
    )

    id: str = Field(..., description="Reservation ID")
    user_id: str = Field(..., description="User ID who made the reservation")
    hotel_id: str = Field(..., description="Hotel ID")
    hotel_name: str = Field(..., description="Hotel name")
    hotel_address: str = Field(..., description="Hotel address")
    hotel_city: str = Field(..., description="Hotel city")
    check_in_date: date = Field(..., description="Check-in date")
    check_out_date: date = Field(..., description="Check-out date")
    nights: int = Field(..., description="Number of nights")
    guests: int = Field(..., description="Number of guests")
    rooms: int = Field(..., description="Number of rooms")
    guest_name: str = Field(..., description="Guest full name")
    guest_email: str = Field(..., description="Guest email address")
    guest_phone: str = Field(..., description="Guest phone number")
    special_requests: Optional[str] = Field(
        None, description="Special requests or notes"
    )
    price_per_night: float = Field(..., description="Price per night")
    total_price: float = Field(..., description="Total price for the stay")
    currency: str = Field(..., description="Currency code")
    status: ReservationStatus = Field(..., description="Reservation status")
    payment_status: PaymentStatus = Field(..., description="Payment status")
    confirmation_number: str = Field(..., description="Unique confirmation number")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    cancelled_at: Optional[datetime] = Field(None, description="Cancellation timestamp")
    cancellation_reason: Optional[str] = Field(None, description="Cancellation reason")


class ReservationInDB(BaseModel):
    id: Optional[str] = None
    user_id: str
    hotel_id: str
    hotel_name: str
    hotel_address: str
    hotel_city: str
    check_in_date: date
    check_out_date: date
    nights: int
    guests: int
    rooms: int
    guest_name: str
    guest_email: str
    guest_phone: str
    special_requests: Optional[str] = None
    price_per_night: float
    total_price: float
    currency: str
    status: ReservationStatus = ReservationStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    confirmation_number: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore"""
        data = self.model_dump()
        data.pop("id", None)

        # Convert dates to strings for Firestore
        if isinstance(data.get("check_in_date"), date):
            data["check_in_date"] = data["check_in_date"].isoformat()
        if isinstance(data.get("check_out_date"), date):
            data["check_out_date"] = data["check_out_date"].isoformat()

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], doc_id: str = None):
        """Create from Firestore document"""
        if doc_id:
            data["id"] = doc_id

        # Convert string dates back to date objects
        if isinstance(data.get("check_in_date"), str):
            data["check_in_date"] = date.fromisoformat(data["check_in_date"])
        if isinstance(data.get("check_out_date"), str):
            data["check_out_date"] = date.fromisoformat(data["check_out_date"])

        return cls(**data)

    def to_response(self) -> ReservationResponse:
        """Convert to response model"""
        return ReservationResponse(**self.model_dump())


class ReservationStatsResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_reservations": 1247,
                "confirmed_reservations": 856,
                "pending_reservations": 23,
                "cancelled_reservations": 368,
                "total_revenue": 567890.50,
                "average_stay_length": 2.8,
                "occupancy_rate": 67.3,
            }
        }
    )

    total_reservations: int = Field(..., description="Total number of reservations")
    confirmed_reservations: int = Field(
        ..., description="Number of confirmed reservations"
    )
    pending_reservations: int = Field(..., description="Number of pending reservations")
    cancelled_reservations: int = Field(
        ..., description="Number of cancelled reservations"
    )
    total_revenue: float = Field(..., description="Total revenue from all reservations")
    average_stay_length: float = Field(..., description="Average stay length in nights")
    occupancy_rate: float = Field(..., description="Current occupancy rate percentage")
