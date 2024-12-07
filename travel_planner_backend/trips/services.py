import requests
import json
from datetime import datetime, timedelta
import random

class WeatherService:
    @staticmethod
    def get_forecast(city, start_date, end_date):
        """Get dummy weather forecast data."""
        weather_conditions = ['Sunny', 'Cloudy', 'Rainy', 'Partly Cloudy']
        
        try:
            # Convert string dates to datetime objects
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Generate weather data for each day
            forecast_data = []
            current_date = start
            
            while current_date <= end:
                forecast_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'temperature': random.randint(18, 30),
                    'condition': random.choice(weather_conditions),
                    'humidity': random.randint(40, 90)
                })
                current_date += timedelta(days=1)
            
            return forecast_data
        except Exception as e:
            print(f"Error generating weather data: {str(e)}")
            return []

class PlacesService:
    @staticmethod
    def get_places_of_interest(location, interests):
        """Get dummy places of interest data."""
        dummy_places = [
            {
                'name': 'Historic City Center',
                'description': 'Beautiful historic district with architecture from the 18th century',
                'rating': 4.5,
                'image': 'https://picsum.photos/400/300',
                'type': 'Cultural'
            },
            {
                'name': 'Central Park Gardens',
                'description': 'Expansive park with walking trails and botanical gardens',
                'rating': 4.7,
                'image': 'https://picsum.photos/400/301',
                'type': 'Nature'
            },
            {
                'name': 'Museum of Modern Art',
                'description': 'World-class museum featuring contemporary artworks',
                'rating': 4.6,
                'image': 'https://picsum.photos/400/302',
                'type': 'Cultural'
            },
            {
                'name': 'Local Food Market',
                'description': 'Traditional market with local specialties and fresh produce',
                'rating': 4.4,
                'image': 'https://picsum.photos/400/303',
                'type': 'Food'
            },
            {
                'name': 'Adventure Sports Center',
                'description': 'Various outdoor activities and adventure sports',
                'rating': 4.3,
                'image': 'https://picsum.photos/400/304',
                'type': 'Adventure'
            }
        ]
        return dummy_places

class FlightService:
    @staticmethod
    def get_flight_offers(origin, destination, departure_date, return_date):
        """Get flight offers using Amadeus API."""
        from travel_planner_backend.api_config import AMADEUS_API_KEY, AMADEUS_API_SECRET, AMADEUS_BASE_URL
        import requests
        import json
        
        try:
            print("\n=== Starting Amadeus API Request ===")
            
            # First, get the access token
            auth_url = f"{AMADEUS_BASE_URL}/v1/security/oauth2/token"
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': AMADEUS_API_KEY,
                'client_secret': AMADEUS_API_SECRET
            }
            
            print(f"\nAuth Request:")
            print(f"URL: {auth_url}")
            print(f"Data: {json.dumps(auth_data, indent=2)}")
            
            auth_response = requests.post(auth_url, data=auth_data)
            
            print(f"\nAuth Response:")
            print(f"Status Code: {auth_response.status_code}")
            print(f"Response Headers: {dict(auth_response.headers)}")
            print(f"Response Body: {auth_response.text}")
            
            if not auth_response.ok:
                print(f"\nAuth Error: {auth_response.status_code} - {auth_response.text}")
                return FlightService.get_dummy_flights(origin, destination, departure_date, return_date)
            
            access_token = auth_response.json().get('access_token')
            if not access_token:
                print("\nNo access token received")
                return FlightService.get_dummy_flights(origin, destination, departure_date, return_date)
            
            # Search for flights
            url = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            # Convert dates to IATA format (YYYY-MM-DD)
            try:
                from datetime import datetime
                if isinstance(departure_date, str):
                    departure_date = datetime.strptime(departure_date, '%Y-%m-%d').strftime('%Y-%m-%d')
                if isinstance(return_date, str):
                    return_date = datetime.strptime(return_date, '%Y-%m-%d').strftime('%Y-%m-%d')
            except Exception as e:
                print(f"\nDate formatting error: {e}")
                return FlightService.get_dummy_flights(origin, destination, departure_date, return_date)
            
            params = {
                'originLocationCode': origin,
                'destinationLocationCode': destination,
                'departureDate': departure_date,
                'adults': '1',
                'max': '5'
            }
            
            if return_date:
                params['returnDate'] = return_date
            
            print(f"\nFlight Search Request:")
            print(f"URL: {url}")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            print(f"Params: {json.dumps(params, indent=2)}")
            
            response = requests.get(url, headers=headers, params=params)
            
            print(f"\nFlight Search Response:")
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Body: {response.text[:1000]}...")  # First 1000 chars to avoid too much output
            
            if not response.ok:
                print(f"\nFlight Search Error: {response.status_code} - {response.text}")
                return FlightService.get_dummy_flights(origin, destination, departure_date, return_date)
            
            flight_data = response.json()
            
            if not flight_data.get('data'):
                print("\nNo flight offers found")
                return FlightService.get_dummy_flights(origin, destination, departure_date, return_date)
            
            # Format the response
            formatted_flights = []
            for offer in flight_data['data']:
                try:
                    itinerary = offer['itineraries'][0]
                    segment = itinerary['segments'][0]
                    price = offer['price']['total']
                    
                    formatted_flights.append({
                        'airline': segment['carrierCode'],
                        'flight_number': f"{segment['carrierCode']}{segment['number']}",
                        'departure': {
                            'city': origin,
                            'date': segment['departure']['at'].split('T')[0],
                            'time': segment['departure']['at'].split('T')[1].split('.')[0]
                        },
                        'arrival': {
                            'city': destination,
                            'date': segment['arrival']['at'].split('T')[0],
                            'time': segment['arrival']['at'].split('T')[1].split('.')[0]
                        },
                        'price': float(price),
                        'currency': offer['price']['currency'],
                        'booking_code': offer['id']
                    })
                except (KeyError, IndexError) as e:
                    print(f"\nError formatting flight offer: {e}")
                    continue
            
            if not formatted_flights:
                print("\nNo valid flight offers could be formatted")
                return FlightService.get_dummy_flights(origin, destination, departure_date, return_date)
            
            print("\n=== Flight Search Completed Successfully ===")
            return {'data': formatted_flights}
            
        except Exception as e:
            print(f"\nAmadeus API error: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return FlightService.get_dummy_flights(origin, destination, departure_date, return_date)
    
    @staticmethod
    def get_dummy_flights(origin, destination, departure_date, return_date):
        """Fallback method for dummy flight data."""
        airlines = ['SkyWings', 'Global Air', 'Ocean Airlines', 'Mountain Express']
        
        dummy_flights = []
        for _ in range(5):
            price = random.randint(300, 1000)
            airline = random.choice(airlines)
            dummy_flights.append({
                'airline': airline,
                'flight_number': f'{airline[:2].upper()}{random.randint(100, 999)}',
                'departure': {
                    'city': origin,
                    'date': departure_date,
                    'time': f'{random.randint(0, 23):02d}:{random.randint(0, 59):02d}'
                },
                'arrival': {
                    'city': destination,
                    'date': departure_date,
                    'time': f'{random.randint(0, 23):02d}:{random.randint(0, 59):02d}'
                },
                'price': price,
                'currency': 'USD',
                'seats_available': random.randint(1, 20)
            })
        
        return {'data': dummy_flights}

class HotelService:
    @staticmethod
    def get_hotel_recommendations(city, check_in, check_out, budget_per_night):
        """Get dummy hotel recommendations data."""
        hotel_names = ['Grand Hotel', 'City Center Inn', 'Luxury Resort', 'Business Hotel', 'Boutique Stay']
        amenities = ['WiFi', 'Pool', 'Spa', 'Gym', 'Restaurant', 'Bar', 'Room Service', 'Parking']
        
        dummy_hotels = []
        for i, name in enumerate(hotel_names):
            price = min(random.randint(100, 300), float(budget_per_night))
            dummy_hotels.append({
                'name': f'{name} {city}',
                'address': f'{random.randint(1, 999)} Main Street, {city}',
                'rating': round(random.uniform(3.5, 5.0), 1),
                'price_per_night': price,
                'total_price': price * (datetime.strptime(check_out, '%Y-%m-%d') - datetime.strptime(check_in, '%Y-%m-%d')).days,
                'currency': 'USD',
                'image': f'https://picsum.photos/400/{305 + i}',
                'amenities': random.sample(amenities, random.randint(3, 6)),
                'description': 'A wonderful hotel in a prime location with excellent service and modern amenities.',
                'available_rooms': random.randint(1, 10)
            })
        
        return dummy_hotels
