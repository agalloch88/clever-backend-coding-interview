"""Tests for photo CRUD endpoints."""

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from photos.models import Photo, PhotoSource, Photographer


class PhotoListTest(APITestCase):
    """Tests for GET /api/photos/."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.photographer = Photographer.objects.create(pexels_id=1, name="Jane")
        cls.other_photographer = Photographer.objects.create(pexels_id=2, name="Bob")

        cls.photo1 = Photo.objects.create(
            pexels_id=10,
            photographer=cls.photographer,
            width=1920,
            height=1080,
            url="https://example.com/1.jpg",
            alt="Sunset over the ocean",
        )
        cls.photo2 = Photo.objects.create(
            pexels_id=11,
            photographer=cls.other_photographer,
            width=800,
            height=600,
            url="https://example.com/2.jpg",
            alt="Mountain landscape",
        )

    def test_list_returns_paginated(self) -> None:
        response = self.client.get(reverse("photo-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 2)

    def test_filter_by_photographer_id(self) -> None:
        response = self.client.get(
            reverse("photo-list"), {"photographer_id": self.photographer.id}
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["pexels_id"], 10)

    def test_filter_by_min_width(self) -> None:
        response = self.client.get(reverse("photo-list"), {"min_width": 1000})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["width"], 1920)

    def test_search_alt_text(self) -> None:
        response = self.client.get(reverse("photo-list"), {"search": "sunset"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["alt"], "Sunset over the ocean")


class PhotoDetailTest(APITestCase):
    """Tests for GET /api/photos/{id}/."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.photographer = Photographer.objects.create(pexels_id=1, name="Jane")
        cls.photo = Photo.objects.create(
            pexels_id=10,
            photographer=cls.photographer,
            width=1920,
            height=1080,
            url="https://example.com/1.jpg",
            alt="Test photo",
        )
        PhotoSource.objects.create(
            photo=cls.photo, size_label="original", url="https://example.com/1/orig.jpg"
        )
        PhotoSource.objects.create(
            photo=cls.photo, size_label="small", url="https://example.com/1/small.jpg"
        )

    def test_retrieve_with_sources(self) -> None:
        response = self.client.get(reverse("photo-detail", args=[self.photo.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["sources"]), 2)
        self.assertIn("updated_at", response.data)
        self.assertIn("owner", response.data)


class PhotoCreateTest(APITestCase):
    """Tests for POST /api/photos/."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(username="creator", password="testpass123")
        cls.photographer = Photographer.objects.create(pexels_id=1, name="Jane")

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.user)

    def test_create_authenticated(self) -> None:
        data = {
            "pexels_id": 99999,
            "photographer": self.photographer.id,
            "width": 1920,
            "height": 1080,
            "url": "https://example.com/new.jpg",
            "alt": "New photo",
        }
        response = self.client.post(reverse("photo-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        photo = Photo.objects.get(pexels_id=99999)
        self.assertEqual(photo.owner, self.user)

    def test_create_unauthenticated(self) -> None:
        self.client.force_authenticate(user=None)
        data = {
            "pexels_id": 99998,
            "photographer": self.photographer.id,
            "width": 1920,
            "height": 1080,
            "url": "https://example.com/new.jpg",
            "alt": "New photo",
        }
        response = self.client.post(reverse("photo-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PhotoUpdateDeleteTest(APITestCase):
    """Tests for PUT/DELETE /api/photos/{id}/."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.owner = User.objects.create_user(username="owner", password="testpass123")
        cls.other_user = User.objects.create_user(username="other", password="testpass123")
        cls.photographer = Photographer.objects.create(pexels_id=1, name="Jane")

    def setUp(self) -> None:
        self.photo = Photo.objects.create(
            pexels_id=self._testMethodName.encode().hex()[:8],
            photographer=self.photographer,
            owner=self.owner,
            width=1920,
            height=1080,
            url="https://example.com/owned.jpg",
            alt="Owner photo",
        )

    def test_update_as_owner(self) -> None:
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            reverse("photo-detail", args=[self.photo.id]),
            {"alt": "Updated alt"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.photo.refresh_from_db()
        self.assertEqual(self.photo.alt, "Updated alt")

    def test_update_as_non_owner(self) -> None:
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(
            reverse("photo-detail", args=[self.photo.id]),
            {"alt": "Hacked"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_as_owner(self) -> None:
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(reverse("photo-detail", args=[self.photo.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Photo.objects.filter(id=self.photo.id).exists())

    def test_delete_as_non_owner(self) -> None:
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(reverse("photo-detail", args=[self.photo.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
