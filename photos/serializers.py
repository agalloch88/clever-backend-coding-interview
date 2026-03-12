"""Serializers for the photos API."""

from django.contrib.auth.models import User
from rest_framework import serializers

from photos.models import Photo, PhotoSource, Photographer


# ── Auth ──────────────────────────────────────────────────────────────────────


class UserRegistrationSerializer(serializers.Serializer):
    """Handles user registration with password confirmation."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        if User.objects.filter(email__iexact=attrs["email"]).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )
        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError(
                {"username": "A user with this username already exists."}
            )
        return attrs

    def create(self, validated_data: dict) -> User:
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Read-only representation of a user."""

    class Meta:
        model = User
        fields = ["id", "username", "email"]
        read_only_fields = fields


# ── Photographers ─────────────────────────────────────────────────────────────


class PhotographerListSerializer(serializers.ModelSerializer):
    """Photographer with an aggregated photo count."""

    photo_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Photographer
        fields = ["id", "pexels_id", "name", "url", "photo_count"]


# ── Photo Sources ─────────────────────────────────────────────────────────────


class PhotoSourceSerializer(serializers.ModelSerializer):
    """A single size variant for a photo."""

    class Meta:
        model = PhotoSource
        fields = ["id", "size_label", "url"]


# ── Photos ────────────────────────────────────────────────────────────────────


class _PhotographerBriefSerializer(serializers.ModelSerializer):
    """Minimal photographer info for nesting inside photo serializers."""

    class Meta:
        model = Photographer
        fields = ["id", "name"]


class PhotoListSerializer(serializers.ModelSerializer):
    """Compact photo representation for list endpoints."""

    photographer = _PhotographerBriefSerializer(read_only=True)

    class Meta:
        model = Photo
        fields = [
            "id",
            "pexels_id",
            "width",
            "height",
            "alt",
            "url",
            "avg_color",
            "photographer",
            "created_at",
        ]


class PhotoDetailSerializer(PhotoListSerializer):
    """Full photo representation including sources and owner."""

    sources = PhotoSourceSerializer(many=True, read_only=True)
    owner = serializers.CharField(source="owner.username", default=None, read_only=True)

    class Meta(PhotoListSerializer.Meta):
        fields = PhotoListSerializer.Meta.fields + [
            "sources",
            "updated_at",
            "owner",
        ]


class PhotoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating user-owned photos."""

    class Meta:
        model = Photo
        fields = ["pexels_id", "photographer", "width", "height", "alt", "url", "avg_color"]

    def validate_width(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError("Width must be a positive integer.")
        return value

    def validate_height(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError("Height must be a positive integer.")
        return value

    def create(self, validated_data: dict) -> Photo:
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)
