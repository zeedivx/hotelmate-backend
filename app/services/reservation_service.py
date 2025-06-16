import math
import secrets
from datetime import datetime, UTC, date
from typing import Optional, Dict, Any, List

from app.config import settings
from app.models.reservation import ReservationCreateRequest, ReservationInDB, ReservationSearchRequest, \
    ReservationResponse, ReservationUpdateRequest, ReservationStatus, PaymentStatus, ReservationStatsResponse
from app.services.firebase_service import firebase_service
from app.services.hotel_service import hotel_service


class ReservationService:
    def __init__(self):
        self.collection_name = settings.RESERVATIONS_COLLECTION

    @staticmethod
    def generate_confirmation_number(user_id: str) -> str:
        """Generate a unique confirmation number for the reservation."""
        timestamp = datetime.now().strftime("%Y%m%d")
        random_part = secrets.token_hex(4).upper()
        user_id_encoded = user_id.encode('utf-8').hex().upper()[:8]
        return f"HM{timestamp}{user_id_encoded}{random_part}"

    async def create_reservation(self, reservation_data: ReservationCreateRequest, user_id: str) -> ReservationInDB:
        """Create a new reservation."""
        try:
            # Get hotel details
            hotel = await hotel_service.get_hotel_by_id(reservation_data.hotel_id)
            if not hotel:
                raise ValueError("Hotel nie został znaleziony")

            if hotel.available_rooms < reservation_data.rooms:
                raise ValueError(f"Brak dostępności. Dostępne pokoje: {hotel.available_rooms}")

            if reservation_data.guests > (hotel.max_guests * reservation_data.rooms):
                raise ValueError(f"Przekroczono maksymalną liczbę gości na pokój ({hotel.max_guests})")

            # Calculate nights and total price
            nights = (reservation_data.check_out_date - reservation_data.check_in_date).days
            if nights <= 0:
                raise ValueError("Data wyjazdu musi być późniejsza niż data przyjazdu")

            total_price = nights * hotel.price_per_night * reservation_data.rooms

            # Create reservation object
            reservation = ReservationInDB(
                user_id=user_id,
                hotel_id=reservation_data.hotel_id,
                hotel_name=hotel.name,
                hotel_address=hotel.address,
                hotel_city=hotel.city,
                check_in_date=reservation_data.check_in_date,
                check_out_date=reservation_data.check_out_date,
                guests=reservation_data.guests,
                rooms=reservation_data.rooms,
                currency=hotel.currency,
                nights=nights,
                guest_name=reservation_data.guest_name,
                guest_email=reservation_data.guest_email,
                guest_phone=reservation_data.guest_phone,
                special_requests=reservation_data.special_requests,
                price_per_night=hotel.price_per_night,
                total_price=total_price,
                confirmation_number=self.generate_confirmation_number(user_id),
                created_at=datetime.now(UTC),
            )

            # Save reservation to Firestore
            doc_id = await firebase_service.create_document(
                self.collection_name, reservation.to_dict()
            )
            reservation.id = doc_id

            # Update hotel availability
            await hotel_service.update_hotel_availability(
                reservation_data.hotel_id, -reservation_data.rooms
            )

            return reservation
        except ValueError as e:
            print(f"❌ Reservation error: {e}")
            raise ValueError(str(e))

        except Exception as e:
            print(f"❌ Unexpected error creating reservation: {e}")
            raise Exception("Wystąpił błąd podczas tworzenia rezerwacji") from e

    async def get_reservation_by_id(self, reservation_id: str) -> Optional[ReservationInDB]:
        """Get reservation by ID"""
        try:
            data = await firebase_service.get_document(self.collection_name, reservation_id)

            if not data:
                return None

            return ReservationInDB.from_dict(data, reservation_id)

        except Exception as e:
            print(f"❌ Error getting reservation: {e}")
            raise

    async def get_reservation_by_confirmation(self, confirmation_number: str) -> Optional[ReservationInDB]:
        """Get reservation by confirmation number"""
        try:
            reservations = await firebase_service.get_documents(
                self.collection_name,
                limit=1,
                where_clauses=[("confirmation_number", "==", confirmation_number)]
            )

            if not reservations:
                return None

            return ReservationInDB.from_dict(reservations[0], reservations[0]["id"])

        except Exception as e:
            print(f"❌ Error getting reservation by confirmation: {e}")
            raise

    async def search_reservations(self, search_request: ReservationSearchRequest) -> Dict[str, Any]:
        """Search reservations with filters and pagination"""
        try:
            where_clauses = []

            # Apply filters
            if search_request.user_id:
                where_clauses.append(("user_id", "==", search_request.user_id))

            if search_request.hotel_id:
                where_clauses.append(("hotel_id", "==", search_request.hotel_id))

            if search_request.status:
                where_clauses.append(("status", "==", search_request.status.value))

            if search_request.guest_email:
                where_clauses.append(("guest_email", "==", search_request.guest_email))

            # Get all matching documents
            all_reservations = await firebase_service.get_documents(
                self.collection_name,
                where_clauses=where_clauses
            )

            # Convert to ReservationInDB objects
            reservations = []
            for res_data in all_reservations:
                try:
                    reservation = ReservationInDB.from_dict(res_data, res_data["id"])

                    # Apply date filters
                    if search_request.check_in_from and reservation.check_in_date < search_request.check_in_from:
                        continue
                    if search_request.check_in_to and reservation.check_in_date > search_request.check_in_to:
                        continue

                    reservations.append(reservation)
                except Exception as e:
                    print(f"⚠️ Error processing reservation {res_data.get('id')}: {e}")
                    continue

            # Sort results
            if search_request.sort_by == "check_in_date":
                reservations.sort(
                    key=lambda x: x.check_in_date,
                    reverse=(search_request.sort_order == "desc")
                )
            elif search_request.sort_by == "total_price":
                reservations.sort(
                    key=lambda x: x.total_price,
                    reverse=(search_request.sort_order == "desc")
                )
            else:  # Default: created_at
                reservations.sort(
                    key=lambda x: x.created_at,
                    reverse=(search_request.sort_order == "desc")
                )

            # Apply pagination
            total = len(reservations)
            total_pages = math.ceil(total / search_request.limit)
            start_idx = (search_request.page - 1) * search_request.limit
            end_idx = start_idx + search_request.limit
            paginated_reservations = reservations[start_idx:end_idx]

            # Convert to response format
            reservation_responses = [res.to_response() for res in paginated_reservations]

            return {
                "reservations": reservation_responses,
                "total": total,
                "page": search_request.page,
                "limit": search_request.limit,
                "total_pages": total_pages,
                "has_next": search_request.page < total_pages,
                "has_previous": search_request.page > 1
            }

        except Exception as e:
            print(f"❌ Error searching reservations: {e}")
            raise

    async def get_user_reservations(self, user_id: str, limit: int = 10) -> List[ReservationResponse]:
        """Get all reservations for a specific user"""
        try:
            search_request = ReservationSearchRequest(
                user_id=user_id,
                limit=limit,
                sort_by="created_at",
                sort_order="desc"
            )

            result = await self.search_reservations(search_request)
            return result["reservations"]

        except Exception as e:
            print(f"❌ Error getting user reservations: {e}")
            raise

    async def update_reservation(self, reservation_id: str, update_data: ReservationUpdateRequest) -> Optional[ReservationInDB]:
        """Update reservation details"""
        try:
            # Get existing reservation
            existing_reservation = await self.get_reservation_by_id(reservation_id)
            if not existing_reservation:
                return None

            # Prepare update data
            update_dict = {}

            if update_data.check_in_date is not None:
                update_dict["check_in_date"] = update_data.check_in_date.isoformat()

            if update_data.check_out_date is not None:
                update_dict["check_out_date"] = update_data.check_out_date.isoformat()

            if update_data.guests is not None:
                update_dict["guests"] = update_data.guests

            if update_data.rooms is not None:
                update_dict["rooms"] = update_data.rooms

            if update_data.guest_name is not None:
                update_dict["guest_name"] = update_data.guest_name

            if update_data.guest_email is not None:
                update_dict["guest_email"] = update_data.guest_email

            if update_data.guest_phone is not None:
                update_dict["guest_phone"] = update_data.guest_phone

            if update_data.special_requests is not None:
                update_dict["special_requests"] = update_data.special_requests

            if update_data.status is not None:
                update_dict["status"] = update_data.status.value

            # Recalculate nights and total price if dates changed
            if update_data.check_in_date or update_data.check_out_date:
                check_in = update_data.check_in_date or existing_reservation.check_in_date
                check_out = update_data.check_out_date or existing_reservation.check_out_date
                rooms = update_data.rooms or existing_reservation.rooms

                nights = (check_out - check_in).days
                if nights <= 0:
                    raise ValueError("Data wyjazdu musi być późniejsza niż data przyjazdu")

                update_dict["nights"] = nights
                update_dict["total_price"] = nights * existing_reservation.price_per_night * rooms

            # Add updated timestamp
            update_dict["updated_at"] = datetime.now(UTC)

            # Update in database
            await firebase_service.update_document(
                self.collection_name,
                reservation_id,
                update_dict
            )

            # Return updated reservation
            return await self.get_reservation_by_id(reservation_id)

        except ValueError:
            raise
        except Exception as e:
            print(f"❌ Error updating reservation: {e}")
            raise

    async def cancel_reservation(self, reservation_id: str, cancellation_reason: str = None) -> bool:
        """Cancel a reservation"""
        try:
            # Get existing reservation
            reservation = await self.get_reservation_by_id(reservation_id)
            if not reservation:
                return False

            # Check if can be cancelled
            if reservation.status in [ReservationStatus.CANCELLED, ReservationStatus.CHECKED_OUT]:
                raise ValueError("Rezerwacja nie może być anulowana")

            # Update reservation status
            update_data = {
                "status": ReservationStatus.CANCELLED.value,
                "cancelled_at": datetime.now(UTC),
                "cancellation_reason": cancellation_reason or "Anulowana przez użytkownika",
                "updated_at": datetime.now(UTC)
            }

            await firebase_service.update_document(
                self.collection_name,
                reservation_id,
                update_data
            )

            # Restore hotel availability
            hotel = await hotel_service.get_hotel_by_id(reservation.hotel_id)
            if hotel:
                await hotel_service.update_hotel_availability(
                    reservation.hotel_id,
                    hotel.available_rooms + reservation.rooms
                )

            print(f"✅ Reservation cancelled: {reservation.confirmation_number}")
            return True

        except ValueError:
            raise
        except Exception as e:
            print(f"❌ Error cancelling reservation: {e}")
            raise

    async def check_in_reservation(self, reservation_id: str) -> bool:
        """Check in a reservation"""
        try:
            reservation = await self.get_reservation_by_id(reservation_id)
            if not reservation:
                return False

            if reservation.status != ReservationStatus.CONFIRMED:
                raise ValueError("Tylko potwierdzone rezerwacje mogą być zameldowane")

            # Check if check-in date is today or in the past
            if reservation.check_in_date > date.today():
                raise ValueError("Zameldowanie możliwe dopiero w dniu przyjazdu")

            update_data = {
                "status": ReservationStatus.CHECKED_IN.value,
                "updated_at": datetime.now(UTC)
            }

            await firebase_service.update_document(
                self.collection_name,
                reservation_id,
                update_data
            )

            return True

        except ValueError:
            raise
        except Exception as e:
            print(f"❌ Error checking in reservation: {e}")
            raise

    async def check_out_reservation(self, reservation_id: str) -> bool:
        """Check out a reservation"""
        try:
            reservation = await self.get_reservation_by_id(reservation_id)
            if not reservation:
                return False

            if reservation.status != ReservationStatus.CHECKED_IN:
                raise ValueError("Tylko zameldowane rezerwacje mogą być wymeldowane")

            update_data = {
                "status": ReservationStatus.CHECKED_OUT.value,
                "updated_at": datetime.now(UTC)
            }

            await firebase_service.update_document(
                self.collection_name,
                reservation_id,
                update_data
            )

            return True

        except ValueError:
            raise
        except Exception as e:
            print(f"❌ Error checking out reservation: {e}")
            raise

    async def update_payment_status(self, reservation_id: str, payment_status: PaymentStatus) -> bool:
        """Update payment status of a reservation"""
        try:
            update_data = {
                "payment_status": payment_status.value,
                "updated_at": datetime.now(UTC)
            }

            # If payment is confirmed, also confirm the reservation
            if payment_status == PaymentStatus.PAID:
                update_data["status"] = ReservationStatus.CONFIRMED.value

            await firebase_service.update_document(
                self.collection_name,
                reservation_id,
                update_data
            )

            return True

        except Exception as e:
            print(f"❌ Error updating payment status: {e}")
            raise

    async def get_reservation_statistics(self) -> ReservationStatsResponse:
        """Get reservation statistics"""
        try:
            # Get all reservations
            all_reservations = await firebase_service.get_documents(self.collection_name)

            if not all_reservations:
                return ReservationStatsResponse(
                    total_reservations=0,
                    confirmed_reservations=0,
                    pending_reservations=0,
                    cancelled_reservations=0,
                    total_revenue=0.0,
                    average_stay_length=0.0,
                    occupancy_rate=0.0
                )

            # Calculate statistics
            total_reservations = len(all_reservations)
            confirmed_count = sum(1 for r in all_reservations if r.get("status") == "confirmed")
            pending_count = sum(1 for r in all_reservations if r.get("status") == "pending")
            cancelled_count = sum(1 for r in all_reservations if r.get("status") == "cancelled")

            # Calculate revenue (only from confirmed/checked_in/checked_out reservations)
            total_revenue = sum(
                r.get("total_price", 0) for r in all_reservations
                if r.get("status") in ["confirmed", "checked_in", "checked_out"]
            )

            # Calculate average stay length
            valid_reservations = [r for r in all_reservations if r.get("nights", 0) > 0]
            average_stay_length = (
                sum(r.get("nights", 0) for r in valid_reservations) / len(valid_reservations)
                if valid_reservations else 0.0
            )

            occupied_rooms = sum(
                r.get("rooms", 0) for r in all_reservations
                if r.get("status") in ["confirmed", "checked_in"]
            )

            # Get total rooms from all hotels
            hotels = await firebase_service.get_documents(settings.HOTELS_COLLECTION)
            total_hotel_rooms = sum(h.get("total_rooms", 0) for h in hotels)

            occupancy_rate = (
                (occupied_rooms / total_hotel_rooms * 100)
                if total_hotel_rooms > 0 else 0.0
            )

            return ReservationStatsResponse(
                total_reservations=total_reservations,
                confirmed_reservations=confirmed_count,
                pending_reservations=pending_count,
                cancelled_reservations=cancelled_count,
                total_revenue=total_revenue,
                average_stay_length=round(average_stay_length, 1),
                occupancy_rate=round(occupancy_rate, 1)
            )

        except Exception as e:
            print(f"❌ Error getting reservation statistics: {e}")
            raise

# Create singleton instance
reservation_service = ReservationService()
