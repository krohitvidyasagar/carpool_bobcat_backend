from django.http import HttpResponseRedirect
from rest_framework import generics
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import AuthenticationFailed, ParseError
from datetime import datetime

from django.contrib.gis.geos import Point

from carpool.models import User, Ride, CarOwner
from carpool.service import AuthenticationUtils, EmailUtils, UserUtils
from carpool.serializers import UserLoginSerializer, RideSerializer, UserProfileSerializer


class UserRegistrationView(generics.CreateAPIView):
    name = 'user-registration-view'
    queryset = User.objects.all()
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        email = self.request.data.get('email')

        # Check if the user already exists in the database
        try:
            user = User.objects.get(email=email)

            # If a verified user with the same email address already exists, raise error
            if user.is_verified:
                raise ParseError(detail='A user with the same email address already exists')
            else:
                # If a user with the same email address exists, but is not verified send verification email
                EmailUtils.send_verification_email(user)

        except ObjectDoesNotExist:
            name = self.request.data.get('name')

            if not AuthenticationUtils.validate_email(email):
                raise ParseError(detail='Invalid email')

            phone = self.request.data.get('phone')
            password = self.request.data.get('password')

            hashed_password = AuthenticationUtils.get_hashed_password(password.encode('utf-8'))

            user = User.objects.create(name=name, email=email.lower(), password=hashed_password)

            has_car = self.request.data.get('has_car')
            if has_car:
                cars_array = self.request.data.get('cars')
                UserUtils.add_cars_of_user(user, cars_array)

            if phone:
                user.phone = phone
                user.save()

            EmailUtils.send_verification_email(user)

            return Response({'detail': 'Please check your inbox to confirm your email address'})


class LoginView(generics.CreateAPIView):
    name = 'user-registration-view'
    queryset = User.objects.all()
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        email = self.request.data['email']
        password = self.request.data['password']

        try:
            authenticated_user = User.objects.get(email__iexact=email)

            hashed_password = AuthenticationUtils.get_hashed_password(password.encode('utf-8'))

            if str(hashed_password) != authenticated_user.password:
                raise ObjectDoesNotExist()

            if not authenticated_user.is_verified:
                raise ParseError(detail='Please verify your email before logging in.')

            user_claims = AuthenticationUtils.get_user_claims(authenticated_user)

            access = AuthenticationUtils.get_user_access_token(user_claims)
            refresh = AuthenticationUtils.get_user_refresh_token(user_claims)

            return Response({
                'user': UserLoginSerializer(authenticated_user).data,
                'access': access,
                'refresh': refresh

            })

        except ObjectDoesNotExist:
            raise AuthenticationFailed(detail='Authentication Error')


class UserVerifyView(generics.ListAPIView):
    name = 'user-verify-view'
    queryset = User.objects.all()
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        api_key = self.request.query_params.get('token')

        try:
            user = User.objects.get(api_secret=api_key)

            user.is_verified = True
            user.save()

            return HttpResponseRedirect(redirect_to='http://localhost:8080')

        except ObjectDoesNotExist:
            raise ParseError(detail='User not found')


class UserProfileView(generics.RetrieveUpdateAPIView):
    name = 'user-profile-view'
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer

    def retrieve(self, request, *args, **kwargs):
        email = self.request.auth_context['user']
        user = User.objects.get(email=email)

        return Response(self.get_serializer(user).data)

    def patch(self, request, *args, **kwargs):
        email = self.request.auth_context['user']
        user = User.objects.get(email=email)

        phone = self.request.data.get('phone')

        user.phone = phone
        user.save()

        # Add a method here to add car information here
        has_car = self.request.data.get('has_car')
        if has_car:
            cars_array = self.request.data.get('cars')
            UserUtils.add_cars_of_user(user, cars_array)

        return Response(self.get_serializer(user).data)


class RideView(generics.ListCreateAPIView):
    name = 'ride-view'
    queryset = Ride.objects.all()
    serializer_class = RideSerializer

    def list(self, request, *args, **kwargs):
        email = self.request.auth_context['user']

        rides = {
            "driver": [],
            "passenger": []
        }

        rides_as_driver_qs = self.get_queryset().filter(driver__email=email)

        if rides_as_driver_qs.exists():
            rides['driver'] = RideSerializer(rides_as_driver_qs, many=True).data

        return Response(rides)

    def post(self, request, *args, **kwargs):
        email = self.request.auth_context['user']
        user = User.objects.get(email=email)

        source = self.request.data['source']
        source_lat = self.request.data['source_coordinates']['lat']
        source_lng = self.request.data['source_coordinates']['lng']

        destination = self.request.data['destination']
        destination_lat = self.request.data['destination_coordinates']['lat']
        destination_lng = self.request.data['destination_coordinates']['lng']

        received_date = self.request.data['date']
        received_time = self.request.data['time']

        # Convert string to date and time objects
        formatted_date = datetime.strptime(received_date, '%Y-%m-%d').date()
        formatted_time = datetime.strptime(received_time, '%I:%M %p').time()

        seats_available = self.request.data['seats_available']
        price_per_seat = self.request.data['price_per_seat']

        source_coordinates = Point(source_lat, source_lng)
        destination_coordinates = Point(destination_lat, destination_lng)

        car_id = self.request.data['car_id']
        car_owner = CarOwner.objects.get(car_id=car_id, owner_id=user.id)

        ride = Ride.objects.create(
            source=source, destination=destination, date=formatted_date, time=formatted_time,
            seats_available=seats_available, price_per_seat=price_per_seat, driver=user,
            source_coordinates=source_coordinates, destination_coordinates=destination_coordinates,
            car=car_owner.car
        )

        return Response(self.get_serializer(ride).data)
