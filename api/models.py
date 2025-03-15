from django.db import models
from django.utils import timezone


class Location(models.Model):
    LOCATION_TYPES = [
        ('fuel', 'Fuel Stop'),
        ('current', 'Current'),
        ('pickup', 'Pickup'),
        ('dropoff', 'Dropoff'),
    ]

    name      = models.CharField(max_length=255)
    type      = models.CharField(max_length=10, choices=LOCATION_TYPES)
    latitude  = models.FloatField()
    longitude = models.FloatField()
    
    distance = models.FloatField(null=True, blank=True)
    time = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)  # Set on creation

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Trip(models.Model):
    locations   = models.ManyToManyField(Location, related_name="trips")
    cycle_hours = models.DecimalField(max_digits=5, decimal_places=2)  # e.g. 10.5 hours

    start_date  = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)  # Set on creation

    def __str__(self):
        return f"Trip at {self.start_date}"


class Logbook(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="logbooks", null=True, blank=True)
    date = models.DateTimeField()
    initials = models.CharField(max_length=10)
    created_at = models.DateTimeField(default=timezone.now)  # Set on creation
    updated_at = models.DateTimeField(auto_now=True)  # Update on save

    def __str__(self):
        return f"Logbook {self.id} - {self.date}"
"""
    # Unused fields for future
    driver_number = models.CharField(max_length=50, blank=True)
    signature = models.CharField(max_length=255, blank=True)
    co_driver = models.CharField(max_length=255, blank=True)
    home_operating_center = models.CharField(max_length=255, blank=True)
    vehicle_no = models.CharField(max_length=50, blank=True)
    trailer_no = models.CharField(max_length=50, blank=True)
    other_trailers = models.JSONField(blank=True, null=True)  # Stores a list of strings
    shipper = models.CharField(max_length=255, blank=True)
    load_id = models.CharField(max_length=255, blank=True)
"""


class Remark(models.Model):
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    commodity = models.CharField(max_length=255)
    detail = models.TextField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Remark: {self.city}, {self.state}"


class Increment(models.Model):
    DUTY_STATUS_CHOICES = [
        ("OFF DUTY", "Off Duty"),
        ("SLEEPER BERTH", "Sleeper Berth"),
        ("DRIVING", "Driving"),
        ("ON DUTY", "On Duty"),
    ]

    logbook = models.ForeignKey(Logbook, on_delete=models.CASCADE, related_name="increments", null=True, blank=True)
    dutyStatus = models.CharField(max_length=20, choices=DUTY_STATUS_CHOICES)
    remark = models.OneToOneField(Remark, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Increment ({self.dutyStatus}) - Logbook {self.logbook.id}"

