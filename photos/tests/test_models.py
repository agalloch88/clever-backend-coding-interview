"""Tests for photos models."""

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from photos.models import Photo, PhotoSource, Photographer


class PhotographerModelTest(TestCase):
    """Tests for the Photographer model."""

    def test_create_photographer(self) -> None:
        photographer = Photographer.objects.create(
            pexels_id=999, name="Test Photographer", url="https://example.com"
        )
        self.assertEqual(photographer.name, "Test Photographer")
        self.assertEqual(photographer.pexels_id, 999)

    def test_str_returns_name(self) -> None:
        photographer = Photographer.objects.create(pexels_id=1, name="Jane Doe")
        self.assertEqual(str(photographer), "Jane Doe")

    def test_unique_pexels_id(self) -> None:
        Photographer.objects.create(pexels_id=1, name="First")
        with self.assertRaises(IntegrityError):
            Photographer.objects.create(pexels_id=1, name="Duplicate")


class PhotoModelTest(TestCase):
    """Tests for the Photo model."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.photographer = Photographer.objects.create(pexels_id=1, name="Jane")

    def test_str_returns_alt(self) -> None:
        photo = Photo.objects.create(
            pexels_id=10,
            photographer=self.photographer,
            width=1920,
            height=1080,
            url="https://example.com/photo.jpg",
            alt="A beautiful sunset",
        )
        self.assertEqual(str(photo), "A beautiful sunset")

    def test_str_fallback_when_alt_empty(self) -> None:
        photo = Photo.objects.create(
            pexels_id=11,
            photographer=self.photographer,
            width=800,
            height=600,
            url="https://example.com/photo2.jpg",
        )
        self.assertEqual(str(photo), "Photo 11")

    def test_owner_set_null_on_delete(self) -> None:
        user = User.objects.create_user(username="owner", password="pass1234")
        photo = Photo.objects.create(
            pexels_id=12,
            photographer=self.photographer,
            owner=user,
            width=640,
            height=480,
            url="https://example.com/photo3.jpg",
        )
        user.delete()
        photo.refresh_from_db()
        self.assertIsNone(photo.owner)


class PhotoSourceModelTest(TestCase):
    """Tests for the PhotoSource model."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.photographer = Photographer.objects.create(pexels_id=1, name="Jane")
        cls.photo = Photo.objects.create(
            pexels_id=10,
            photographer=cls.photographer,
            width=1920,
            height=1080,
            url="https://example.com/photo.jpg",
            alt="Test photo",
        )

    def test_str(self) -> None:
        source = PhotoSource.objects.create(
            photo=self.photo, size_label="large", url="https://example.com/large.jpg"
        )
        self.assertEqual(str(source), "Test photo - large")

    def test_unique_photo_size_label_constraint(self) -> None:
        PhotoSource.objects.create(
            photo=self.photo, size_label="medium", url="https://example.com/medium.jpg"
        )
        with self.assertRaises(IntegrityError):
            PhotoSource.objects.create(
                photo=self.photo, size_label="medium", url="https://example.com/medium2.jpg"
            )
