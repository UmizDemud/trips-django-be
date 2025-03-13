from django.urls import path, include
from .views import LogbookViewSet, TripViewSet

from rest_framework.routers import DefaultRouter

# Set up the DRF router
router = DefaultRouter()
router.register(r"logbook", LogbookViewSet, basename="logbook")
router.register(r"trip", TripViewSet, basename="trip")

urlpatterns = [
  path("", include(router.urls)),  # Includes all logbook-related endpoints
]

