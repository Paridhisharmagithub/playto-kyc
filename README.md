# Playto KYC Pipeline 🚀

A production-style KYC (Know Your Customer) onboarding system where merchants submit verification details and reviewers process them through a controlled workflow.

Built for the **Playto Founding Engineering Intern Challenge**.

---

## 🌐 Live Demo
👉 https://playto-kyc-ruby.vercel.app

---

## 🧠 Overview

This project simulates a real-world KYC pipeline with:

- Multi-step merchant onboarding  
- Secure document upload with strict validation  
- Reviewer queue with controlled actions  
- Centralized state machine for workflow enforcement  
- SLA tracking and operational metrics  
- Role-based authentication (Merchant vs Reviewer)  

The focus is on **correctness, backend design, and production-like behavior**, not UI complexity.

---

## 🏗️ Tech Stack

| Layer       | Technology                         |
|------------|----------------------------------|
| Backend     | Django + Django REST Framework   |
| Frontend    | React (Vite) + Tailwind CSS      |
| Database    | PostgreSQL (production) / SQLite |
| Auth        | Token-based (DRF TokenAuth)      |
| Deployment  | Vercel (frontend) + Render (backend) |
| Container   | Docker + Docker Compose          |

---

## 🔄 KYC Workflow

### States

```
draft → submitted → under_review → (approved | rejected | more_info_requested)
more_info_requested → submitted
```

### 🔒 Rules

- Merchants can edit only in `draft` or `more_info_requested`  
- Submission must be complete before moving to `submitted`  
- Reviewers control all post-submission transitions  
- Invalid transitions return HTTP 400  

---

## 👤 Merchant Flow

- Create/update KYC submission (draft)  
- Upload required documents:
  - PAN  
  - Aadhaar  
  - Bank Statement  
- Save progress anytime  
- Submit only when all required fields are complete  

---

## 🧑‍💼 Reviewer Flow

- View queue (oldest first)  
- Inspect full submission  
- Perform actions:
  - Start review  
  - Approve  
  - Reject (requires reason)  
  - Request more info (requires reason)  

---

## 📂 File Upload Validation

Strict backend validation:

- Allowed types: **PDF, JPG, PNG**  
- Max size: **5 MB**  

Checks include:

- File extension  
- Content type  
- Magic bytes (file signature)  

Invalid uploads → HTTP 400  

---

## ⏱️ SLA Tracking

- Submissions in queue for more than **24 hours** are flagged as `at_risk`  
- Computed dynamically (not stored in DB)  

---

## 📊 Reviewer Metrics

Available via API:

- Total queue size  
- Average wait time  
- Approval rate (last 7 days)  

---

## 🔐 Authentication & Authorization

- Token-based authentication (DRF)  

### Roles

- `merchant`  
- `reviewer`  

### Security Guarantees

- Merchants can access **only their submissions**  
- Reviewers can access **all submissions**  
- No unauthorized access allowed  

---

## 🔗 API Endpoints

All endpoints under `/api/v1/`

### Auth

```
POST /auth/signup/
POST /auth/login/
```

### Merchant

```
GET /merchant/submission/
PATCH /merchant/submission/
POST /merchant/submission/submit/
POST /merchant/submission/documents/
```

### Reviewer

```
GET /reviewer/queue/
GET /reviewer/metrics/
GET /reviewer/submissions/<id>/
POST /reviewer/submissions/<id>/action/
```

---

## 🐳 Run with Docker (Recommended)

### Prerequisites

- Docker Desktop installed  

### Run

```bash
docker compose up --build
```

### Access

```
http://localhost:8000
```

---

## ⚙️ Manual Setup (Without Docker)

### Backend

```bash
cd backend

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

### Frontend

```bash
cd frontend

npm install
npm run dev
```

Frontend runs at:

```
http://127.0.0.1:5173
```

---

## 👥 Test Credentials

| Role              | Username          | Password     |
|------------------|------------------|-------------|
| Reviewer         | reviewer1         | password123 |
| Merchant (draft) | merchant_draft    | password123 |
| Merchant (review)| merchant_review   | password123 |

---

## 🧪 Testing

```bash
python manage.py test
```

Includes:

- API validation tests  
- State transition checks  

---

## 🚢 Deployment

- Frontend → Vercel  
- Backend → Render  

### Production Notes

- Set `DEBUG = False`  
- Use PostgreSQL  
- Configure media storage (S3 or cloud storage)  

---

## 🧠 Design Philosophy

- Centralized business logic using a state machine  
- Backend as the single source of truth  
- Strong validation and error handling  
- Clean, maintainable, production-style code  
