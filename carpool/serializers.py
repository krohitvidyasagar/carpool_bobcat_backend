from rest_framework import serializers

from carpool.models import User, Ride


class UserLoginSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['name', 'email']


class RideCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ride
        fields = '__all__'
