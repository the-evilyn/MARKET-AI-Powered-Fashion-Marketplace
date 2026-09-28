# AI Fashion Marketplace

An AI-driven fashion marketplace platform engineered with a clean modular-monolith architecture.

---

## Current Status: Phase 0 Foundation

> [!IMPORTANT]
> **Phase 0 Scope**: This phase establishes the core foundational infrastructure, modular project structure, containerization, environment management, and diagnostics.
> Per architectural guidelines, business domain features (Authentication, Catalog, Cart, Orders, Payments, Reviews, AI recommendation engines) remain intentionally deferred to subsequent phases.

---

## Architecture Overview

The system follows a **clean modular-monolith** pattern designed to scale without early microservices overhead while remaining ready for future AI capabilities:

```
AI Fashion Marketplace
├── backend/                  # FastAPI Application (Modular Monolith)
│   ├── app/
│   │   ├── api/v1/           # API version 1 routing
│   │   ├── core/             # Cross-cutting infrastructure (config, DB, Redis, storage)
│   │   └── modules/          # Isolated domain modules
│   │       └── health/       # Health and readiness diagnostics
│   ├── alembic/              # Database schema migrations
│   ├── tests/                # Automated pytest suite
│   └── Dockerfile            # Container definition
├── frontend/                 # Next.js App Router Application
│   ├── src/app/              # Pages, layout, and Tailwind CSS UI
│   └── Dockerfile            # Production multi-stage container
├── infrastructure/           # Database scripts & object storage initialization
│   ├── docker/init-db.sql    # PostgreSQL extensions (uuid-ossp, pgvector)
│   └── minio/                # Bucket provisioning
├── docker-compose.yml        # Local infrastructure & orchestration
├── .env.example              # Environment variables template
└── README.md
```

### Technology Stack

* **Frontend**: Next.js 14 (App Router) + TypeScript + Tailwind CSS
* **Backend**: FastAPI + Python 3.12/3.14 (async SQLAlchemy 2, asyncpg, pydantic v2)
* **Database**: PostgreSQL 16 with `pgvector` extension for vector embeddings
* **Cache**: Redis 7 Alpine
* **Storage**: MinIO S3-compatible Object Storage (architecture-ready for fashion imagery & AI assets)
* **Orchestration**: Docker Compose

---

## Getting Started

### 1. Prerequisites

* [Docker](https://docs.docker.com/get-docker/) & Docker Compose
* Python 3.11+ (Python 3.12 recommended; Python 3.14 compatible)
* Node.js 20+ & npm

### 2. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Review and adjust variables in `.env` if necessary. Default values are configured for local development out of the box.

---

## Running with Docker Compose (Recommended)

To start the entire foundation stack (PostgreSQL, Redis, MinIO, Backend, and Frontend):

```bash
docker compose up --build -d
```

### Accessing Services

| Service | URL | Notes |
| :--- | :--- | :--- |
| **Frontend** | [http://localhost:3001](http://localhost:3001) | Dashboard & live diagnostics |
| **Backend API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive Swagger UI |
| **Backend Health** | [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) | Service health check |
| **Readiness Check** | [http://localhost:8000/api/v1/health/ready](http://localhost:8000/api/v1/health/ready) | PostgreSQL & Redis diagnostics |
| **Liveness Check** | [http://localhost:8000/api/v1/health/live](http://localhost:8000/api/v1/health/live) | Process liveness probe |
| **MinIO Console** | [http://localhost:9001](http://localhost:9001) | Credentials: `minioadmin` / `minioadmin` |

To stop the services:

```bash
docker compose down
```

---

## Running Locally for Development

### Backend (FastAPI)

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Run the development server:
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend (Next.js)

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Run the development server (configured on port 3001):
   ```bash
   npm run dev -- -p 3001
   ```

---

## Testing & Validation

### Backend Tests

Execute the automated test suite with pytest:

```bash
pytest -v backend
```

Tests cover:
* Configuration loading & CORS parsing
* Root service info endpoint
* Health diagnostic probe (`/api/v1/health`)
* Liveness probe (`/api/v1/health/live`)
* Readiness checks (`/api/v1/health/ready`) with healthy and degraded dependency scenarios

### Frontend Build Validation

Verify TypeScript types, linting, and production compilation:

```bash
cd frontend
npm run build
```

### Docker Compose Validation

Validate Docker Compose configuration syntax:

```bash
docker compose config
```

---

## Health Check API Specification

* `GET /api/v1/health`
  Returns service status, app name, version, and deployment environment.
* `GET /api/v1/health/ready`
  Verifies connectivity to backing infrastructure (PostgreSQL database and Redis cache). Returns `200 OK` when healthy, or `503 Service Unavailable` if backing services are unreachable.
* `GET /api/v1/health/live`
  Standard container liveness endpoint returning `{"status": "alive"}`.

---

## Phase Roadmap

* [x] **Phase 0: Infrastructure & Core Foundation** (Current)
* [ ] **Phase 1: Authentication & User Accounts** (JWT, roles: buyer/seller/admin)
* [ ] **Phase 2: Product Catalog & Media Management** (PostgreSQL + MinIO storage)
* [ ] **Phase 3: Search & Discovery** (Meilisearch + pgvector embeddings)
* [ ] **Phase 4: Cart, Checkout & Orders**
* [ ] **Phase 5: AI Recommendations & Virtual Try-On Integration**
