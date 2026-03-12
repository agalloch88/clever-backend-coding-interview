"""Tests for photographer endpoints."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from photos.models import Photo, Photographer


class PhotographerViewSetTest(APITestCase):
    """Tests for /api/photographers/."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.photographer = Photographer.objects.create(pexels_id=1, name="Jane")
        cls.empty_photographer = Photographer.objects.create(pexels_id=2, name="Bob")

        Photo.objects.create(
            pexels_id=10,
            photographer=cls.photographer,
            width=1920,
            height=1080,
            url="https://example.com/1.jpg",
            alt="Photo one",
        )
        Photo.objects.create(
            pexels_id=11,
            photographer=cls.photographer,
            width=800,
            height=600,
            url="https://example.com/2.jpg",
            alt="Photo two",
        )

    def test_list_with_photo_count(self) -> None:
        response = self.client.get(reverse("photographer-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = {r["name"]: r for r in response.data["results"]}
        self.assertEqual(results["Jane"]["photo_count"], 2)
        self.assertEqual(results["Bob"]["photo_count"], 0)

    def test_retrieve(self) -> None:
        response = self.client.get(
            reverse("photographer-detail", args=[self.photographer.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Jane")

    def test_photographer_photos_action(self) -> None:
        response = self.client.get(
            reverse("photographer-photos", args=[self.photographer.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertIn("results", response.data)
