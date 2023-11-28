from django.http import HttpResponseRedirect
from rest_framework import generics
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import AuthenticationFailed, ParseError

from carpool.models import User
from carpool.service import AuthenticationUtils, EmailUtils, UserUtils
from carpool.serializers import UserLoginSerializer


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


class UpdateProfileView(generics.UpdateAPIView):
    name = 'update-profile-view'
    queryset = User.objects.all()

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

        return Response({'detail': 'Profile has been updated successfully'})
