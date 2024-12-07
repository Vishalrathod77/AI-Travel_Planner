from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TripViewSet, test_google_places, search_flights

router = DefaultRouter()
router.register(r'trips', TripViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('trips/search-flights/', search_flights, name='search-flights'),
    path('test-places/', test_google_places, name='test-places'),
]
