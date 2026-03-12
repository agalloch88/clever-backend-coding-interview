from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from photos.views import PhotoViewSet, PhotographerViewSet, RegisterView, health_check

router = DefaultRouter()
router.register(r"photos", PhotoViewSet, basename="photo")
router.register(r"photographers", PhotographerViewSet, basename="photographer")

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Health
    path("health/", health_check, name="health_check"),
    # Router
    path("", include(router.urls)),
]
