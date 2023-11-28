from rest_framework import serializers

from carpool.models import User


class UserLoginSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['name', 'email']
