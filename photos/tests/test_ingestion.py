"""Tests for the ingest_photos management command."""

from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from photos.models import Photo, PhotoSource, Photographer

FIXTURE_CSV = Path(__file__).parent / "fixtures" / "test_photos.csv"


class IngestPhotosCommandTest(TestCase):
    """Tests for the ingest_photos management command."""

    @patch("photos.management.commands.ingest_photos.Path")
    def test_ingest_creates_correct_counts(self, mock_path_cls) -> None:
        mock_path_cls.return_value.__truediv__ = lambda self, other: FIXTURE_CSV
        mock_path_cls.return_value.__truediv__.return_value = FIXTURE_CSV

        call_command("ingest_photos")

        self.assertEqual(Photo.objects.count(), 4)
        self.assertEqual(Photographer.objects.count(), 2)
        self.assertEqual(PhotoSource.objects.count(), 32)  # 4 photos * 8 sources

        alice = Photographer.objects.get(pexels_id=1001)
        self.assertEqual(alice.name, "Alice")
        self.assertEqual(alice.photos.count(), 2)

        bob = Photographer.objects.get(pexels_id=1002)
        self.assertEqual(bob.name, "Bob")
        self.assertEqual(bob.photos.count(), 2)

    @patch("photos.management.commands.ingest_photos.Path")
    def test_ingest_idempotent(self, mock_path_cls) -> None:
        mock_path_cls.return_value.__truediv__ = lambda self, other: FIXTURE_CSV
        mock_path_cls.return_value.__truediv__.return_value = FIXTURE_CSV

        call_command("ingest_photos")
        call_command("ingest_photos")

        self.assertEqual(Photo.objects.count(), 4)
        self.assertEqual(Photographer.objects.count(), 2)

    @patch("photos.management.commands.ingest_photos.Path")
    def test_ingest_skips_existing(self, mock_path_cls) -> None:
        mock_path_cls.return_value.__truediv__ = lambda self, other: FIXTURE_CSV
        mock_path_cls.return_value.__truediv__.return_value = FIXTURE_CSV

        photographer = Photographer.objects.create(pexels_id=1001, name="Alice")
        Photo.objects.create(
            pexels_id=100,
            photographer=photographer,
            width=100,
            height=100,
            url="https://example.com/existing.jpg",
        )

        call_command("ingest_photos")

        self.assertEqual(Photo.objects.count(), 4)
        existing = Photo.objects.get(pexels_id=100)
        self.assertEqual(existing.url, "https://example.com/existing.jpg")

    @patch("photos.management.commands.ingest_photos.Path")
    def test_ingest_handles_empty_alt_and_strips_names(self, mock_path_cls) -> None:
        mock_path_cls.return_value.__truediv__ = lambda self, other: FIXTURE_CSV
        mock_path_cls.return_value.__truediv__.return_value = FIXTURE_CSV

        call_command("ingest_photos")

        empty_alt_photo = Photo.objects.get(pexels_id=400)
        self.assertEqual(empty_alt_photo.alt, "")
        self.assertEqual(str(empty_alt_photo), "Photo 400")

        bob = Photographer.objects.get(pexels_id=1002)
        self.assertEqual(bob.name, "Bob")
