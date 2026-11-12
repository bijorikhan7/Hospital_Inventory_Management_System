# Office IT Asset Management System

Production-oriented system for tracking office IT equipment: unique asset codes, QR labels, assignments, warranty, issues, repairs, replacements, and an immutable audit history.

## 1. Overview

The application helps Admin, IT Staff, and Employees manage laptops, monitors, printers, network gear, and other IT assets through a Django REST API and a React admin UI.

## 2. Architecture

```
React (Vite + TypeScript + Tailwind)
        │  JWT Bearer token
        ▼
Django + Django REST Framework
        │
        ▼
PostgreSQL
```

Backend apps:

| App | Responsibility |
| --- | --- |
| `accounts` | Users, roles, employees, JWT login |
| `assets` | Categories, vendors, assets, purchases, warranties, assignments, replacements, history, QR |
| `maintenance` | Issues and repairs |
| `reports` | Dashboard statistics |

Business rules live in backend services (`assets/services.py`, `assets/lifecycle.py`, `maintenance/services.py`). The UI only shows permitted actions; the API still enforces permissions.

## 3. Requirements

- Python 3.12+
- Node.js 20+
- PostgreSQL 14+ (required for production and recommended for development)
- pip / venv
- npm

## 4. Backend setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` with a strong `SECRET_KEY` and your PostgreSQL credentials.

## 5. PostgreSQL setup

Create a database (example using `psql`):

```sql
CREATE DATABASE it_inventory;
CREATE USER it_inventory WITH PASSWORD 'choose-a-strong-password';
GRANT ALL PRIVILEGES ON DATABASE it_inventory TO it_inventory;
```

Set in `backend/.env`:

```
DATABASE_ENGINE=postgresql
POSTGRES_DB=it_inventory
POSTGRES_USER=it_inventory
POSTGRES_PASSWORD=choose-a-strong-password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

Local automated tests can use SQLite **only** as a fallback:

```powershell
$env:DATABASE_ENGINE="sqlite"
python manage.py test
```

Do not use SQLite in production.

## 6. Frontend setup

```powershell
cd frontend
copy .env.example .env
npm install
```

`VITE_API_BASE_URL` must point at the API, e.g. `http://127.0.0.1:8000/api`.

## 7. Environment variables

Backend (`backend/.env.example`):

- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- `DATABASE_ENGINE` (`postgresql` or `sqlite` for local tests)
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- `CORS_ALLOWED_ORIGINS`
- `FRONTEND_URL` (used in QR payloads; no secrets inside QR codes)

Frontend:

- `VITE_API_BASE_URL`

Never commit real secrets. `.env` is gitignored.

## 8. Migrations

```powershell
cd backend
.\.venv\Scripts\activate
python manage.py makemigrations
python manage.py migrate
```

## 9. Seed command (development only)

```powershell
python manage.py seed_dev
```

Development logins (not for production):

| Username | Password | Role |
| --- | --- | --- |
| `admin` | `Admin@12345` | ADMIN |
| `itstaff` | `Staff@12345` | IT_STAFF |
| `employee` | `Employee@12345` | EMPLOYEE |

## 10. Run commands

Terminal 1:

```powershell
cd backend
.\.venv\Scripts\activate
python manage.py runserver
```

Terminal 2:

```powershell
cd frontend
npm run dev
```

Open `http://localhost:5173`. Django admin is at `http://127.0.0.1:8000/admin/`.

## 11. Test commands

```powershell
cd backend
.\.venv\Scripts\activate
python manage.py test
```

```powershell
cd frontend
npm test
```

## 12. API overview

JWT login:

`POST /api/auth/login/` `{ "username", "password" }`

Use `Authorization: Bearer <access>`.

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/auth/me/` | Current user |
| GET/POST | `/api/auth/users/` | Admin |
| GET/POST | `/api/auth/employees/` | Employees |
| GET/POST | `/api/assets/` | List/create (paginated, search, filters) |
| GET | `/api/assets/{id}/` | Detail |
| POST | `/api/assets/{id}/assign/` | `{ employee_id, remarks }` |
| POST | `/api/assets/{id}/return/` | `{ remarks }` |
| POST | `/api/assets/{id}/transfer/` | `{ employee_id, remarks }` |
| POST | `/api/assets/{id}/status/` | Controlled status change |
| GET | `/api/assets/{id}/history/` | Audit log |
| GET | `/api/assets/{id}/warranty/` | Warranties |
| GET | `/api/assets/{id}/qr/` | PNG |
| GET | `/api/assets/by-code/{code}/` | QR lookup |
| GET/POST | `/api/categories/` `/api/vendors/` `/api/purchases/` `/api/warranties/` |
| GET/POST | `/api/issues/` `/api/repairs/` `/api/replacements/` `/api/history/` |
| GET | `/api/dashboard/` | Live statistics |

Error shape:

```json
{ "success": false, "message": "This asset is already assigned to another employee." }
```

## 13. User roles

- **ADMIN** — full access including users, purchases, vendors, dispose/replace.
- **IT_STAFF** — operational access: assets, assign/return/transfer, issues, repairs, QR, history. Cannot manage users or unrestricted admin data.
- **EMPLOYEE** — own profile, assigned assets, QR lookup, report problems. Cannot change purchase price, warranty, or assignment history.

Permissions are enforced in the API, not only in the UI.

## 14. Asset lifecycle

Purchase → **AVAILABLE** → **ASSIGNED** → return → **AVAILABLE**

Damaged: **ASSIGNED** → issue → **UNDER_REPAIR** → repaired → **ASSIGNED** (or **AVAILABLE**)

Failed repair: **UNDER_REPAIR** → **DAMAGED** → **REPLACED** → **DISPOSED**

Lost: **ASSIGNED** → **LOST** → **DISPOSED**

Invalid transitions are rejected. Assign/return/transfer/replace run in database transactions. History is append-only.

Asset codes are unique (`IT-LAP-0001` style). Inactive employees cannot receive assets. Disposed, lost, and replaced assets cannot be assigned. Only one active assignment per asset.

Warranty status is calculated from dates: **ACTIVE**, **EXPIRING_SOON** (≤ 30 days), **EXPIRED**.

## 15. QR workflow

Each asset QR encodes a non-sensitive URL such as `http://localhost:5173/assets/IT-LAP-0001`.

1. Print labels from **QR Print**.
2. Scan with **QR Scanner** (camera) or type the asset code if the camera is unavailable.
3. The asset page is mobile-friendly. Employees can report a problem; IT/Admin see assign, return, transfer, repair, and history.

## 16. Production considerations

- Set `DEBUG=False`, a unique `SECRET_KEY`, tight `ALLOWED_HOSTS`, and HTTPS.
- Use PostgreSQL with backups and least-privilege DB users.
- Serve the API behind a reverse proxy; collect static files (`python manage.py collectstatic`).
- Store uploads (`MEDIA_ROOT`) outside the repo with access controls.
- Rotate JWT lifetimes to match your security policy.
- Do not run `seed_dev` in production.
- Keep CORS limited to the real frontend origin.
- Apply OS and Python package updates regularly.

## Implementation notes

Phases 1–10 are implemented in this repository: project bootstrap, JWT roles, asset CRUD, lifecycle, warranty/purchase, issues/repairs, replacement, QR, dashboard, tests, and documentation.
