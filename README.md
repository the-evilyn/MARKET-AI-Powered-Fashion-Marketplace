# AI Fashion Marketplace

An AI-driven fashion marketplace platform engineered with a clean modular-monolith architecture.

---

## Current Status: Phase 1 — Authentication & Identity

> [!IMPORTANT]
> **Phase 1 Scope**: Implements a production-quality identity and authentication foundation for the multi-vendor marketplace.
> Roles supported: `CUSTOMER`, `SELLER`, and `ADMIN`.
> Marketplace business features (Catalog, Cart, Orders, Payments, Reviews, AI recommendation engines) remain strictly deferred to subsequent phases.

---

## Architecture Overview

The system follows a **clean modular-monolith** pattern designed to scale without early microservices overhead while remaining ready for future AI capabilities:

```
AI Fashion Marketplace
├── backend/                  # FastAPI Application (Modular Monolith)
│   ├── app/
│   │   ├── api/v1/           # API version 1 routing (health, auth, users)
│   │   ├── core/             # Cross-cutting infrastructure (config, DB, Redis, storage, security)
│   │   └── modules/          # Isolated domain modules
│   │       ├── health/       # Health and readiness diagnostics
│   │       ├── auth/         # Authentication endpoints, schemas, dependencies
│   │       └── users/        # User entity, schemas, service layer, enums
│   ├── alembic/              # Database schema migrations
│   │   └── versions/         # 0001_create_users_table.py
│   ├── tests/                # Automated pytest suite (health, config, auth, roles)
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
* **Backend**: FastAPI + Python 3.12/3.14 (async SQLAlchemy 2, asyncpg, pydantic v2, PyJWT, Argon2id)
* **Database**: PostgreSQL 16 with `pgvector` extension for vector embeddings
* **Cache**: Redis 7 Alpine
* **Storage**: MinIO S3-compatible Object Storage (architecture-ready for fashion imagery & AI assets)
* **Orchestration**: Docker Compose

---

## Authentication & Identity (Phase 1)

### User Model Specification

| Field | Type | Attributes | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, default `uuid4` | Unique account identifier |
| `email` | `VARCHAR(255)` | Unique, Indexed, Not Null | Normalized lowercase email |
| `password_hash` | `VARCHAR(255)` | Not Null | Salted Argon2id hash |
| `first_name` | `VARCHAR(100)` | Not Null | Given name |
| `last_name` | `VARCHAR(100)` | Not Null | Family name |
| `role` | `VARCHAR(32)` | Indexed, Not Null | `CUSTOMER`, `SELLER`, `ADMIN` |
| `is_active` | `BOOLEAN` | Default `true`, Not Null | Account active status |
| `is_verified` | `BOOLEAN` | Default `false`, Not Null | Email verification status |
| `created_at` | `TIMESTAMPTZ` | Default `now()`, Not Null | Account creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | Default `now()`, Not Null | Last update timestamp |
| `last_login_at` | `TIMESTAMPTZ` | Nullable | Last successful login |

### Security Measures

* **Password Hashing**: OWASP-recommended Argon2id (`time_cost=2`, `memory_cost=64MB`, `parallelism=1`). Plaintext passwords are never stored.
* **Token Security**: Cryptographically signed HMAC-SHA256 JWT access tokens with configurable expiration (`JWT_ACCESS_EXPIRE_MINUTES`). Secrets are strictly loaded from environment variables.
* **Safe Error Handling**: Authentication endpoints return unified, non-enumerating credentials errors (`"Invalid email or password"`) preventing account existence disclosure.
* **Role-Based Access Control**: Reusable dependencies (`get_current_active_user`, `require_roles`) enforce role permissions at the route level.

### API Endpoints

| Method | Path | Auth Required | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/auth/register` | No | Self-register as `CUSTOMER` or `SELLER` |
| `POST` | `/api/v1/auth/login` | No | Authenticate with email/password; returns JWT |
| `POST` | `/api/v1/auth/logout` | Bearer Token | Invalidate current session |
| `GET` | `/api/v1/users/me` | Bearer Token | Get profile of authenticated user |
| `GET` | `/api/v1/health` | No | Service health check |
| `GET` | `/api/v1/health/ready` | No | Backing dependencies readiness probe |
| `GET` | `/api/v1/health/live` | No | Container liveness probe |

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

To start the stack (PostgreSQL, Redis, MinIO, Backend, and Frontend):

```bash
docker compose up --build -d
```

### Accessing Services

| Service | URL | Notes |
| :--- | :--- | :--- |
| **Frontend** | [http://localhost:3001](http://localhost:3001) | Dashboard & live diagnostics |
| **Backend API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive Swagger UI |
| **Backend Health** | [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) | Service health check |
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

3. Run database migrations:
   ```bash
   cd backend
   alembic upgrade head
   ```

4. Run the development server:
   ```bash
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

Tests cover 23 test cases:
* Password hashing behavior (Argon2id uniqueness, salting, verification)
* JWT creation, claims encoding, expiration, and tampering validation
* Successful user registration (`CUSTOMER` and `SELLER`)
* Duplicate email prevention and format validation
* Public self-registration privilege escalation prevention (disallowing `ADMIN` self-registration)
* Successful authentication and token issuance
* Invalid password & non-existent user safe error responses
* Inactive account lockout handling
* Authenticated and unauthenticated `/api/v1/users/me`
* Role-based authorization (`require_roles`)
* Health, readiness, and liveness endpoints

### Database Migration Validation

Generate and verify Alembic SQL DDL offline:

```bash
cd backend
alembic upgrade head --sql
```

### Frontend Build Validation

Verify TypeScript types, linting, and production compilation:

```bash
cd frontend
npm run build
```

---

## Phase Roadmap

* [x] **Phase 0: Infrastructure & Core Foundation**
* [x] **Phase 1: Authentication & Identity** (User model, JWT, Argon2id, roles: CUSTOMER/SELLER/ADMIN)
* [ ] **Phase 2: Product Catalog & Media Management** (PostgreSQL + MinIO storage)
* [ ] **Phase 3: Search & Discovery** (Meilisearch + pgvector embeddings)
* [ ] **Phase 4: Cart, Checkout & Orders**
* [ ] **Phase 5: AI Recommendations & Virtual Try-On Integration**
