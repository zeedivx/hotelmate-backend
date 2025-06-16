from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import math

from google.cloud import firestore

from app.models.hotel import (
    HotelInDB, HotelCreateRequest, HotelUpdateRequest,
    HotelSearchRequest, HotelResponse, HotelListResponse,
    HotelCategory, HotelStatus
)
from app.services.firebase_service import firebase_service
from app.config import settings


class HotelService:

    @staticmethod
    async def create_hotel(hotel_data: HotelCreateRequest) -> HotelInDB:
        """Create a new hotel"""
        try:
            # Create hotel object
            hotel_in_db = HotelInDB(
                name=hotel_data.name,
                description=hotel_data.description,
                category=hotel_data.category,
                address=hotel_data.address,
                city=hotel_data.city,
                country=hotel_data.country,
                latitude=hotel_data.latitude,
                longitude=hotel_data.longitude,
                price_per_night=hotel_data.price_per_night,
                currency=hotel_data.currency,
                max_guests=hotel_data.max_guests,
                total_rooms=hotel_data.total_rooms,
                available_rooms=hotel_data.total_rooms,
                amenities=hotel_data.amenities,
                images=hotel_data.images,
                contact_phone=hotel_data.contact_phone,
                contact_email=hotel_data.contact_email,
                website=hotel_data.website,
                check_in_time=hotel_data.check_in_time,
                check_out_time=hotel_data.check_out_time,
                cancellation_policy=hotel_data.cancellation_policy,
                status=HotelStatus.ACTIVE,
                created_at=datetime.now(timezone.utc)
            )

            # Save to Firestore
            hotel_id = await firebase_service.create_document(
                settings.HOTELS_COLLECTION,
                hotel_in_db.to_dict()
            )

            hotel_in_db.id = hotel_id
            return hotel_in_db

        except Exception as e:
            print(f"❌ Error creating hotel: {e}")
            raise e

    @staticmethod
    async def get_hotel_by_id(hotel_id: str) -> Optional[HotelInDB]:
        """Get hotel by ID"""
        try:
            hotel_data = await firebase_service.get_document(
                settings.HOTELS_COLLECTION,
                hotel_id
            )

            if not hotel_data:
                return None

            return HotelInDB.from_dict(hotel_data, hotel_id)

        except Exception as e:
            print(f"❌ Error getting hotel {hotel_id}: {e}")
            return None

    @staticmethod
    async def update_hotel(hotel_id: str, hotel_data: HotelUpdateRequest) -> Optional[HotelInDB]:
        """Update hotel information"""
        try:
            # Get existing hotel
            existing_hotel = await HotelService.get_hotel_by_id(hotel_id)
            if not existing_hotel:
                return None

            # Prepare update data (only non-None fields)
            update_data = {}
            for field, value in hotel_data.dict(exclude_unset=True).items():
                if value is not None:
                    update_data[field] = value

            # Add update timestamp
            update_data['updated_at'] = datetime.now(timezone.utc)

            # Update in Firestore
            await firebase_service.update_document(
                settings.HOTELS_COLLECTION,
                hotel_id,
                update_data
            )

            # Return updated hotel
            return await HotelService.get_hotel_by_id(hotel_id)

        except Exception as e:
            print(f"❌ Error updating hotel {hotel_id}: {e}")
            return None

    @staticmethod
    async def delete_hotel(hotel_id: str) -> bool:
        """Delete hotel (soft delete by setting status to inactive)"""
        try:
            update_data = {
                'status': HotelStatus.INACTIVE,
                'updated_at': datetime.now(timezone.utc)
            }

            await firebase_service.update_document(
                settings.HOTELS_COLLECTION,
                hotel_id,
                update_data
            )
            return True

        except Exception as e:
            print(f"❌ Error deleting hotel {hotel_id}: {e}")
            return False

    @staticmethod
    async def search_hotels(search_request: HotelSearchRequest) -> HotelListResponse:
        """Search hotels with filters and pagination"""
        try:
            # Build query
            collection = firebase_service.get_hotels_collection()
            query = collection.where('status', '==', HotelStatus.ACTIVE.value)

            # Apply filters
            if search_request.city:
                query = query.where('city', '==', search_request.city)

            if search_request.country:
                query = query.where('country', '==', search_request.country)

            if search_request.category:
                query = query.where('category', '==', search_request.category.value)

            if search_request.min_price:
                query = query.where('price_per_night', '>=', search_request.min_price)

            if search_request.max_price:
                query = query.where('price_per_night', '<=', search_request.max_price)

            if search_request.min_rating:
                query = query.where('rating', '>=', search_request.min_rating)

            # Apply sorting
            if search_request.sort_by == 'price_asc':
                query = query.order_by('price_per_night')
            elif search_request.sort_by == 'price_desc':
                query = query.order_by('price_per_night', direction=firestore.Query.DESCENDING)
            elif search_request.sort_by == 'rating':
                query = query.order_by('rating', direction=firestore.Query.DESCENDING)
            elif search_request.sort_by == 'name':
                query = query.order_by('name')
            else:  # Default: created_at desc
                query = query.order_by('created_at', direction=firestore.Query.DESCENDING)

            # Get total count for pagination
            total_results = len((query.get()))

            # Apply pagination
            if search_request.page and search_request.limit:
                offset = (search_request.page - 1) * search_request.limit
                query = query.offset(offset).limit(search_request.limit)

            # Execute query
            docs = query.get()
            hotels = []

            for doc in docs:
                hotel_data = doc.to_dict()
                hotel = HotelInDB.from_dict(hotel_data, doc.id)

                if search_request.amenities:
                    if not all(amenity in hotel.amenities for amenity in search_request.amenities):
                        continue

                # Apply location-based filtering if coordinates provided
                if (search_request.latitude and search_request.longitude and
                        search_request.radius_km and hotel.latitude and hotel.longitude):

                    distance = HotelService._calculate_distance(
                        search_request.latitude, search_request.longitude,
                        hotel.latitude, hotel.longitude
                    )

                    if distance > search_request.radius_km:
                        continue

                hotels.append(hotel.to_response())

            # Calculate pagination info
            total_pages = math.ceil(total_results / search_request.limit) if search_request.limit else 1

            return HotelListResponse(
                hotels=hotels,
                total=len(hotels),
                page=search_request.page or 1,
                limit=search_request.limit or len(hotels),
                total_pages=total_pages,
                has_next=search_request.page < total_pages if search_request.page else False,
                has_previous=search_request.page > 1 if search_request.page else False
            )

        except Exception as e:
            print(f"❌ Error during hotel search: {e}")
            return HotelListResponse(hotels=[], total=0, page=1, limit=10, total_pages=0, has_next=False, has_previous=False)

    @staticmethod
    async def get_hotels_by_city(city: str, limit: int = 10) -> List[HotelResponse]:
        """Get hotels by city"""
        try:
            collection = firebase_service.get_hotels_collection()
            query = (collection
                     .where('city', '==', city)
                     .where('status', '==', HotelStatus.ACTIVE.value)
                     .limit(limit))

            docs = query.get()
            hotels = []

            for doc in docs:
                hotel_data = doc.to_dict()
                hotel = HotelInDB.from_dict(hotel_data, doc.id)
                hotels.append(hotel.to_response())

            return hotels

        except Exception as e:
            print(f"❌ Error getting hotels in city {city}: {e}")
            return []

    @staticmethod
    async def get_hotels_by_category(category: HotelCategory, limit: int = 10) -> List[HotelResponse]:
        """Get hotels by category"""
        try:
            collection = firebase_service.get_hotels_collection()
            query = (collection
                     .where('category', '==', category.value)
                     .where('status', '==', HotelStatus.ACTIVE.value)
                     .limit(limit))

            docs = query.get()
            print(f"🔥 Found {len(docs)} hotels in category {category.value}")
            hotels = []

            for doc in docs:
                hotel_data = doc.to_dict()
                hotel = HotelInDB.from_dict(hotel_data, doc.id)
                hotels.append(hotel.to_response())

            return hotels

        except Exception as e:
            print(f"❌ Error getting hotels in category {category.value}: {e}")
            return []

    @staticmethod
    async def get_featured_hotels(limit: int = 6) -> List[HotelResponse]:
        """Get featured hotels (highest rated)"""
        try:
            collection = firebase_service.get_hotels_collection()
            query = (collection
                     .where('status', '==', HotelStatus.ACTIVE.value)
                     .order_by('rating', direction=firestore.Query.DESCENDING)
                     .limit(limit))

            docs = query.get()
            hotels = []

            for doc in docs:
                hotel_data = doc.to_dict()
                hotel = HotelInDB.from_dict(hotel_data, doc.id)
                hotels.append(hotel.to_response())

            return hotels

        except Exception as e:
            print(f"❌ Error getting featured hotels: {e}")
            return []

    @staticmethod
    async def update_hotel_availability(hotel_id: str, available_rooms: int) -> bool:
        """Update hotel room availability"""
        try:
            update_data = {
                'available_rooms': available_rooms,
                'updated_at': datetime.now(timezone.utc)
            }

            await firebase_service.update_document(
                settings.HOTELS_COLLECTION,
                hotel_id,
                update_data
            )
            return True

        except Exception as e:
            print(f"❌ Error updating availability for hotel {hotel_id}: {e}")
            return False

    @staticmethod
    async def update_hotel_rating(hotel_id: str, new_rating: float, review_count: int) -> bool:
        """Update hotel rating and review count"""
        try:
            update_data = {
                'rating': round(new_rating, 1),
                'review_count': review_count,
                'updated_at': datetime.now(timezone.utc)
            }

            await firebase_service.update_document(
                settings.HOTELS_COLLECTION,
                hotel_id,
                update_data
            )
            return True

        except Exception as e:
            print(f"❌ Error updating rating for hotel {hotel_id}: {e}")
            return False

    @staticmethod
    async def get_hotels_near_location(
            latitude: float,
            longitude: float,
            radius_km: float = 10.0,
            limit: int = 20
    ) -> List[HotelResponse]:
        """Get hotels near specific coordinates"""
        try:
            # Get all active hotels (we'll filter by distance in memory)
            collection = firebase_service.get_hotels_collection()
            query = collection.where('status', '==', HotelStatus.ACTIVE.value)

            docs = await query.get()
            nearby_hotels = []

            for doc in docs:
                hotel_data = doc.to_dict()
                hotel = HotelInDB.from_dict(hotel_data, doc.id)

                # Skip hotels without coordinates
                if not hotel.latitude or not hotel.longitude:
                    continue

                # Calculate distance
                distance = HotelService._calculate_distance(
                    latitude, longitude,
                    hotel.latitude, hotel.longitude
                )

                # Check if within radius
                if distance <= radius_km:
                    hotel_response = hotel.to_response()
                    # Add distance to the response for sorting
                    hotel_dict = hotel_response.dict()
                    hotel_dict['distance_km'] = round(distance, 2)
                    nearby_hotels.append((distance, hotel_response))

            # Sort by distance and limit results
            nearby_hotels.sort(key=lambda x: x[0])
            return [hotel for _, hotel in nearby_hotels[:limit]]

        except Exception as e:
            print(f"❌ Error getting hotels near location ({latitude}, {longitude}): {e}")
            return []

    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        # Earth radius in kilometers
        r = 6371

        return c * r

    @staticmethod
    async def get_hotel_statistics() -> Dict[str, Any]:
        """Get general hotel statistics"""
        try:
            collection = firebase_service.get_hotels_collection()

            # Count all hotels
            all_hotels_query = collection.where('status', '==', HotelStatus.ACTIVE.value)
            all_hotels = await all_hotels_query.get()
            total_hotels = len(all_hotels)

            # Calculate average rating
            total_rating = 0
            rated_hotels = 0
            total_rooms = 0

            for doc in all_hotels:
                hotel_data = doc.to_dict()
                if hotel_data.get('rating', 0) > 0:
                    total_rating += hotel_data['rating']
                    rated_hotels += 1
                total_rooms += hotel_data.get('total_rooms', 0)

            average_rating = round(total_rating / rated_hotels, 2) if rated_hotels > 0 else 0

            # Count by category
            categories_count = {}
            for category in HotelCategory:
                category_query = collection.where('category', '==', category.value)
                category_docs = await category_query.get()
                categories_count[category.value] = len(category_docs)

            return {
                'total_hotels': total_hotels,
                'total_rooms': total_rooms,
                'average_rating': average_rating,
                'categories_distribution': categories_count
            }

        except Exception as e:
            print(f"❌ Error getting hotel statistics: {e}")
            return {
                'total_hotels': 0,
                'total_rooms': 0,
                'average_rating': 0,
                'categories_distribution': {}
            }


# Create service instance
hotel_service = HotelService()