from django.contrib import admin
from .models import Trip, TripDetail

# Register your models here.

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('destination', 'start_date', 'end_date', 'budget', 'created_at')
    search_fields = ('destination',)

@admin.register(TripDetail)
class TripDetailAdmin(admin.ModelAdmin):
    list_display = ('trip',)
