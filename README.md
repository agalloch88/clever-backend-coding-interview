# Photo Management API

RESTful API for managing a photo library, built with Django REST Framework. JWT authentication, photo CRUD with ownership-based authorization, photographer browsing, filtering and search, and auto-generated OpenAPI docs.

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/backend-coding-interview
cd backend-coding-interview

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # SQLite works out of the box, edit for PostgreSQL
python manage.py migrate
python manage.py ingest_photos # loads the Pexels dataset
python manage.py runserver
```

Visit [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/) for the interactive Swagger UI.

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register/` | No | Create account, returns JWT tokens |
| POST | `/api/auth/login/` | No | Get JWT tokens |
| POST | `/api/auth/refresh/` | No | Refresh access token |
| GET | `/api/photos/` | No | List photos (paginated, filterable) |
| GET | `/api/photos/:id/` | No | Photo detail with all size variants |
| POST | `/api/photos/` | Yes | Create a new photo |
| PUT/PATCH | `/api/photos/:id/` | Yes (owner) | Update your photo |
| DELETE | `/api/photos/:id/` | Yes (owner) | Delete your photo |
| GET | `/api/photographers/` | No | List photographers with photo counts |
| GET | `/api/photographers/:id/` | No | Photographer detail |
| GET | `/api/photographers/:id/photos/` | No | Photos by photographer |
| GET | `/api/health/` | No | Health check |
| GET | `/api/docs/` | No | Interactive Swagger UI |
| GET | `/api/schema/` | No | Raw OpenAPI schema |

## Filtering & Search

```
GET /api/photos/?photographer_id=123
GET /api/photos/?min_width=1920&max_width=4000
GET /api/photos/?min_height=1080
GET /api/photos/?search=beach
GET /api/photos/?ordering=-created_at
GET /api/photos/?ordering=width
```

All filters can be combined. Pagination is included by default (20 per page).

## Architecture Decisions

**Django + DRF.** The challenge mentioned Django as a primary framework at Clever, so I went with what matches the production stack. DRF gives you a mature REST toolkit with built-in serialization, pagination, permissions, and browsable API out of the box.

**Normalized schema over flat JSON.** Photographers and photo size variants live in their own tables (Photographer, Photo, PhotoSource) instead of being stored as JSON blobs on a single Photo model. This gives you referential integrity, efficient querying (e.g., "all photos by this photographer"), and no data duplication. The trade-off is more joins on reads, but `select_related` and `prefetch_related` handle that cleanly.

**JWT over session auth.** For a standalone API that could serve a mobile client, SPA, or third-party integration, stateless auth makes more sense than server-side sessions. simplejwt handles token issuance and refresh without needing any session storage.

**Ownership-based permissions.** Any authenticated user can create photos. Only the owner can update or delete. This is handled through a custom `IsOwnerOrReadOnly` permission class, keeping the authorization logic clean, testable, and separate from the view logic.

**Consistent error envelope.** Every error response follows the same structure: `{ "error": { "code", "message", "status", "details" } }`. This makes client-side error handling predictable regardless of which endpoint throws. Validation errors include field-level detail, auth errors are clearly typed.

**Idempotent CSV ingestion.** The `ingest_photos` management command checks for existing `pexels_id` values before inserting, so you can safely run it multiple times without duplicating data. It wraps everything in a transaction and handles row-level errors gracefully.

**SQLite fallback for local dev.** PostgreSQL is the production choice for relational data with clear foreign key relationships, but requiring a running Postgres instance just to evaluate a take-home adds friction. The app reads `DATABASE_URL` from the environment and falls back to SQLite if it's not set.

## What I'd Add With More Time

- **Rate limiting** via DRF throttling to prevent API abuse
- **Redis caching** for popular photo listings and photographer pages
- **Docker Compose** for one-command setup with PostgreSQL
- **CI/CD pipeline** (GitHub Actions) running tests and linting on every push
- **Role-based permissions** so admins can manage all photos, not just their own
- **Background task queue** (Celery + Redis) for bulk import operations on larger datasets
- **Full-text search** with PostgreSQL trigram indexes for better alt text matching
- **Cursor-based pagination** for more efficient deep pagination on large result sets
- **API versioning** (`/api/v1/`) for backward compatibility as the API evolves
- **Image CDN integration** for serving optimized images based on client device

## Assumptions

- `photos.csv` is a one-time seed dataset, not a streaming source
- Photographers are metadata from Pexels, not user accounts in the system
- All authenticated users can upload new photos (no admin approval flow)
- Photo URLs point to the external Pexels CDN. We store URLs, not image files.
- The `avg_color` field is informational metadata, not validated as a real hex color

## Running Tests

```bash
python manage.py test photos -v2
```

~25 tests covering models, authentication, photo CRUD, photographer endpoints, filtering, and ingestion idempotency.
