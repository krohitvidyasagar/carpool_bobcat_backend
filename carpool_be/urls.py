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

from carpool.views import UserRegistrationView, LoginView, UserVerifyView, UpdateProfileView, RideView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/register', UserRegistrationView.as_view(), name=UserRegistrationView.name),
    path('api/login', LoginView.as_view(), name=LoginView.name),

    path('api/verify', UserVerifyView.as_view(), name=UserVerifyView.name),

    path('api/ride', RideView.as_view(), name=RideView.name),

    # Add an API for forgot password?

    path('api/profile', UpdateProfileView.as_view(), name=UpdateProfileView.name)
]
