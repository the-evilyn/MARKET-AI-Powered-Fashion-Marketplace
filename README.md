# AI Fashion Marketplace

An AI-driven fashion marketplace platform engineered with a clean modular-monolith architecture.

---

## Current Status: Phase 2 — Product Catalog & Media Foundation

> [!IMPORTANT]
> **Phase 2 Scope**: Implements the multi-vendor catalog domain model, hierarchical category taxonomy, brand registry, SKU-level product variants, and object storage-compatible product media metadata.
> - **Ownership & RBAC**: Sellers can create products and manage only their own listings, variants, and media. Admins manage global brands, category trees, and platform catalog moderation. Customers and unauthenticated shoppers have read-only access to active catalog listings.
> - **Scope Boundaries**: Marketplace business features (Cart, Checkout, Orders, Payments, Reviews, Wishlist, Search Engine, Recommendations, AI features, Inventory quantities) remain strictly deferred to subsequent phases.

---

## Architecture Overview

The system follows a **clean modular-monolith** pattern designed to scale without early microservices overhead while remaining ready for future AI capabilities:

```
AI Fashion Marketplace
├── backend/                  # FastAPI Application (Modular Monolith)
│   ├── app/
│   │   ├── api/v1/           # API version 1 routing (health, auth, users, brands, categories, products)
│   │   ├── core/             # Cross-cutting infrastructure (config, DB, Redis, storage, security)
│   │   └── modules/          # Isolated domain modules
│   │       ├── health/       # Health and readiness diagnostics
│   │       ├── auth/         # Authentication endpoints, schemas, dependencies
│   │       ├── users/        # User entity, schemas, service layer, enums
│   │       └── catalog/      # Brands, Categories, Products, Variants, Media
│   │           ├── routes/   # Modular domain routes (brands, categories, products)
│   │           ├── models.py # SQLAlchemy models (Brand, Category, Product, ProductVariant, ProductMedia)
│   │           ├── schemas.py# Pydantic validation schemas
│   │           ├── service.py# Business services with seller ownership & validation
│   │           └── enums.py  # ProductStatus and MediaType
│   ├── alembic/              # Database schema migrations
│   │   └── versions/         # 0001_create_users_table.py, 0002_create_catalog_tables.py
│   ├── tests/                # Automated pytest suite (48 passing tests)
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

## Catalog Domain & Media Foundation (Phase 2)

### Domain Entities

1. **Brand**:
   - Fashion labels and designers (`id`, `name`, `slug`, `description`, `logo_url`, `is_active`, timestamps).
   - Slugs are normalized and unique. Managed by `ADMIN`.
2. **Category**:
   - Hierarchical category taxonomy supporting unlimited tree depth via self-referencing `parent_id`.
   - Prevents self-parenting and circular ancestor relationships. Slugs are normalized and unique. Managed by `ADMIN`.
3. **Product**:
   - Multi-vendor catalog listing (`id`, `seller_id`, `brand_id`, `category_id`, `name`, `slug`, `description`, `status`, `base_price`, `currency`, `is_active`, timestamps).
   - `seller_id` references `users.id` (`SELLER` role).
   - `brand_id` is optional (`nullable=True`) to support independent boutique and bespoke handmade fashion.
   - `category_id` is optional (`nullable=True`) for draft flexibility.
   - `status`: Enum (`DRAFT`, `ACTIVE`, `ARCHIVED`).
   - `base_price`: Decimal/Numeric (never float) with check constraint `base_price >= 0`.
4. **ProductVariant**:
   - Purchasable SKU-level variation combinations (e.g. Size / Color combinations).
   - `sku` is globally unique. `price` is non-negative Decimal.
   - Optional `compare_at_price` validated to ensure `compare_at_price >= price`.
   - Bound to parent product with `CASCADE` delete.
5. **ProductMedia**:
   - Media asset metadata (`IMAGE`, `VIDEO`, `LOOKBOOK`).
   - Stores S3/MinIO `object_key` or `url` without storing binary blobs in PostgreSQL.
   - Supports sequence ordering (`sort_order`) and hero indicator (`is_primary`).
   - Prepared for future AI visual search and CLIP/vector embeddings.

### Authorization & Ownership Matrix

| Resource | Public / Customer | Seller | Admin |
| :--- | :--- | :--- | :--- |
| **Brands** | Read active (`GET`) | Read active (`GET`) | Full CRUD (`POST`, `PATCH`, `DELETE`) |
| **Categories** | Read active (`GET`) | Read active (`GET`) | Full CRUD (`POST`, `PATCH`, `DELETE`) |
| **Products** | Read active (`GET`) | Create; Modify/Delete **own** listings | Full CRUD on any listing |
| **Variants** | Read (`GET`) | Create/Modify/Delete on **own** products | Full CRUD on any variant |
| **Media** | Read (`GET`) | Create/Modify/Delete on **own** products | Full CRUD on any media |

---

## API Endpoints

### Catalog Endpoints (Phase 2)

| Method | Path | Auth Required | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/brands` | No | List brands with optional active filtering |
| `GET` | `/api/v1/brands/{id}` | No | Get single brand by UUID |
| `POST` | `/api/v1/brands` | ADMIN | Create brand |
| `PATCH` | `/api/v1/brands/{id}` | ADMIN | Update brand |
| `DELETE` | `/api/v1/brands/{id}` | ADMIN | Delete brand |
| `GET` | `/api/v1/categories` | No | List categories with parent filtering |
| `GET` | `/api/v1/categories/{id}` | No | Get single category by UUID |
| `POST` | `/api/v1/categories` | ADMIN | Create root or child category |
| `PATCH` | `/api/v1/categories/{id}` | ADMIN | Update category or hierarchy |
| `DELETE` | `/api/v1/categories/{id}` | ADMIN | Delete category |
| `GET` | `/api/v1/products` | No | List products with brand/category/seller filters |
| `GET` | `/api/v1/products/{id}` | No | Get detailed product (with variants & media) |
| `POST` | `/api/v1/products` | SELLER, ADMIN | Create product listing (bound to seller) |
| `PATCH` | `/api/v1/products/{id}` | Owner SELLER, ADMIN | Update product details |
| `DELETE` | `/api/v1/products/{id}` | Owner SELLER, ADMIN | Delete product (cascades variants & media) |
| `GET` | `/api/v1/products/{id}/variants` | No | List SKU variants for a product |
| `POST` | `/api/v1/products/{id}/variants` | Owner SELLER, ADMIN | Add SKU variant to product |
| `PATCH` | `/api/v1/products/{id}/variants/{v_id}` | Owner SELLER, ADMIN | Update SKU variant |
| `DELETE` | `/api/v1/products/{id}/variants/{v_id}` | Owner SELLER, ADMIN | Delete SKU variant |
| `GET` | `/api/v1/products/{id}/media` | No | List media assets for a product |
| `POST` | `/api/v1/products/{id}/media` | Owner SELLER, ADMIN | Attach media asset metadata |
| `PATCH` | `/api/v1/products/{id}/media/{m_id}` | Owner SELLER, ADMIN | Update media metadata |
| `DELETE` | `/api/v1/products/{id}/media/{m_id}` | Owner SELLER, ADMIN | Remove media asset |

### Authentication & System Endpoints (Phase 1 & 0)

| Method | Path | Auth Required | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/auth/register` | No | Self-register as `CUSTOMER` or `SELLER` |
| `POST` | `/api/v1/auth/login` | No | Authenticate with email/password; returns JWT |
| `POST` | `/api/v1/auth/logout` | Bearer Token | Invalidate current session (stateless) |
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
