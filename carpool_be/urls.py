"""
URL configuration for carpool_be project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from carpool.views import UserRegistrationView, LoginView, UserVerifyView, UserProfileView, RideView, \
    DriverReviewListCreateView, MessageView, PassengerRideView, ImageUploadView, FindRideView

urlpatterns = [
    # API to register new users
    path('api/register', UserRegistrationView.as_view(), name=UserRegistrationView.name),
    # API to verify email address using token
    path('api/verify', UserVerifyView.as_view(), name=UserVerifyView.name),
    # API to login
    path('api/login', LoginView.as_view(), name=LoginView.name),

    # API to get or update profile
    path('api/profile', UserProfileView.as_view(), name=UserProfileView.name),

    # API to create a new ride and to list all rides as driver or passengers
    path('api/ride', RideView.as_view(), name=RideView.name),

    # API to list all nearby rides
    path('api/find-ride', FindRideView.as_view(), name=FindRideView.name),

    # API to book a ride for passenger
    path('api/passenger-ride', PassengerRideView.as_view(), name=PassengerRideView.name),

    # API to cancel a ride as a passenger
    path('api/passenger-ride/<uuid:ride_id>', PassengerRideView.as_view(), name=PassengerRideView.name),

    # API to list all reviews of a driver
    # API to leave a review for a driver
    path('api/review', DriverReviewListCreateView.as_view(), name=DriverReviewListCreateView.name),

    # API to send a chat
    # API to retrieve all messages of a chat
    path('api/ride/<uuid:ride_id>/message', MessageView.as_view(), name=MessageView.name),

    path('api/image', ImageUploadView.as_view(), name=ImageUploadView.name),
]
