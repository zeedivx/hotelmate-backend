from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from app.models.reservation import (
    ReservationCreateRequest, ReservationUpdateRequest, ReservationResponse,
    ReservationSearchRequest, ReservationStatsResponse, ReservationStatus, PaymentStatus
)
from app.models.user import UserResponse
from app.services.reservation_service import reservation_service
from app.routers.auth import get_current_user, get_current_admin

router = APIRouter()


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(
        reservation_data: ReservationCreateRequest,
        current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new reservation

    - **hotel_id**: Hotel ID
    - **check_in_date**: Check-in date (YYYY-MM-DD)
    - **check_out_date**: Check-out date (YYYY-MM-DD)
    - **guests**: Number of guests (1-10)
    - **rooms**: Number of rooms (1-5)
    - **guest_name**: Guest full name
    - **guest_email**: Guest email address
    - **guest_phone**: Guest phone number
    - **special_requests**: Special requests (optional)
    """
    try:
        reservation = await reservation_service.create_reservation(reservation_data, current_user.id)
        return reservation.to_response()

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Niepoprawne dane: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Error creating reservation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas tworzenia rezerwacji"
        )


@router.get("/search")
async def search_reservations(
        user_id: Optional[str] = Query(None, description="Filter by user ID"),
        hotel_id: Optional[str] = Query(None, description="Filter by hotel ID"),
        status_filter: Optional[ReservationStatus] = Query(None, description="Filter by status"),
        check_in_from: Optional[str] = Query(None, description="Check-in date from (YYYY-MM-DD)"),
        check_in_to: Optional[str] = Query(None, description="Check-in date to (YYYY-MM-DD)"),
        guest_email: Optional[str] = Query(None, description="Filter by guest email"),
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(20, ge=1, le=100, description="Results per page"),
        sort_by: Optional[str] = Query("created_at", description="Sort by: created_at, check_in_date, total_price"),
        sort_order: Optional[str] = Query("desc", description="Sort order: asc, desc"),
        current_user: UserResponse = Depends(get_current_admin)
):
    """
    Search reservations with advanced filters

    **Usage examples:**
    - `/search?status=confirmed&check_in_from=2024-12-01` - Confirmed reservations from December 2024
    - `/search?hotel_id=hotel123&sort_by=check_in_date` - Reservations for specific hotel
    - `/search?guest_email=jan@example.com` - Reservations for specific guest
    """
    try:
        from datetime import date

        # Convert string dates to date objects
        check_in_from_date = None
        check_in_to_date = None

        if check_in_from:
            check_in_from_date = date.fromisoformat(check_in_from)
        if check_in_to:
            check_in_to_date = date.fromisoformat(check_in_to)

        search_request = ReservationSearchRequest(
            user_id=user_id,
            hotel_id=hotel_id,
            status=status_filter,
            check_in_from=check_in_from_date,
            check_in_to=check_in_to_date,
            guest_email=guest_email,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return await reservation_service.search_reservations(search_request)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Niepoprawne dane: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Error searching reservations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas wyszukiwania rezerwacji"
        )


@router.get("/my", response_model=List[ReservationResponse])
async def get_my_reservations(
        limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
        current_user: UserResponse = Depends(get_current_user)
):
    """
    Get current user's reservations

    Returns list of reservations for the authenticated user, ordered by creation date (newest first)
    """
    try:
        reservations = await reservation_service.get_user_reservations(current_user.id, limit)
        return reservations

    except Exception as e:
        print(f"❌ Error getting user reservations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas pobierania rezerwacji"
        )


@router.get("/confirmation/{confirmation_number}", response_model=ReservationResponse)
async def get_reservation_by_confirmation(
        confirmation_number: str,
        current_user: UserResponse = Depends(get_current_user)
):
    """
    Get reservation by confirmation number

    **Parameters:**
    - **confirmation_number**: Unique confirmation number
    """
    try:
        reservation = await reservation_service.get_reservation_by_confirmation(confirmation_number)

        if not reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rezerwacja nie została znaleziona"
            )

        # Check if user owns this reservation or is admin
        if reservation.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Brak dostępu do tej rezerwacji"
            )

        return reservation.to_response()

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting reservation by confirmation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas pobierania rezerwacji"
        )


@router.get("/statistics", response_model=ReservationStatsResponse)
async def get_reservation_statistics(
        current_user: UserResponse = Depends(get_current_admin)
):
    """
    Get reservation statistics

    Returns comprehensive statistics for all reservations:
    - Total number of reservations by status
    - Total revenue from confirmed reservations
    - Average stay length
    - Current occupancy rate
    """
    try:
        stats = await reservation_service.get_reservation_statistics()
        return stats

    except Exception as e:
        print(f"❌ Error getting reservation statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas pobierania statystyk rezerwacji"
        )


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation_by_id(
        reservation_id: str,
        current_user: UserResponse = Depends(get_current_user)
):
    """
    Get reservation details by ID

    **Parameters:**
    - **reservation_id**: Unique reservation identifier
    """
    try:
        reservation = await reservation_service.get_reservation_by_id(reservation_id)

        if not reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rezerwacja nie została znaleziona"
            )

        # Check if user owns this reservation or is admin
        if reservation.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Brak dostępu do tej rezerwacji"
            )

        return reservation.to_response()

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting reservation {reservation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas pobierania rezerwacji"
        )


@router.put("/{reservation_id}", response_model=ReservationResponse)
async def update_reservation(
        reservation_id: str,
        reservation_data: ReservationUpdateRequest,
        current_user: UserResponse = Depends(get_current_user)
):
    """
    Update reservation details

    **Parameters:**
    - **reservation_id**: Unique reservation identifier
    - **reservation_data**: Data to update (only provided fields will be updated)
    """
    try:
        # Check if reservation exists and user has access
        existing_reservation = await reservation_service.get_reservation_by_id(reservation_id)
        if not existing_reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rezerwacja nie została znaleziona"
            )

        # Check permissions
        if existing_reservation.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Brak dostępu do tej rezerwacji"
            )

        # Non-admin users can't change status
        if not current_user.is_admin and reservation_data.status is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Brak uprawnień do zmiany statusu rezerwacji"
            )

        # Update reservation
        updated_reservation = await reservation_service.update_reservation(reservation_id, reservation_data)

        if not updated_reservation:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Błąd podczas aktualizacji rezerwacji"
            )

        return updated_reservation.to_response()

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Niepoprawne dane: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Error updating reservation {reservation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas aktualizacji rezerwacji"
        )


@router.patch("/{reservation_id}/cancel")
async def cancel_reservation(
        reservation_id: str,
        cancellation_reason: Optional[str] = Query(None, description="Reason for cancellation"),
        current_user: UserResponse = Depends(get_current_user)
):
    """
    Cancel a reservation

    **Parameters:**
    - **reservation_id**: Unique reservation identifier
    - **cancellation_reason**: Optional reason for cancellation
    """
    try:
        # Check if reservation exists and user has access
        existing_reservation = await reservation_service.get_reservation_by_id(reservation_id)
        if not existing_reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rezerwacja nie została znaleziona"
            )

        # Check permissions
        if existing_reservation.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Brak dostępu do tej rezerwacji"
            )

        # Cancel reservation
        success = await reservation_service.cancel_reservation(
            reservation_id,
            cancellation_reason or "Anulowana przez użytkownika"
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Błąd podczas anulowania rezerwacji"
            )

        return {"message": "Rezerwacja została pomyślnie anulowana"}

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Niepoprawne dane: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Error cancelling reservation {reservation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas anulowania rezerwacji"
        )


@router.patch("/{reservation_id}/check-in")
async def check_in_reservation(
        reservation_id: str,
        current_user: UserResponse = Depends(get_current_admin)
):
    """
    Check in a reservation

    **Parameters:**
    - **reservation_id**: Unique reservation identifier
    """
    try:
        # Check if reservation exists
        existing_reservation = await reservation_service.get_reservation_by_id(reservation_id)
        if not existing_reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rezerwacja nie została znaleziona"
            )

        # Check in reservation
        success = await reservation_service.check_in_reservation(reservation_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Błąd podczas zameldowania"
            )

        return {"message": "Gość został pomyślnie zameldowany"}

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Niepoprawne dane: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Error checking in reservation {reservation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas zameldowania"
        )


@router.patch("/{reservation_id}/check-out")
async def check_out_reservation(
        reservation_id: str,
        current_user: UserResponse = Depends(get_current_admin)
):
    """
    Check out a reservation

    **Parameters:**
    - **reservation_id**: Unique reservation identifier
    """
    try:
        # Check if reservation exists
        existing_reservation = await reservation_service.get_reservation_by_id(reservation_id)
        if not existing_reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rezerwacja nie została znaleziona"
            )

        # Check out reservation
        success = await reservation_service.check_out_reservation(reservation_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Błąd podczas wymeldowania"
            )

        return {"message": "Gość został pomyślnie wymeldowany"}

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Niepoprawne dane: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Error checking out reservation {reservation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas wymeldowania"
        )


@router.patch("/{reservation_id}/payment-status")
async def update_payment_status(
        reservation_id: str,
        payment_status: PaymentStatus = Query(..., description="New payment status"),
        current_user: UserResponse = Depends(get_current_admin)
):
    """
    Update payment status of a reservation

    **Parameters:**
    - **reservation_id**: Unique reservation identifier
    - **payment_status**: New payment status (pending, paid, partially_paid, refunded, failed)
    """
    try:
        # Check if reservation exists
        existing_reservation = await reservation_service.get_reservation_by_id(reservation_id)
        if not existing_reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rezerwacja nie została znaleziona"
            )

        # Update payment status
        success = await reservation_service.update_payment_status(reservation_id, payment_status)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Błąd podczas aktualizacji statusu płatności"
            )

        return {"message": "Status płatności został pomyślnie zaktualizowany"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating payment status for reservation {reservation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas aktualizacji statusu płatności"
        )