from rest_framework import serializers
from .models import Trip, TripDetail
import json

class TripDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripDetail
        fields = ['weather_data', 'hotel_data', 'food_data']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Convert stored JSON strings back to Python objects
        for field in ['weather_data', 'hotel_data', 'food_data']:
            if ret[field]:
                try:
                    ret[field] = json.loads(ret[field])
                except (json.JSONDecodeError, TypeError):
                    ret[field] = None
        return ret

    def to_internal_value(self, data):
        # Convert incoming Python objects to JSON strings
        internal_data = {}
        for field in ['weather_data', 'hotel_data', 'food_data']:
            value = data.get(field)
            if value:
                try:
                    internal_data[field] = json.dumps(value)
                except (TypeError, ValueError):
                    internal_data[field] = None
            else:
                internal_data[field] = None
        return super().to_internal_value(internal_data)

class TripSerializer(serializers.ModelSerializer):
    details = TripDetailSerializer(required=False)

    class Meta:
        model = Trip
        fields = ['id', 'destination', 'start_date', 'end_date', 'budget', 'interests', 'details', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        details_data = validated_data.pop('details', {})
        trip = Trip.objects.create(**validated_data)
        
        # Create TripDetail with safe JSON handling
        detail_data = {}
        for field in ['weather_data', 'hotel_data', 'food_data']:
            value = details_data.get(field)
            if value:
                try:
                    detail_data[field] = json.dumps(value)
                except (TypeError, ValueError):
                    detail_data[field] = None
            else:
                detail_data[field] = None
        
        TripDetail.objects.create(trip=trip, **detail_data)
        return trip

    def update(self, instance, validated_data):
        details_data = validated_data.pop('details', None)
        # Update trip fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update trip details if provided
        if details_data and hasattr(instance, 'details'):
            details = instance.details
            for field in ['weather_data', 'hotel_data', 'food_data']:
                value = details_data.get(field)
                if value is not None:
                    try:
                        setattr(details, field, json.dumps(value))
                    except (TypeError, ValueError):
                        setattr(details, field, None)
            details.save()
        
        return instance
