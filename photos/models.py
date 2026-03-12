from django.conf import settings
from django.db import models


class Photographer(models.Model):
    """A photographer sourced from the Pexels dataset."""

    pexels_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=500, blank=True)

    def __str__(self) -> str:
        return self.name


class Photo(models.Model):
    """A photo record, either imported from Pexels or user-uploaded."""

    pexels_id = models.IntegerField(unique=True)
    photographer = models.ForeignKey(
        Photographer,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    url = models.URLField(max_length=500)
    alt = models.TextField(blank=True, default="")
    avg_color = models.CharField(max_length=7, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["photographer"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["pexels_id"]),
        ]

    def __str__(self) -> str:
        return self.alt or f"Photo {self.pexels_id}"


class PhotoSource(models.Model):
    """A single size variant (e.g. 'large', 'tiny') for a Photo."""

    photo = models.ForeignKey(
        Photo,
        on_delete=models.CASCADE,
        related_name="sources",
    )
    size_label = models.CharField(max_length=20)
    url = models.URLField(max_length=500)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["photo", "size_label"],
                name="unique_photo_size_label",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.photo} - {self.size_label}"
