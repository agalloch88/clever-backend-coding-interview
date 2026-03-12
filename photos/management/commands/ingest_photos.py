"""Management command to import photos.csv into the database."""

import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from photos.models import Photo, PhotoSource, Photographer

SIZE_LABELS = [
    "original",
    "large2x",
    "large",
    "medium",
    "small",
    "portrait",
    "landscape",
    "tiny",
]


class Command(BaseCommand):
    """Import the Pexels photos.csv dataset into Photographer, Photo, and PhotoSource models."""

    help = "Ingest photos.csv from the project root into the database."

    def handle(self, *args, **options) -> None:
        csv_path = Path(settings.BASE_DIR) / "photos.csv"
        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f"CSV not found: {csv_path}"))
            return

        existing_pexels_ids = set(Photo.objects.values_list("pexels_id", flat=True))

        photos_created = 0
        photographers_created = 0
        skipped = 0
        errors = 0
        seen_photographer_ids: dict[int, Photographer] = {}

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):
                try:
                    pexels_id = int(row["id"])

                    if pexels_id in existing_pexels_ids:
                        skipped += 1
                        continue

                    photographer_pexels_id = int(row["photographer_id"])

                    if photographer_pexels_id in seen_photographer_ids:
                        photographer = seen_photographer_ids[photographer_pexels_id]
                        created = False
                    else:
                        photographer, created = Photographer.objects.get_or_create(
                            pexels_id=photographer_pexels_id,
                            defaults={
                                "name": row["photographer"].strip(),
                                "url": row.get("photographer_url", ""),
                            },
                        )
                        seen_photographer_ids[photographer_pexels_id] = photographer

                    if created:
                        photographers_created += 1

                    with transaction.atomic():
                        photo = Photo.objects.create(
                            pexels_id=pexels_id,
                            photographer=photographer,
                            width=int(row["width"]),
                            height=int(row["height"]),
                            url=row["url"],
                            alt=row.get("alt", ""),
                            avg_color=row.get("avg_color", ""),
                        )

                        sources = [
                            PhotoSource(
                                photo=photo,
                                size_label=label,
                                url=row[f"src.{label}"],
                            )
                            for label in SIZE_LABELS
                            if row.get(f"src.{label}")
                        ]
                        PhotoSource.objects.bulk_create(sources)

                    existing_pexels_ids.add(pexels_id)
                    photos_created += 1

                except Exception as exc:
                    errors += 1
                    self.stderr.write(
                        self.style.WARNING(f"Row {row_num}: {exc}")
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {photos_created} photos, {photographers_created} photographers. "
                f"Skipped {skipped} existing."
            )
        )
        if errors:
            self.stderr.write(
                self.style.WARNING(f"{errors} rows had errors.")
            )
