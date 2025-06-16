import asyncio
import sys
import os
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.hotel import HotelCreateRequest, HotelCategory
from app.services.hotel_service import HotelService
from app.services.firebase_service import firebase_service

# Sample hotel data
SAMPLE_HOTELS = [
    {
        "name": "Grand Hotel Warsaw",
        "description": "Luksusowy hotel w samym sercu Warszawy z przepięknym widokiem na Wisłę. Oferujemy najwyższej klasy usługi, eleganckie pokoje oraz doskonałą kuchnię. Idealny dla biznesu i wypoczynku.",
        "category": HotelCategory.HOTEL,
        "address": "Krakowskie Przedmieście 13",
        "city": "Warszawa",
        "country": "Polska",
        "latitude": 52.2394,
        "longitude": 21.0150,
        "price_per_night": 450.00,
        "currency": "PLN",
        "max_guests": 4,
        "total_rooms": 150,
        "amenities": ["WiFi", "Spa", "Parking", "Restauracja", "Siłownia", "Basen", "Room Service", "Klimatyzacja"],
        "images": [
            "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&q=80",
            "https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=600&q=80",
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=600&q=80"
        ],
        "contact_phone": "+48 22 123 4567",
        "contact_email": "info@grandhotelwarsaw.pl",
        "website": "https://grandhotelwarsaw.pl",
        "check_in_time": "15:00",
        "check_out_time": "11:00",
        "cancellation_policy": "Darmowa anulacja do 24 godzin przed przyjazdem",
        "rating": 4.8,
        "review_count": 1247
    },
    {
        "name": "Seaside Resort Sopot",
        "description": "Ekskluzywny resort nad morzem, zaledwie 50 metrów od pięknej plaży w Sopocie. Doskonałe miejsce na romantyczny weekend lub rodzinne wakacje nad Bałtykiem.",
        "category": HotelCategory.HOTEL,
        "address": "Plażowa 15",
        "city": "Sopot",
        "country": "Polska",
        "latitude": 54.4518,
        "longitude": 18.5644,
        "price_per_night": 345.00,
        "currency": "PLN",
        "max_guests": 6,
        "total_rooms": 80,
        "amenities": ["WiFi", "Plaża", "Restauracja", "Basen", "Spa", "Parking", "Taras", "Widok na morze"],
        "images": [
            "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=600&q=80",
            "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=600&q=80",
            "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=600&q=80"
        ],
        "contact_phone": "+48 58 765 4321",
        "contact_email": "rezerwacje@seasideresort.pl",
        "website": "https://seasideresort.pl",
        "check_in_time": "14:00",
        "check_out_time": "12:00",
        "cancellation_policy": "Darmowa anulacja do 48 godzin przed przyjazdem",
        "rating": 4.6,
        "review_count": 892
    },
    {
        "name": "Mountain Resort Zakopane",
        "description": "Malowniczy resort w sercu Tatr, otoczony wspaniałymi górskimi krajobrazami. Idealny dla miłośników sportów zimowych i pieszych wędrówek górskich.",
        "category": HotelCategory.HOTEL,
        "address": "Krupówki 42",
        "city": "Zakopane",
        "country": "Polska",
        "latitude": 49.2992,
        "longitude": 19.9496,
        "price_per_night": 298.00,
        "currency": "PLN",
        "max_guests": 4,
        "total_rooms": 65,
        "amenities": ["WiFi", "Spa", "Restauracja", "Siłownia", "Sauna", "Parking", "Wypożyczalnia nart", "Kominek"],
        "images": [
            "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=600&q=80",
            "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&q=80",
            "https://images.unsplash.com/photo-1486022332546-27bd52eb6919?w=600&q=80"
        ],
        "contact_phone": "+48 18 234 5678",
        "contact_email": "info@mountainresort.pl",
        "website": "https://mountainresort.pl",
        "check_in_time": "15:00",
        "check_out_time": "11:00",
        "cancellation_policy": "Darmowa anulacja do 72 godzin przed przyjazdem",
        "rating": 4.7,
        "review_count": 643
    },
    {
        "name": "City Business Hotel Kraków",
        "description": "Nowoczesny hotel biznesowy w centrum Krakowa, w pobliżu Starego Miasta i głównych atrakcji turystycznych. Doskonały dla podróży służbowych i turystycznych.",
        "category": HotelCategory.HOTEL,
        "address": "Floriańska 32",
        "city": "Kraków",
        "country": "Polska",
        "latitude": 50.0647,
        "longitude": 19.9450,
        "price_per_night": 267.00,
        "currency": "PLN",
        "max_guests": 2,
        "total_rooms": 120,
        "amenities": ["WiFi", "Centrum biznesowe", "Parking", "Restauracja", "Sala konferencyjna", "Recepcja 24h"],
        "images": [
            "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=600&q=80",
            "https://images.unsplash.com/photo-1568495248636-6432b97bd949?w=600&q=80",
            "https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=600&q=80"
        ],
        "contact_phone": "+48 12 345 6789",
        "contact_email": "business@citykrakow.pl",
        "website": "https://citybusinesskrakow.pl",
        "check_in_time": "14:00",
        "check_out_time": "12:00",
        "cancellation_policy": "Darmowa anulacja do 24 godzin przed przyjazdem",
        "rating": 4.5,
        "review_count": 523
    },
    {
        "name": "Wellness Spa Karpacz",
        "description": "Luksusowy hotel SPA w malowniczych Karkonoszach. Oferujemy bogaty program zabiegów wellness, saunę, basen termalny i wiele więcej dla pełnego relaksu.",
        "category": HotelCategory.HOTEL,
        "address": "Olimpijska 10",
        "city": "Karpacz",
        "country": "Polska",
        "latitude": 50.7795,
        "longitude": 15.7398,
        "price_per_night": 389.00,
        "currency": "PLN",
        "max_guests": 2,
        "total_rooms": 45,
        "amenities": ["WiFi", "Spa", "Basen termalny", "Sauna", "Masaże", "Joga", "Restauracja", "Parking"],
        "images": [
            "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=600&q=80",
            "https://images.unsplash.com/photo-1540555700478-4be289fbecef?w=600&q=80",
            "https://images.unsplash.com/photo-1544943910-4c1dc44aab44?w=600&q=80"
        ],
        "contact_phone": "+48 75 987 6543",
        "contact_email": "wellness@spapalace.pl",
        "website": "https://wellnessspakarpacz.pl",
        "check_in_time": "16:00",
        "check_out_time": "11:00",
        "cancellation_policy": "Darmowa anulacja do 48 godzin przed przyjazdem",
        "rating": 4.9,
        "review_count": 234
    },
    {
        "name": "Boutique Hotel Wrocław",
        "description": "Klimatyczny hotel butikowy w zabytkowej kamienicy na wrocławskim Rynku. Każdy pokój urządzony w unikalnym stylu, łącząc historię z nowoczesnością.",
        "category": HotelCategory.HOTEL,
        "address": "Rynek 15",
        "city": "Wrocław",
        "country": "Polska",
        "latitude": 51.1079,
        "longitude": 17.0385,
        "price_per_night": 320.00,
        "currency": "PLN",
        "max_guests": 3,
        "total_rooms": 25,
        "amenities": ["WiFi", "Restauracja", "Bar", "Parking", "Concierge", "Klimatyzacja", "Historyczny budynek"],
        "images": [
            "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=600&q=80",
            "https://images.unsplash.com/photo-1586611292717-f828b167408c?w=600&q=80",
            "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=600&q=80"
        ],
        "contact_phone": "+48 71 654 3210",
        "contact_email": "reservations@boutiquewroclaw.pl",
        "website": "https://boutiquewroclaw.pl",
        "check_in_time": "15:00",
        "check_out_time": "11:00",
        "cancellation_policy": "Darmowa anulacja do 24 godzin przed przyjazdem",
        "rating": 4.4,
        "review_count": 178
    },
    {
        "name": "Nowoczesny Apartament Gdańsk",
        "description": "Stylowe apartamenty w centrum Gdańska, w pełni wyposażone, idealne na dłuższe pobyty. Bliskość Starego Miasta i głównych atrakcji turystycznych.",
        "category": HotelCategory.APARTMENT,
        "address": "Długa 88",
        "city": "Gdańsk",
        "country": "Polska",
        "latitude": 54.3520,
        "longitude": 18.6466,
        "price_per_night": 195.00,
        "currency": "PLN",
        "max_guests": 4,
        "total_rooms": 15,
        "amenities": ["WiFi", "Kuchnia", "Pralka", "Parking", "Balkon", "Recepcja", "Klimatyzacja"],
        "images": [
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=600&q=80",
            "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=600&q=80",
            "https://images.unsplash.com/photo-1574362848149-11496d93a7c7?w=600&q=80"
        ],
        "contact_phone": "+48 58 123 9876",
        "contact_email": "apartamenty@gdansk.pl",
        "website": "https://apartamentygdansk.pl",
        "check_in_time": "15:00",
        "check_out_time": "11:00",
        "cancellation_policy": "Darmowa anulacja do 48 godzin przed przyjazdem",
        "rating": 4.3,
        "review_count": 89
    },
    {
        "name": "Hostel Młodzieżowy Poznań",
        "description": "Przytulny hostel w centrum Poznania, oferujący czyste i wygodne pokoje w przystępnych cenach. Idealny dla backpackerów i młodych podróżników.",
        "category": HotelCategory.HOSTEL,
        "address": "Święty Marcin 67",
        "city": "Poznań",
        "country": "Polska",
        "latitude": 52.4064,
        "longitude": 16.9252,
        "price_per_night": 65.00,
        "currency": "PLN",
        "max_guests": 8,
        "total_rooms": 30,
        "amenities": ["WiFi", "Kuchnia wspólna", "Pralnia", "Wspólna przestrzeń", "Przechowalnia bagażu",
                      "Recepcja 24h"],
        "images": [
            "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=600&q=80",
            "https://images.unsplash.com/photo-1586227740560-8cf2732c1531?w=600&q=80",
            "https://images.unsplash.com/photo-1576675466776-1fbc74c5b14b?w=600&q=80"
        ],
        "contact_phone": "+48 61 987 6543",
        "contact_email": "hostel@poznanstay.pl",
        "website": "https://hostelpoznan.pl",
        "check_in_time": "14:00",
        "check_out_time": "10:00",
        "cancellation_policy": "Darmowa anulacja do 24 godzin przed przyjazdem",
        "rating": 4.1,
        "review_count": 412
    },
    {
        "name": "Villa Luxury Ustka",
        "description": "Elegancka willa nad morzem w Ustce, oferująca ekskluzywne pokoje z widokiem na Bałtyk. Prywatna plaża, ogród i wyjątkowa atmosfera.",
        "category": HotelCategory.VILLA,
        "address": "Nadmorska 22",
        "city": "Ustka",
        "country": "Polska",
        "latitude": 54.5806,
        "longitude": 16.8614,
        "price_per_night": 520.00,
        "currency": "PLN",
        "max_guests": 6,
        "total_rooms": 8,
        "amenities": ["WiFi", "Prywatna plaża", "Ogród", "Taras", "Parking", "Grill", "Jacuzzi", "Widok na morze"],
        "images": [
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600&q=80",
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&q=80",
            "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=600&q=80"
        ],
        "contact_phone": "+48 59 123 4567",
        "contact_email": "villa@luxuryustka.pl",
        "website": "https://villaluxuryustka.pl",
        "check_in_time": "16:00",
        "check_out_time": "12:00",
        "cancellation_policy": "Darmowa anulacja do 7 dni przed przyjazdem",
        "rating": 4.8,
        "review_count": 67
    },
    {
        "name": "Eco Glamping Bieszczady",
        "description": "Unikalny glamping w sercu Bieszczadów, oferujący komfortowe namioty z pełnym wyposażeniem. Idealne miejsce na połączenie z naturą bez rezygnacji z wygody.",
        "category": HotelCategory.GLAMPING,
        "address": "Lesko, ul. Bieszczadzka 1",
        "city": "Lesko",
        "country": "Polska",
        "latitude": 49.4697,
        "longitude": 22.3306,
        "price_per_night": 180.00,
        "currency": "PLN",
        "max_guests": 4,
        "total_rooms": 12,
        "amenities": ["WiFi", "Ognisko", "Wędrówki", "Obserwacja gwiazd", "Parking", "Ekologia", "Restauracja"],
        "images": [
            "https://images.unsplash.com/photo-1504851149312-7a075b496cc7?w=600&q=80",
            "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&q=80",
            "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=600&q=80"
        ],
        "contact_phone": "+48 13 567 8901",
        "contact_email": "glamping@bieszczady.pl",
        "website": "https://glampingbieszczady.pl",
        "check_in_time": "15:00",
        "check_out_time": "11:00",
        "cancellation_policy": "Darmowa anulacja do 48 godzin przed przyjazdem",
        "rating": 4.6,
        "review_count": 156
    }
]


async def create_sample_hotel(hotel_data: dict) -> bool:
    """Create a single hotel from sample data"""
    try:
        # Extract rating and review_count for later update
        rating = hotel_data.pop('rating', 0.0)
        review_count = hotel_data.pop('review_count', 0)

        # Create hotel request
        hotel_request = HotelCreateRequest(**hotel_data)

        # Create hotel
        created_hotel = await HotelService.create_hotel(hotel_request)

        if created_hotel and created_hotel.id:
            await HotelService.update_hotel_rating(
                created_hotel.id,
                rating,
                review_count
            )

            available_rooms = random.randint(
                max(1, created_hotel.total_rooms - 20),
                created_hotel.total_rooms
            )
            await HotelService.update_hotel_availability(
                created_hotel.id,
                available_rooms
            )

            print(f"✅ Utworzono hotel: {created_hotel.name} (ID: {created_hotel.id})")
            print(f"   📍 {created_hotel.city}, {created_hotel.address}")
            print(f"   💰 {created_hotel.price_per_night} {created_hotel.currency}/noc")
            print(f"   ⭐ {rating}/5.0 ({review_count} opinii)")
            print(f"   🏠 {available_rooms}/{created_hotel.total_rooms} pokoi dostępnych")
            print()
            return True
        else:
            print(f"❌ Nie udało się utworzyć hotelu: {hotel_data['name']}")
            return False

    except Exception as e:
        print(f"❌ Błąd podczas tworzenia hotelu {hotel_data['name']}: {e}")
        return False


async def seed_hotels():
    """Create all sample hotels"""
    print("🏨 HotelMate - Skrypt seed dla hoteli")
    print("=" * 50)
    print()

    # Initialize Firebase connection
    try:
        # Test Firebase connection
        collections = firebase_service.get_hotels_collection()
        print("✅ Połączono z Firebase Firestore")
        print()
    except Exception as e:
        print(f"❌ Błąd połączenia z Firebase: {e}")
        print("Sprawdź konfigurację Firebase i upewnij się, że zmienne środowiskowe są ustawione.")
        return

    # Check if hotels already exist
    try:
        existing_query = firebase_service.get_hotels_collection().limit(1)
        existing_docs = existing_query.get()

        if len(existing_docs) > 0:
            print("⚠️  Wykryto istniejące hotele w bazie danych.")
            response = input("Czy chcesz kontynuować i dodać więcej hoteli? (y/N): ")
            if response.lower() not in ['y', 'yes', 'tak', 't']:
                print("Anulowano operację.")
                return
            print()
    except Exception as e:
        print(f"⚠️  Nie można sprawdzić istniejących hoteli: {e}")
        print("Kontynuowanie...")
        print()

    # Create hotels
    print(f"🚀 Tworzenie {len(SAMPLE_HOTELS)} przykładowych hoteli...")
    print()

    success_count = 0
    for i, hotel_data in enumerate(SAMPLE_HOTELS, 1):
        print(f"[{i}/{len(SAMPLE_HOTELS)}] Tworzenie: {hotel_data['name']}")

        if await create_sample_hotel(hotel_data.copy()):
            success_count += 1

        # Sleep to avoid hitting Firestore limits
        await asyncio.sleep(0.5)

    # Summary
    print("=" * 50)
    print(f"✅ Zakończono! Utworzono {success_count}/{len(SAMPLE_HOTELS)} hoteli")

    if success_count > 0:
        print()
        print("🎉 Przykładowe hotele zostały pomyślnie dodane do bazy danych!")
        print("Możesz teraz:")
        print("   • Uruchomić aplikację mobilną i zobaczyć hotele")
        print("   • Testować wyszukiwanie i filtrowanie")
        print("   • Sprawdzić API endpoints w dokumentacji (/docs)")
        print()
        print("📊 Statystyki utworzonych hoteli:")

        # Count by category
        categories = {}
        cities = set()
        for hotel in SAMPLE_HOTELS[:success_count]:
            category = hotel['category']
            if category in categories:
                categories[category] += 1
            else:
                categories[category] = 1
            cities.add(hotel['city'])

        for category, count in categories.items():
            print(f"   • {category.value}: {count} hoteli")

        print(f"   • Miasta: {len(cities)} ({', '.join(sorted(cities))})")

        # Price range
        prices = [hotel['price_per_night'] for hotel in SAMPLE_HOTELS[:success_count]]
        print(f"   • Zakres cen: {min(prices):.0f} - {max(prices):.0f} PLN/noc")

    print()


async def clear_all_hotels():
    """Clear all hotels from database (for testing)"""
    print("🗑️  Usuwanie wszystkich hoteli z bazy danych...")

    try:
        collection = firebase_service.get_hotels_collection()
        docs = await collection.get()

        count = 0
        for doc in docs:
            await doc.reference.delete()
            count += 1

        print(f"✅ Usunięto {count} hoteli")
    except Exception as e:
        print(f"❌ Błąd podczas usuwania hoteli: {e}")


async def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        await clear_all_hotels()
    else:
        await seed_hotels()


if __name__ == "__main__":
    # Run the seed script
    asyncio.run(main())