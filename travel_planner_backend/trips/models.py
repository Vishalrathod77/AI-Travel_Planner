from django.db import models

# Create your models here.

class Trip(models.Model):
    destination = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    interests = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.destination} ({self.start_date} - {self.end_date})"

class TripDetail(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name='details')
    weather_data = models.TextField(null=True, blank=True)  # Store JSON as text
    hotel_data = models.TextField(null=True, blank=True)    # Store JSON as text
    food_data = models.TextField(null=True, blank=True)     # Store JSON as text
    
    def __str__(self):
        return f"Details for {self.trip.destination}"
