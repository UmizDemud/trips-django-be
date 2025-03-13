
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, viewsets
from .models import Trip, Logbook
from .serializer import TripSerializer, LogbookSerializer

class LogbookViewSet(viewsets.ModelViewSet):
    queryset = Logbook.objects.all().order_by("-created_at")
    serializer_class = LogbookSerializer
    
    
    def update(self, request, *args, **kwargs):
        print("Request data:", request.data)  # Log incoming data
        return super().update(request, *args, **kwargs)

    filter_backends = [DjangoFilterBackend, OrderingFilter]  # Enable filtering & sorting
    filterset_fields = ["date", "initials", "trip"]  # Allow filtering by these fields
    ordering_fields = ["date", "created_at", "updated_at"]  # Allow sorting
    ordering = ["-created_at"]  # Default ordering
    
    

class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all().order_by("-start_date")
    serializer_class = TripSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]  # Enable filtering & sorting
    filterset_fields = [ "cycle_hours"]  # Allow filtering by these fields
    ordering_fields = ["start_date"]  # Allow sorting
    ordering = ["-start_date"]  # Default ordering



"""
@api_view(['GET'])
def get_trips(request):
  trips = Trip.objects.all();
  serializer = TripSerializer(trips, many=True)
  return Response(serializer.data)
  
@api_view(['POST'])
def create_trip(request):
  serializer = TripSerializer(data=request.data)
  if not serializer.is_valid():
    print(serializer.errors)  # This will show the actual validation errors

  if serializer.is_valid():
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)
  return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
"""