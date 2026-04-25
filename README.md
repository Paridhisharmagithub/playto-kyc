# Playto KYC Pipeline Challenge

Working KYC onboarding pipeline with:
- Django + DRF backend (`/api/v1/*`)
- React + Tailwind frontend
- Token auth with `merchant` and `reviewer` roles
- Centralized state machine enforcement
- File upload validation (PDF/JPG/PNG, max 5 MB)
- Reviewer queue + SLA risk flag + 7-day approval metrics

## Quick Start

## 1) Backend setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Backend runs at `http://127.0.0.1:8000`.

## 2) Frontend setup

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend runs at `http://127.0.0.1:5173`.

If your browser opens `http://localhost:5173`, CORS is already configured for both
`localhost` and `127.0.0.1`.

## Seeded Test Users

- Reviewer: `reviewer1` / `password123`
- Merchant (draft): `merchant_draft` / `password123`
- Merchant (under_review): `merchant_review` / `password123`

## API Overview

All endpoints are under `/api/v1/`.

- `POST /api/v1/auth/signup/`
- `POST /api/v1/auth/login/`
- `GET/PATCH /api/v1/merchant/submission/`
- `POST /api/v1/merchant/submission/submit/`
- `GET /api/v1/reviewer/queue/`
- `GET /api/v1/reviewer/metrics/`
- `GET /api/v1/reviewer/submissions/<id>/`
- `POST /api/v1/reviewer/submissions/<id>/action/`

## Test

```bash
python manage.py test
```

Includes an API-level test that verifies an illegal state transition returns 400.
