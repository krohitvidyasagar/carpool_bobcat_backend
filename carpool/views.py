import base64

from django.http import HttpResponseRedirect
from rest_framework import generics
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import AuthenticationFailed, ParseError
from datetime import datetime, timedelta
from django.utils import timezone

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance

from carpool.models import User, Ride, CarOwner, DriverReview, RidePassenger, Message
from carpool.service import AuthenticationUtils, EmailUtils, UserUtils
from carpool.serializers import UserLoginSerializer, RideSerializer, UserProfileSerializer, DriverReviewSerializer, \
    MessageSerializer, RidePassengerSerializer


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
        speaks = self.request.data.get('speaks')
        studies = self.request.data.get('studies')
        from_location = self.request.data.get('from_location')

        user.speaks = speaks
        user.studies = studies
        user.from_location = from_location
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

        rides_as_passenger_qs = RidePassenger.objects.filter(passenger__email=email)

        if rides_as_passenger_qs.exists():
            rides['passenger'] = RidePassengerSerializer(rides_as_passenger_qs, many=True).data

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
        formatted_time = datetime.strptime(received_time, '%H:%M').time()

        seats_available = self.request.data['seats_available']
        price_per_seat = self.request.data['price_per_seat']

        source_coordinates = Point(source_lat, source_lng)
        destination_coordinates = Point(destination_lat, destination_lng)

        car_owner = CarOwner.objects.filter(owner_id=user.id).first()

        ride = Ride.objects.create(
            source=source, destination=destination, date=formatted_date, time=formatted_time,
            seats_available=seats_available, price_per_seat=price_per_seat, driver=user,
            source_coordinates=source_coordinates, destination_coordinates=destination_coordinates,
            car=car_owner.car
        )

        return Response(self.get_serializer(ride).data)


class DriverReviewListCreateView(generics.ListCreateAPIView):
    name = 'rider-review-list-create-view'
    queryset = DriverReview.objects.all()
    serializer_class = DriverReviewSerializer

    def get(self, request, *args, **kwargs):
        # TODO: Modify this API according to what Kathia needs
        driver_email = self.request.query_params['driver']
        driver = User.objects.get(email=driver_email)

        profile = UserProfileSerializer(driver).data

        reviews_qs = self.get_queryset().filter(ride__driver_id=driver.id)

        reviews_serializer = DriverReviewSerializer(reviews_qs, many=True)

        data = {
            'profile': profile,
            'reviews': reviews_serializer.data
        }

        return Response(data)

    def post(self, request, *args, **kwargs):
        email = self.request.auth_context['user']
        user = User.objects.get(email=email)

        ride_id = self.request.data['ride_id']
        ride = Ride.objects.get(id=ride_id)

        # Check if user has taken the ride
        # try:
        #     ride_passenger = RidePassenger.objects.get(ride_id=ride_id, passenger_id=user.id)
        # except ObjectDoesNotExist:
        #     raise ParseError(detail='User has not taken this ride')

        driver_review = DriverReview.objects.create(
            ride=ride, passenger=user, rating=self.request.data['rating'],
            review=self.request.data['review']
        )

        serializer = self.get_serializer(driver_review)

        return Response(serializer.data)


class MessageView(generics.ListCreateAPIView):
    name = 'message-view'
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_queryset(self):
        ride_id = self.kwargs['ride_id']
        return super().get_queryset().filter(ride_id=ride_id).order_by('created_at')

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        email = self.request.auth_context['user']
        user = User.objects.get(email=email)

        ride_id = self.kwargs['ride_id']
        ride = Ride.objects.get(id=ride_id)

        message = Message.objects.create(
            ride=ride, sender=user, content=self.request.data['message']
        )

        serializer = self.get_serializer(message)
        return Response(serializer.data)


class FindRideView(generics.CreateAPIView):
    name = 'find-ride-view'
    queryset = Ride.objects.all()
    serializer_class = RideSerializer

    def post(self, request, *args, **kwargs):
        pickup_coordinates = self.request.data['pickup_coordinates']
        drop_off_coordinates = self.request.data['drop_off_coordinates']

        # Passenger details
        passenger_source = "POINT({} {})".format(pickup_coordinates['lat'], pickup_coordinates['lng'])
        passenger_destination = "POINT({} {})".format(drop_off_coordinates['lat'], drop_off_coordinates['lng'])

        # Define the time range for departure (2 hours from now)
        departure_time = datetime.strptime(self.request.data['datetime'], '%Y-%m-%dT%H:%M')
        two_hours_before = departure_time - timedelta(hours=2)
        two_hours_later = departure_time + timedelta(hours=2)

        # Find rides within 5 miles of source and destination, and within the time range
        rides = Ride.objects.filter(
            source_coordinates__distance_lte=(passenger_source, Distance(mi=5)),
            destination_coordinates__distance_lte=(passenger_destination, Distance(mi=5)),
            date=departure_time.date(),
            time__range=(two_hours_before.time(), two_hours_later.time()),
            seats_available__gte=1
        ).select_related('driver', 'car')

        available_rides = RideSerializer(rides, many=True).data

        return Response(available_rides)


class PassengerRideView(generics.CreateAPIView):
    name = 'passenger-ride-view'
    queryset = Ride.objects.all()
    serializer_class = RideSerializer

    def get(self, request, *args, **kwargs):
        pickup_coordinates = self.request.data['pickup_coordinates']
        drop_off_coordinates = self.request.data['drop_off_coordinates']

        # Passenger details
        passenger_source = "POINT({} {})".format(pickup_coordinates['lat'], pickup_coordinates['lng'])
        passenger_destination = "POINT({} {})".format(drop_off_coordinates['lat'], drop_off_coordinates['lng'])

        # Define the time range for departure (2 hours from now)
        departure_time = datetime.strptime(self.request.data['datetime'], '%m/%d/%YT%H:%M')
        two_hours_before = departure_time - timedelta(hours=2)
        two_hours_later = departure_time + timedelta(hours=2)

        # Find rides within 5 miles of source and destination, and within the time range
        rides = Ride.objects.filter(
            source_coordinates__distance_lte=(passenger_source, Distance(mi=5)),
            destination_coordinates__distance_lte=(passenger_destination, Distance(mi=5)),
            date=departure_time.date(),
            time__range=(two_hours_before.time(), two_hours_later.time()),
            seats_available__gte=1
        ).select_related('driver', 'car')

        available_rides = RideSerializer(rides, many=True).data

        return Response(available_rides)

    def post(self, request, *args, **kwargs):
        email = self.request.auth_context['user']
        user = User.objects.get(email=email)

        ride_id = self.request.data['ride_id']
        ride = Ride.objects.get(id=ride_id)

        pickup_location = self.request.data['pickup_location']
        pickup_coordinates = self.request.data['pickup_coordinates']

        drop_off_location = self.request.data['drop_off_location']
        drop_off_coordinates = self.request.data['drop_off_coordinates']

        # Passenger details
        passenger_source = "POINT({} {})".format(pickup_coordinates['lat'], pickup_coordinates['lng'])
        passenger_destination = "POINT({} {})".format(drop_off_coordinates['lat'], drop_off_coordinates['lng'])

        # Define the time range for departure (2 hours from now)
        pickup_time = datetime.strptime(self.request.data['datetime'], '%Y-%m-%dT%H:%M')

        RidePassenger.objects.create(ride=ride, passenger=user)

        ride.seats_available = ride.seats_available - 1
        ride.save()

        # TODO: Have a discussion on what the response should be
        return Response({'detail': 'Your ride has been confirmed'})


class PassengerRideCancelView(generics.DestroyAPIView):
    name = 'passenger-ride-cancel-view'
    queryset = RidePassenger.objects.all()

    def delete(self, request, *args, **kwargs):
        email = self.request.auth_context['user']
        user = User.objects.get(email=email)

        ride_id = self.kwargs['ride_id']

        ride_passenger = RidePassenger.objects.get(ride_id=ride_id, passenger_id=user.id)
        ride_passenger.delete()

        ride = Ride.objects.get(id=ride_id)
        ride.seats_available = ride.seats_available + 1
        ride.save()

        return Response({'detail': 'Your booking has been cancelled successfully'})


class ImageUploadView(generics.CreateAPIView):
    name = 'image-upload-view'
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        email = self.request.auth_context['user']
        user = User.objects.get(email=email)

        if self.request.FILES and 'profile_photo' in self.request.FILES:
            profile_photo = self.request.FILES['profile_photo']
            profile_photo_base64 = base64.b64encode(profile_photo.read()).decode('utf-8')
            user.profile_photo_base64 = profile_photo_base64

        if self.request.FILES and 'cover_photo' in self.request.FILES:
            cover_photo = self.request.FILES['cover_photo']
            cover_photo_base64 = base64.b64encode(cover_photo.read()).decode('utf-8')
            user.cover_photo_base64 = cover_photo_base64

        user.save()

        return Response({'detail': 'Image uploaded successfully.'})
