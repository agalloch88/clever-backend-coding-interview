"""Filters for the photos API."""

import django_filters

from photos.models import Photo


class PhotoFilter(django_filters.FilterSet):
    """Filter photos by photographer, dimensions, and alt text search."""

    photographer_id = django_filters.NumberFilter(
        field_name="photographer__id",
    )
    min_width = django_filters.NumberFilter(field_name="width", lookup_expr="gte")
    max_width = django_filters.NumberFilter(field_name="width", lookup_expr="lte")
    min_height = django_filters.NumberFilter(field_name="height", lookup_expr="gte")
    max_height = django_filters.NumberFilter(field_name="height", lookup_expr="lte")
    search = django_filters.CharFilter(field_name="alt", lookup_expr="icontains")

    class Meta:
        model = Photo
        fields = [
            "photographer_id",
            "min_width",
            "max_width",
            "min_height",
            "max_height",
            "search",
        ]
