# Playto KYC Pipeline Challenge

A production-style KYC onboarding system that simulates how merchants submit verification details and how reviewers process them through a controlled workflow.

---

## 🚀 Overview

This project implements a complete KYC pipeline with:

* Merchant onboarding (multi-step submission)
* Document upload with strict validation
* Reviewer queue and actions
* Centralized state machine
* SLA tracking (time-based risk flag)
* Metrics for operational visibility
* Role-based authentication (merchant vs reviewer)

The focus is on **correctness, security, and clear system design**, not UI complexity.

---

## 🏗️ System Architecture

### Backend (Django + DRF)

* REST APIs under `/api/v1/`
* Business logic centralized in services + state machine
* Token-based authentication
* SQLite (can be replaced with PostgreSQL)

### Frontend (React + Tailwind)

* Minimal UI for merchant submission and reviewer dashboard
* API-driven interaction

---

## 🔄 KYC Workflow

### States

```
draft → submitted → under_review → (approved | rejected | more_info_requested)
more_info_requested → submitted
```

### Key Rules

* Merchants can edit only in `draft` or after `more_info_requested`
* Submission must be complete before moving to `submitted`
* Reviewers control all post-submission transitions
* Illegal transitions are blocked at the API level

---

## 👤 Merchant Flow

* Create or update KYC submission (draft)
* Upload required documents:

  * PAN
  * Aadhaar
  * Bank statement
* Save progress anytime
* Submit only when all required fields are filled

---

## 🧑‍💼 Reviewer Flow

* View queue of submissions (oldest first)
* Open full submission details
* Perform actions:

  * Start review
  * Approve
  * Reject (requires reason)
  * Request more info (requires reason)

---

## 📂 File Upload Validation

Validation is enforced on the backend:

* Allowed types: `PDF`, `JPG`, `PNG`
* Maximum size: `5 MB`
* Checks include:

  * File extension
  * Content type
  * File signature (PDF header / image verification)

Invalid uploads are rejected with HTTP 400.

---

## ⏱️ SLA Tracking

* Any submission in queue for **more than 24 hours** is flagged as `at_risk`
* Computed dynamically (not stored in DB)
* Ensures real-time accuracy

---

## 📊 Reviewer Metrics

Available via `/api/v1/reviewer/metrics/`:

* Total submissions in queue
* Average time in queue
* Approval rate (last 7 days)

All metrics are computed dynamically.

---

## 🔐 Authentication & Authorization

* Token-based authentication (`DRF TokenAuth`)
* Role-based access:

  * `merchant`
  * `reviewer`

### Security Guarantees

* Merchant can only access their own submission
* Reviewer can access all submissions
* No endpoint allows arbitrary submission access by merchants

---

## 🔗 API Endpoints

All endpoints are prefixed with `/api/v1/`.

### Auth

* `POST /auth/signup/`
* `POST /auth/login/`

### Merchant

* `GET /merchant/submission/`
* `PATCH /merchant/submission/`
* `POST /merchant/submission/submit/`

### Reviewer

* `GET /reviewer/queue/`
* `GET /reviewer/metrics/`
* `GET /reviewer/submissions/<id>/`
* `POST /reviewer/submissions/<id>/action/`

---

## ⚙️ Setup Instructions

### 1. Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Backend runs at:

```
http://127.0.0.1:8000
```

---

### 2. Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend runs at:

```
http://127.0.0.1:5173
```

---

## 👥 Seeded Users

* Reviewer:

  * `reviewer1 / password123`

* Merchant (draft):

  * `merchant_draft / password123`

* Merchant (under_review):

  * `merchant_review / password123`

---

## 🧪 Testing

Run tests:

```bash
python manage.py test
```

Includes:

* API-level test verifying illegal state transition returns HTTP 400

---

## 🚢 Deployment

This project can be deployed on:

* Railway
* Render
* Fly.io

### Notes for production:

* Set `DEBUG = False`
* Configure media storage properly
* Use PostgreSQL instead of SQLite

---

## 🧠 Design Philosophy

* Centralized business logic (state machine)
* Backend as the source of truth
* Defensive validation (files, auth, transitions)
* Simple, readable, maintainable code
* Focus on correctness over complexity
