# CLAUDE.md

## Project
Backend take-home for Clever Real Estate. Building a Django REST Framework photo management API.

## Stack
- Python 3.12+, Django 5.x, Django REST Framework
- PostgreSQL (with SQLite fallback for local dev)
- JWT auth via simplejwt
- OpenAPI docs via drf-spectacular
- Filtering via django-filter

## Data
- photos.csv in project root: Pexels dataset with 8 image size variants per photo
- Columns: id, width, height, url, photographer, photographer_url, photographer_id, avg_color, src.original, src.large2x, src.large, src.medium, src.small, src.portrait, src.landscape, src.tiny, alt

## Architecture Decisions (FOLLOW THESE)
- Normalized schema: Photographer, Photo, PhotoSource as separate models
- PhotoSource stores the 8 size variants (not JSON blob on Photo)
- Photographer is extracted from CSV, not a user account
- Photo.owner is FK to User for user-uploaded photos
- Idempotent CSV ingestion (skip existing pexels_ids)
- Consistent error envelope on all error responses
- IsOwnerOrReadOnly custom permission for write operations

## Code Style
- Docstrings on all views, serializers, and management commands
- Type hints on function signatures
- No unused imports
- Clean, descriptive commit messages (I commit manually)

## Don't
- Don't create Docker files (not asked for)
- Don't add Celery or async tasks
- Don't over-engineer. Clean CRUD > sprawling features.
- Don't commit for me. Just write the code.