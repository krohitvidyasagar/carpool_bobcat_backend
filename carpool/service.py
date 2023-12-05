from datetime import datetime
from django.core.mail import send_mail

import bcrypt
import jwt
import re
import secrets

from carpool.models import Car, CarOwner
from carpool.serializers import UserLoginSerializer
from carpool_be import settings


class AuthenticationUtils:
    bcrypt_salt = b'$2b$12$Lr2f5Vp8q5yn3tYr.AD2Uu'

    @classmethod
    def get_user_claims(cls, authenticated_user):
        return {
            'claims': UserLoginSerializer(authenticated_user).data
        }

    @classmethod
    def validate_email(cls, email):
        pattern = r'^[a-zA-Z0-9._-]+@txstate\.edu$'

        if not re.match(pattern, email):
            return False
        else:
            return True

    @classmethod
    def get_bcrypt_salt(cls):
        return cls.bcrypt_salt

    @classmethod
    def get_hashed_password(cls, password):
        return bcrypt.hashpw(password, cls.bcrypt_salt)

    @classmethod
    def get_user_access_token(cls, user_claims):
        claims_obj = {
            **user_claims,
            'type': 'access',
            'exp': datetime.utcnow() + settings.JWTConfig['ACCESS_TOKEN_LIFETIME']
        }

        return jwt.encode(claims_obj, settings.JWTConfig['SIGNING_KEY'], settings.JWTConfig['ALGORITHM'])

    @classmethod
    def get_user_refresh_token(cls, user_claims):
        claims_obj = {
            **user_claims,
            'type': 'refresh',
            'exp': datetime.utcnow() + settings.JWTConfig['REFRESH_TOKEN_LIFETIME']
        }

        return jwt.encode(claims_obj, settings.JWTConfig['SIGNING_KEY'], settings.JWTConfig['ALGORITHM'])


class EmailUtils:

    @classmethod
    def send_verification_email(cls, user, attachment_path=None):
        api_secret = cls.generate_email_verification_api_secret()

        # Save api_secret into the database
        user.api_secret = api_secret
        user.save()

        verification_url = f'http://127.0.0.1:8000/api/verify?token={api_secret}'

        body = f'''
        <p>Dear {user.name},</p>

        <p>We hope this email finds you well. On behalf of the entire team at Bobcat Carpool, we want to express our 
        sincere gratitude for choosing our service and joining our carpooling community.</p>

        <p>Your decision to sign up not only contributes to reducing traffic congestion but also promotes a more 
        sustainable and eco-friendly way of commuting. We believe in the power of community-driven initiatives, and 
        your participation is a valuable addition to our growing network.</p>

        <p>As a member of Bobcat Carpool, you now have the opportunity to connect with like-minded 
        individuals, share rides, and make a positive impact on the environment. We are committed to providing you 
        with a seamless and enjoyable carpooling experience.</p>

        <a href="{verification_url}">Please click on this link to confirm your email address</a>

        <p>Best regards,</p>
        <p>Rohit</p>
        <p>Bobcat Carpool</p>
        '''
        subject = "Thank You for Joining the Bobcat Carpooling Community!"

        cls.send_email(user.email, subject, body)

    @classmethod
    def send_ride_confirmation_email(cls, user, ride_passenger):
        subject = "Booking Confirmation: Your Ride Has Been Reserved"

        body = f'''
        <p>Dear {user.name},</p>
        
        <p>We trust this message finds you well.</p>

        <p>I'm pleased to inform you that a traveler has booked a ride in Bobcat carpool.</p>
        
        <ul>
        <li>Number of Passengers: 1</li>
        <li>Pick-up Location: {ride_passenger.pickup_location}</li>
        <li>Drop-off Location: {ride_passenger.drop_off_location}</li>
        <li>Drop-off Location: {ride_passenger.drop_off_location}</li>
        </ul>

        <p>Your willingness to share your journey is greatly appreciated. 
        Your scheduled ride is an important part of our community-driven service.</p>

        <p>Please ensure that you're prepared to accommodate the passengers and provide a safe and comfortable trip 
        from the pick-up point to the drop-off location.</p>
        
        <p>Thank you for contributing to our carpooling initiative!</p>
        
        <p>Best regards,</p>
        <p>Rohit</p>
        <p>Bobcat Carpool</p>
        '''
        cls.send_email(user.email, subject, body)

    @classmethod
    def generate_email_verification_api_secret(cls):
        return secrets.token_urlsafe()

    @classmethod
    def send_email(cls, receiver_email, subject, body, attachment_path=None):
        send_mail(
            subject,
            '',
            settings.EMAIL_HOST_USER,
            [receiver_email],
            html_message=body,
            fail_silently=False
        )


class UserUtils:

    @classmethod
    def add_cars_of_user(cls, user, cars_array):
        cars = []
        for car in cars_array:
            cars.append(Car(model=car['model'], make=car['make'], color=car['color'], year=car['year'],
                            license_plate=car['license_plate']))

        Car.objects.bulk_create(cars, ignore_conflicts=True)

        license_plates = [car['license_plate'] for car in cars_array]

        cars_qs = Car.objects.filter(license_plate__in=license_plates)

        car_owners = []
        for car_obj in cars_qs:
            car_owners.append(CarOwner(owner=user, car=car_obj))

        CarOwner.objects.bulk_create(car_owners, ignore_conflicts=True)

        user.has_car = True
        user.save()

