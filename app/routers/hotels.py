from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from app.models.hotel import (
    HotelCreateRequest, HotelUpdateRequest, HotelResponse,
    HotelListResponse, HotelSearchRequest, HotelCategory
)
from app.models.user import UserResponse
from app.services.hotel_service import hotel_service
from app.routers.auth import get_current_user, get_current_admin

router = APIRouter()


@router.post("/", response_model=HotelResponse, status_code=status.HTTP_201_CREATED)
async def create_hotel(
        hotel_data: HotelCreateRequest,
        current_user: UserResponse = Depends(get_current_admin)
):
    """
    Create a new hotel

    - **name**: Hotel name (2-100 characters)
    - **description**: Hotel description (max 2500 characters)
    - **category**: Hotel category (hotel, apartment, guesthouse, villa, hostel, glamping)
    - **address**: Full hotel address
    - **city**: City name
    - **country**: Country name
    - **latitude/longitude**: Geographic coordinates (optional)
    - **price_per_night**: Price per night
    - **currency**: Currency code
    - **max_guests**: Maximum number of guests
    - **total_rooms**: Total number of rooms
    - **amenities**: List of amenities
    - **images**: List of image URLs
    - **contact_phone**: Contact phone (optional)
    - **contact_email**: Contact email (optional)
    - **website**: Website URL (optional)
    - **check_in_time**: Check-in time
    - **check_out_time**: Check-out time
    - **cancellation_policy**: Cancellation policy
    """
    try:
        hotel = await hotel_service.create_hotel(hotel_data)
        return hotel.to_response()

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Niepoprawne dane: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Error creating hotel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas tworzenia hotelu"
        )


@router.get("/search", response_model=HotelListResponse)
async def search_hotels(
        query: Optional[str] = Query(None, description="Search in hotel name or location"),
        city: Optional[str] = Query(None, description="Filter by city"),
        country: Optional[str] = Query(None, description="Filter by country"),
        category: Optional[HotelCategory] = Query(None, description="Filter by category"),
        min_price: Optional[float] = Query(None, ge=0, description="Minimum price per night"),
        max_price: Optional[float] = Query(None, ge=0, description="Maximum price per night"),
        min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
        guests: Optional[int] = Query(None, ge=1, description="Number of guests"),
        check_in: Optional[str] = Query(None, description="Check-in date (YYYY-MM-DD)"),
        check_out: Optional[str] = Query(None, description="Check-out date (YYYY-MM-DD)"),
        sort_order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
        amenities: Optional[List[str]] = Query(None, description="List of required amenities"),
        latitude: Optional[float] = Query(None, ge=-90, le=90, description="Latitude for nearby search"),
        longitude: Optional[float] = Query(None, ge=-180, le=180, description="Longitude for nearby search"),
        radius_km: Optional[float] = Query(None, ge=0, description="Search radius in kilometers"),
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(10, ge=1, le=100, description="Results per page"),
        sort_by: Optional[str] = Query("rating",
                                       description="Sort by: price_asc, price_desc, rating, name, created_at"),
        current_user: UserResponse = Depends(get_current_user)
):
    """
    Search hotels with advanced filters

    **Usage examples:**
    - `/search?city=Warsaw&min_rating=4.0` - Hotels in Warsaw with rating min. 4.0
    - `/search?category=hotel&min_price=200&max_price=500` - Hotels in price range 200-500
    - `/search?latitude=52.2297&longitude=21.0122&radius_km=10` - Hotels within 10km from Warsaw center
    - `/search?amenities=wifi&amenities=spa&amenities=parking` - Hotels with specific amenities
    """
    try:
        search_request = HotelSearchRequest(
            query=query,
            city=city,
            country=country,
            category=category,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            amenities=amenities,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            check_in=check_in,
            check_out=check_out,
            guests=guests
        )

        return await hotel_service.search_hotels(search_request)

    except Exception as e:
        print(f"❌ Error searching hotels: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas wyszukiwania hoteli"
        )


@router.get("/featured", response_model=List[HotelResponse])
async def get_featured_hotels(
        limit: int = Query(6, ge=1, le=20, description="Number of featured hotels"),
        current_user: UserResponse = Depends(get_current_user)
):
    """
    Get featured hotels (highest rated)

    Returns a list of best rated active hotels
    """
    try:
        hotels = await hotel_service.get_featured_hotels(limit)
        return hotels

    except Exception as e:
        print(f"❌ Error getting featured hotels: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas pobierania polecanych hoteli"
        )


@router.get("/nearby", response_model=List[HotelResponse])
async def get_nearby_hotels(
        latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
        longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
        radius_km: float = Query(10.0, ge=0.1, le=100, description="Search radius in kilometers"),
        limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
        current_user: UserResponse = Depends(get_current_user)
):
    """
    Find hotels near specific coordinates

    **Usage example:**
    - `/nearby?latitude=52.2297&longitude=21.0122&radius_km=5` - Hotels within 5km from Warsaw center
    """
    try:
        hotels = await hotel_service.get_hotels_near_location(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            limit=limit
        )
        return hotels

    except Exception as e:
        print(f"❌ Error searching nearby hotels: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas wyszukiwania hoteli w pobliżu"
        )


@router.get("/city/{city}", response_model=List[HotelResponse])
async def get_hotels_by_city(
        city: str,
        limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
        current_user: UserResponse = Depends(get_current_user)
):
    """
    Get hotels from a specific city

    **Usage example:**
    - `/city/Warsaw?limit=15` - First 15 hotels from Warsaw
    """
    try:
        hotels = await hotel_service.get_hotels_by_city(city, limit)
        return hotels

    except Exception as e:
        print(f"❌ Error getting hotels from city {city}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas pobierania hoteli z miasta {city}"
        )


@router.get("/category/{category}", response_model=List[HotelResponse])
async def get_hotels_by_category(
        category: HotelCategory,
        limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
        current_user: UserResponse = Depends(get_current_user)
):
    """
    Get hotels by category

    **Available categories:**
    - `hotel` - Hotels
    - `apartment` - Apartments
    - `guesthouse` - Guesthouses
    - `villa` - Villas
    - `hostel` - Hostels
    - `glamping` - Glamping
    """
    try:
        hotels = await hotel_service.get_hotels_by_category(category, limit)
        return hotels

    except Exception as e:
        print(f"❌ Error getting hotels by category {category}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas pobierania hoteli w kategorii {category.value}"
        )


@router.get("/statistics")
async def get_hotel_statistics(
        current_user: UserResponse = Depends(get_current_admin)
):
    """
    Get hotel statistics

    Returns general statistics for all hotels in the system:
    - Total number of hotels
    - Total number of rooms
    - Average rating
    - Distribution by category
    """
    try:
        stats = await hotel_service.get_hotel_statistics()
        return stats

    except Exception as e:
        print(f"❌ Error getting hotel statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas pobierania statystyk hoteli"
        )


@router.get("/{hotel_id}", response_model=HotelResponse)
async def get_hotel_by_id(hotel_id: str, current_user: UserResponse = Depends(get_current_user)):
    """
    Get hotel details by ID

    **Parameters:**
    - **hotel_id**: Unique hotel identifier
    """
    try:
        hotel = await hotel_service.get_hotel_by_id(hotel_id)

        if not hotel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hotel nie znaleziony"
            )

        return hotel.to_response()

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting hotel {hotel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas pobierania hotelu"
        )


@router.put("/{hotel_id}", response_model=HotelResponse)
async def update_hotel(
        hotel_id: str,
        hotel_data: HotelUpdateRequest,
        current_user: UserResponse = Depends(get_current_admin)
):
    """
    Update hotel information

    **Parameters:**
    - **hotel_id**: Unique hotel identifier
    - **hotel_data**: Data to update (only provided fields will be updated)
    """
    try:
        # Check if hotel exists
        existing_hotel = await hotel_service.get_hotel_by_id(hotel_id)
        if not existing_hotel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hotel nie znaleziony"
            )

        # Update hotel
        updated_hotel = await hotel_service.update_hotel(hotel_id, hotel_data)

        if not updated_hotel:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Błąd podczas aktualizacji hotelu"
            )

        return updated_hotel.to_response()

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Error updating hotel {hotel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas aktualizacji hotelu"
        )


@router.delete("/{hotel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hotel(
        hotel_id: str,
        current_user: UserResponse = Depends(get_current_admin)
):
    """
    Delete hotel (deactivation)

    **Parameters:**
    - **hotel_id**: Unique hotel identifier
    """
    try:
        # Check if hotel exists
        existing_hotel = await hotel_service.get_hotel_by_id(hotel_id)
        if not existing_hotel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hotel nie znaleziony"
            )

        # Delete hotel
        success = await hotel_service.delete_hotel(hotel_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Błąd podczas usuwania hotelu"
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting hotel {hotel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas usuwania hotelu"
        )


@router.patch("/{hotel_id}/availability")
async def update_hotel_availability(
        hotel_id: str,
        available_rooms: int = Query(..., ge=0, description="Number of available rooms"),
        current_user: UserResponse = Depends(get_current_admin)
):
    """
    Update hotel room availability

    **Parameters:**
    - **hotel_id**: Unique hotel identifier
    - **available_rooms**: New number of available rooms
    """
    try:
        # Check if hotel exists
        existing_hotel = await hotel_service.get_hotel_by_id(hotel_id)
        if not existing_hotel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hotel nie znaleziony"
            )

        # Update availability
        success = await hotel_service.update_hotel_availability(hotel_id, available_rooms)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Błąd podczas aktualizacji dostępności hotelu"
            )

        return {"message": "Dostępność hotelu zaktualizowana pomyślnie"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating hotel availability {hotel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas aktualizacji dostępności hotelu"
        )


@router.patch("/{hotel_id}/rating")
async def update_hotel_rating(
        hotel_id: str,
        rating: float = Query(..., ge=0, le=5, description="New hotel rating"),
        review_count: int = Query(..., ge=0, description="Number of reviews"),
        current_user: UserResponse = Depends(get_current_admin)
):
    """
    Update hotel rating and review count

    **Parameters:**
    - **hotel_id**: Unique hotel identifier
    - **rating**: New average rating (0-5)
    - **review_count**: Total number of reviews
    """
    try:
        # Check if hotel exists
        existing_hotel = await hotel_service.get_hotel_by_id(hotel_id)
        if not existing_hotel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hotel nie znaleziony"
            )

        # Update rating
        success = await hotel_service.update_hotel_rating(hotel_id, rating, review_count)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Błąd podczas aktualizacji oceny hotelu"
            )

        return {"message": "Ocena hotelu zaktualizowana pomyślnie"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating hotel rating {hotel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas aktualizacji oceny hotelu"
        )