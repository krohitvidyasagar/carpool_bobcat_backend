from rest_framework import serializers
from django.db.models import Avg

from carpool.models import User, Ride, Car, CarOwner, DriverReview, Message


class UserLoginSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone', 'has_car']


class CarSerializer(serializers.ModelSerializer):

    class Meta:
        model = Car
        fields = ['id', 'model', 'make', 'color', 'year', 'license_plate']


class UserProfileSerializer(serializers.ModelSerializer):
    cars = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    trips = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone', 'has_car', 'bio', 'cars', 'speaks', 'studies',
                  'from_location', 'rating', 'trips']

    def get_rating(self, obj):
        avg_value = DriverReview.objects.filter(ride__driver_id=obj.id).aggregate(avg_field=Avg('rating'))
        return avg_value['avg_field']

    def get_trips(self, obj):
        return Ride.objects.filter(driver_id=obj.id).count()

    def get_cars(self, obj):
        car_ids = CarOwner.objects.filter(owner_id=obj.id).values_list('car_id', flat=True)
        cars_qs = Car.objects.filter(id__in=car_ids)

        if cars_qs.exists():
            return CarSerializer(cars_qs, many=True).data
        else:
            return []


class RideSerializer(serializers.ModelSerializer):
    driver = serializers.SerializerMethodField()
    car = serializers.SerializerMethodField()
    source_coordinates = serializers.SerializerMethodField()
    destination_coordinates = serializers.SerializerMethodField()

    class Meta:
        model = Ride
        fields = ['id', 'source', 'source_coordinates', 'destination', 'destination_coordinates', 'driver',
                  'car', 'date', 'time', 'seats_available', 'price_per_seat']

    def get_driver(self, obj):
        driver = User.objects.get(id=obj.driver.id)
        return UserLoginSerializer(driver).data

    def get_car(self, obj):
        car = Car.objects.get(id=obj.car.id)
        return CarSerializer(car).data

    def get_source_coordinates(self, obj):
        coordinates = {
            "lat": obj.source_coordinates.y,
            "lng": obj.source_coordinates.x
        }
        return coordinates

    def get_destination_coordinates(self, obj):
        coordinates = {
            "lat": obj.destination_coordinates.y,
            "lng": obj.destination_coordinates.x
        }
        return coordinates


class RideMinSerializer(serializers.ModelSerializer):
    driver = serializers.SerializerMethodField()
    car = serializers.SerializerMethodField()

    class Meta:
        model = Ride
        fields = ['id', 'driver', 'car', 'date', 'time', 'seats_available', 'price_per_seat',
                  'source', 'destination']

    def get_driver(self, obj):
        driver = User.objects.get(id=obj.driver.id)
        return UserLoginSerializer(driver).data

    def get_car(self, obj):
        car = Car.objects.get(id=obj.car.id)
        return CarSerializer(car).data


class DriverReviewSerializer(serializers.ModelSerializer):
    ride = RideMinSerializer()
    passenger = UserLoginSerializer()

    class Meta:
        model = DriverReview
        fields = ['ride', 'passenger', 'rating', 'review', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    ride = RideMinSerializer()
    sender = UserLoginSerializer()
    message = serializers.CharField(source='content')

    class Meta:
        model = Message
        fields = ['ride', 'sender', 'message', 'timestamp', 'created_at']
