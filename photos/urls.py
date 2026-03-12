from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from photos.views import RegisterView

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
