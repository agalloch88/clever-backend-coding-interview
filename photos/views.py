"""Views for the photos API."""

import django_filters.rest_framework
from django.db.models import Count
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from photos.filters import PhotoFilter
from photos.models import Photo, Photographer
from photos.permissions import IsOwnerOrReadOnly
from photos.serializers import (
    PhotoCreateUpdateSerializer,
    PhotoDetailSerializer,
    PhotoListSerializer,
    PhotographerListSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)


# ── Auth ──────────────────────────────────────────────────────────────────────


class RegisterView(generics.CreateAPIView):
    """Register a new user and return JWT tokens."""

    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


# ── Health ────────────────────────────────────────────────────────────────────


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request: Request) -> Response:
    """Simple health check endpoint."""
    return Response({"status": "ok"})


# ── Photos ────────────────────────────────────────────────────────────────────


class PhotoViewSet(viewsets.ModelViewSet):
    """CRUD operations for photos with filtering and ordering."""

    filterset_class = PhotoFilter
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        OrderingFilter,
    ]
    ordering_fields = ["created_at", "width", "height"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Photo.objects.select_related("photographer")
            .prefetch_related("sources")
            .all()
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PhotoDetailSerializer
        if self.action in ("create", "update", "partial_update"):
            return PhotoCreateUpdateSerializer
        return PhotoListSerializer

    def get_permissions(self):
        if self.action in ("create",):
            return [IsAuthenticated()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [AllowAny()]


# ── Photographers ─────────────────────────────────────────────────────────────


class PhotographerViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to photographers with photo counts."""

    serializer_class = PhotographerListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Photographer.objects.annotate(photo_count=Count("photos"))

    @action(detail=True, methods=["get"])
    def photos(self, request: Request, pk=None) -> Response:
        """Return paginated photos for a specific photographer."""
        photographer = self.get_object()
        photos = (
            Photo.objects.filter(photographer=photographer)
            .select_related("photographer")
            .order_by("-created_at")
        )
        page = self.paginate_queryset(photos)
        if page is not None:
            serializer = PhotoListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = PhotoListSerializer(photos, many=True)
        return Response(serializer.data)
