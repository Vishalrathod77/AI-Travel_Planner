from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from django.core.exceptions import ValidationError
from .models import Trip, TripDetail
from .serializers import TripSerializer, TripDetailSerializer
from django.shortcuts import get_object_or_404
from .services import WeatherService, PlacesService, FlightService, HotelService
from .test_api import test_places_api
import json
from django.db import transaction

@api_view(['GET'])
def test_google_places(request):
    """Test endpoint for Google Places API"""
    result = test_places_api()
    return Response(result)

@api_view(['POST'])
def search_flights(request):
    """Search for flights using Amadeus API."""
    try:
        origin = request.data.get('origin')
        destination = request.data.get('destination')
        departure_date = request.data.get('departure_date')
        return_date = request.data.get('return_date')

        if not all([origin, destination, departure_date]):
            return Response(
                {'error': 'Missing required parameters'},
                status=400
            )

        flight_data = FlightService.get_flight_offers(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date
        )

        return Response(flight_data)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=500
        )

# Create your views here.

class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all().order_by('-created_at')
    serializer_class = TripSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def retrieve(self, request, *args, **kwargs):
        """Get a single trip with all its details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        # Get or create TripDetail
        trip_detail, created = TripDetail.objects.get_or_create(trip=instance)
        
        # Fetch fresh data if details don't exist
        if created or not any([trip_detail.weather_data, trip_detail.hotel_data, trip_detail.food_data]):
            try:
                # Get weather data
                weather_data = WeatherService.get_forecast(
                    instance.destination,
                    instance.start_date,
                    instance.end_date
                )
                trip_detail.weather_data = weather_data

                # Get hotel recommendations
                trip_duration = (instance.end_date - instance.start_date).days
                budget_per_night = float(instance.budget) / trip_duration if trip_duration > 0 else float(instance.budget)
                hotels = HotelService.get_hotel_recommendations(
                    city=instance.destination,
                    check_in=instance.start_date.isoformat(),
                    check_out=instance.end_date.isoformat(),
                    budget_per_night=budget_per_night
                )
                trip_detail.hotel_data = hotels

                # Get places of interest
                places = PlacesService.get_places_of_interest(
                    instance.destination,
                    instance.interests
                )
                trip_detail.food_data = places  # Using places API for food recommendations too

                trip_detail.save()
            except Exception as e:
                print(f"Error fetching trip details: {str(e)}")

        # Add details to response
        detail_serializer = TripDetailSerializer(trip_detail)
        data['details'] = detail_serializer.data
        
        return Response(data)

    def list(self, request, *args, **kwargs):
        """Get all trips with their details"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data

            # Fetch details for each trip if they don't exist
            for trip_data in data:
                trip = Trip.objects.get(id=trip_data['id'])
                trip_detail, created = TripDetail.objects.get_or_create(trip=trip)
                
                # Only fetch fresh data if details don't exist
                if created or not any([trip_detail.weather_data, trip_detail.hotel_data, trip_detail.food_data]):
                    try:
                        # Get weather data
                        weather_data = WeatherService.get_forecast(
                            trip.destination,
                            trip.start_date,
                            trip.end_date
                        )
                        trip_detail.weather_data = json.dumps(weather_data) if weather_data else None

                        # Get hotel recommendations
                        trip_duration = (trip.end_date - trip.start_date).days
                        budget_per_night = float(trip.budget) / trip_duration if trip_duration > 0 else float(trip.budget)
                        hotels = HotelService.get_hotel_recommendations(
                            city=trip.destination,
                            check_in=trip.start_date.isoformat(),
                            check_out=trip.end_date.isoformat(),
                            budget_per_night=budget_per_night
                        )
                        trip_detail.hotel_data = json.dumps(hotels) if hotels else None

                        # Get places of interest
                        places = PlacesService.get_places_of_interest(
                            trip.destination,
                            trip.interests
                        )
                        trip_detail.food_data = json.dumps(places) if places else None

                        trip_detail.save()
                    except Exception as e:
                        print(f"Error fetching details for trip {trip.id}: {str(e)}")
                        # Continue with next trip if there's an error

            return Response(data)
        except Exception as e:
            print("Error listing trips:", str(e))
            return Response(
                {"detail": "Failed to retrieve trips"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a new trip with optional details"""
        try:
            print("Received data:", request.data)
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                print("Validation errors:", serializer.errors)
                return Response(
                    {"detail": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the trip in a transaction
            trip = serializer.save()
            
            # Get or create TripDetail
            trip_detail, created = TripDetail.objects.get_or_create(
                trip=trip,
                defaults={
                    'weather_data': None,
                    'hotel_data': None,
                    'food_data': None
                }
            )
            
            # Fetch fresh data for the trip
            try:
                weather_data = WeatherService.get_forecast(
                    trip.destination,
                    trip.start_date,
                    trip.end_date
                )
                if weather_data:
                    trip_detail.weather_data = json.dumps(weather_data)

                trip_duration = (trip.end_date - trip.start_date).days
                budget_per_night = float(trip.budget) / trip_duration if trip_duration > 0 else float(trip.budget)
                hotels = HotelService.get_hotel_recommendations(
                    city=trip.destination,
                    check_in=trip.start_date.isoformat(),
                    check_out=trip.end_date.isoformat(),
                    budget_per_night=budget_per_night
                )
                if hotels:
                    trip_detail.hotel_data = json.dumps(hotels)

                places = PlacesService.get_places_of_interest(
                    trip.destination,
                    trip.interests
                )
                if places:
                    trip_detail.food_data = json.dumps(places)

                trip_detail.save()
            except Exception as e:
                print(f"Error fetching trip details: {str(e)}")
                # Continue even if fetching details fails
            
            # Return the trip with details
            response_serializer = self.get_serializer(trip)
            headers = self.get_success_headers(response_serializer.data)
            
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except Exception as e:
            print("Error creating trip:", str(e))
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        trip = self.get_object()
        # Delete associated trip details first
        if hasattr(trip, 'tripdetail'):
            trip.tripdetail.delete()
        trip.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Update a trip and its details"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
            
            if not serializer.is_valid():
                return Response(
                    {"detail": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update the trip
            trip = serializer.save()
            
            # Get or create TripDetail
            trip_detail, created = TripDetail.objects.get_or_create(
                trip=trip,
                defaults={
                    'weather_data': None,
                    'hotel_data': None,
                    'food_data': None
                }
            )
            
            # Fetch fresh data
            try:
                weather_data = WeatherService.get_forecast(
                    trip.destination,
                    trip.start_date,
                    trip.end_date
                )
                if weather_data:
                    trip_detail.weather_data = json.dumps(weather_data)

                trip_duration = (trip.end_date - trip.start_date).days
                budget_per_night = float(trip.budget) / trip_duration if trip_duration > 0 else float(trip.budget)
                hotels = HotelService.get_hotel_recommendations(
                    city=trip.destination,
                    check_in=trip.start_date.isoformat(),
                    check_out=trip.end_date.isoformat(),
                    budget_per_night=budget_per_night
                )
                if hotels:
                    trip_detail.hotel_data = json.dumps(hotels)

                places = PlacesService.get_places_of_interest(
                    trip.destination,
                    trip.interests
                )
                if places:
                    trip_detail.food_data = json.dumps(places)

                trip_detail.save()
            except Exception as e:
                print(f"Error fetching trip details: {str(e)}")
            
            return Response(serializer.data)
        except Exception as e:
            print("Error updating trip:", str(e))
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def save_details(self, request, pk=None):
        try:
            trip = self.get_object()
            details_data = request.data
            
            try:
                trip_detail = trip.details
                for key, value in details_data.items():
                    setattr(trip_detail, key, value)
                trip_detail.save()
            except TripDetail.DoesNotExist:
                TripDetail.objects.create(trip=trip, **details_data)
            
            return Response({'status': 'details saved'})
        except Exception as e:
            print("Error saving details:", str(e))
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def weather(self, request, pk=None):
        """Get weather forecast for the trip destination."""
        trip = self.get_object()
        weather_data = WeatherService.get_forecast(
            trip.destination,
            trip.start_date,
            trip.end_date
        )
        return Response(weather_data)

    def places_of_interest(self, request, pk=None):
        """Get interesting places based on trip preferences."""
        trip = self.get_object()
        places = PlacesService.get_places_of_interest(
            trip.destination,
            trip.interests
        )
        return Response(places)

    def search_flights(self, request, pk=None):
        """Search for flights for the trip."""
        trip = self.get_object()
        origin = request.data.get('origin')
        if not origin:
            return Response(
                {"error": "Origin city is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        flight_offers = FlightService.get_flight_offers(
            origin=origin,
            destination=trip.destination,
            departure_date=trip.start_date.isoformat(),
            return_date=trip.end_date.isoformat()
        )
        return Response(flight_offers)

    def hotel_recommendations(self, request, pk=None):
        """Get hotel recommendations for the trip."""
        trip = self.get_object()
        # Calculate budget per night
        trip_duration = (trip.end_date - trip.start_date).days
        budget_per_night = float(trip.budget) / trip_duration if trip_duration > 0 else float(trip.budget)
        
        hotels = HotelService.get_hotel_recommendations(
            city=trip.destination,
            check_in=trip.start_date.isoformat(),
            check_out=trip.end_date.isoformat(),
            budget_per_night=budget_per_night
        )
        return Response(hotels)
