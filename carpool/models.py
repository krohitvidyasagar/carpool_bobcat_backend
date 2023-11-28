import uuid

from django.contrib.gis.db import models


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100, null=False)
    email = models.EmailField(max_length=100, null=False)
    phone = models.CharField(max_length=20, null=True)
    password = models.CharField(max_length=100, null=False)
    has_car = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    api_secret = models.CharField(max_length=45, null=True)
    bio = models.TextField(null=True, blank=True)

    # Add image here

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user'
        ordering = ['-created_at']


class Car(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    model = models.CharField(max_length=50, null=False)
    make = models.CharField(max_length=50, null=False)
    color = models.CharField(max_length=20, null=False)
    year = models.IntegerField(null=False)
    license_plate = models.CharField(null=False, max_length=15, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'car'
        ordering = ['-created_at']


class CarOwner(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'car_owner'
        ordering = ['-created_at']
        unique_together = ['owner', 'car']


class Ride(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    source = models.CharField(max_length=200, null=False)
    source_coordinates = models.PointField(null=False)

    destination = models.CharField(max_length=200, null=False)
    destination_coordinates = models.PointField(null=False)

    driver = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE, null=True)

    date = models.DateField(null=False)
    time = models.TimeField(null=False)
    seats_available = models.IntegerField(null=False)
    price_per_seat = models.FloatField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ride'
        ordering = ['-created_at']


class RidePassenger(models.Model):
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE)
    passenger = models.ForeignKey(User, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ride_passenger'
        ordering = ['-created_at']


class RideReview(models.Model):
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    rating = models.IntegerField(null=False)
    review = models.TextField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ride_review'
        ordering = ['-created_at']
