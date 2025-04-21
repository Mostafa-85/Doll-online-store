from django.urls import path
from .views import (EmailConfirmation,UserSignUp,)
from rest_framework_simplejwt.views import (
TokenObtainPairView,
TokenRefreshView,
TokenBlacklistView
)

urlpatterns = [
    path('sign_up/',UserSignUp.as_view(),name='sign_up'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('logout/',TokenBlacklistView.as_view(),name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('email-confirmation/', EmailConfirmation.as_view(), name='email-confirmation'),

    ]