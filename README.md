# AI Fashion Marketplace

An AI-driven fashion marketplace platform engineered with a clean modular-monolith architecture.

---

## Current Status: Phase 5 — Real PayPal Sandbox Payment + Order Lifecycle + Customer Checkout UI

> [!IMPORTANT]
> **Phase 5 Scope**: Implements real PayPal Sandbox checkout integration, authoritative server-side order total calculation, atomic stock reservation/finalization/release lifecycle with row-level locks (`SELECT ... FOR UPDATE`), idempotent webhook processing, customer order history, and Next.js 14 marketplace customer checkout UI.
> - **Inventory Lifecycle Fix**: Stock is reserved on checkout (`quantity_reserved += qty`), finalized upon confirmed payment capture (`quantity_on_hand -= qty, quantity_reserved -= qty`), and safely released on cancellation/failure (`quantity_reserved -= qty`).
> - **Security**: DB order is source of truth for payment amounts. No card credentials stored. Sandbox credentials exist only in environment variables.

---

## Architecture Overview

The system follows a **clean modular-monolith** pattern designed to scale without early microservices overhead while remaining extensible for multiple payment providers (e.g. PayPal, CMI):

```
AI Fashion Marketplace
├── backend/                  # FastAPI Application (Modular Monolith)
│   ├── app/
│   │   ├── api/v1/           # API version 1 routing
│   │   ├── core/             # Cross-cutting infrastructure (config, DB, Redis, storage, security)
│   │   └── modules/          # Isolated domain modules
│   │       ├── health/       # Health and readiness diagnostics
│   │       ├── auth/         # Authentication endpoints, schemas, dependencies
│   │       ├── users/        # User entity, schemas, service layer, enums
│   │       ├── catalog/      # Brands, Categories, Products, Variants, Media
│   │       ├── inventory/    # Stock on hand, reservations, availability, row locking
│   │       ├── cart/         # Shopping cart, line items, subtotal calculation
│   │       ├── orders/       # Order snapshot preservation, checkout transaction
│   │       └── payments/     # Payment entities, PayPal client provider, webhooks, lifecycle
│   ├── alembic/              # Database schema migrations (0001 - 0006)
│   ├── tests/                # Automated pytest suite (121 passing tests)
│   └── Dockerfile            # Container definition
├── frontend/                 # Next.js App Router Application
│   ├── src/app/              # Pages: Catalog (/), Checkout (/checkout), Orders (/orders, /orders/[id])
│   ├── src/components/       # UI: Navbar with customer login and reactive cart indicator
│   ├── src/context/          # Auth & Cart Context with 1-click customer login
│   ├── src/lib/              # Typed API client and data contracts
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

### Inventory Endpoints (Phase 3)

| Method | Path | Auth Required | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/inventory/variants/{id}` | Owner SELLER, ADMIN | Get SKU inventory details (on hand, reserved, available) |
| `POST` | `/api/v1/inventory/variants/{id}` | Owner SELLER, ADMIN | Initialize inventory item for a variant |
| `PATCH` | `/api/v1/inventory/variants/{id}` | Owner SELLER, ADMIN | Update stock quantities or low stock threshold |

### Cart Endpoints (Phase 4)

| Method | Path | Auth Required | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/cart` | CUSTOMER | Get active customer cart with calculated subtotal & items |
| `POST` | `/api/v1/cart/items` | CUSTOMER | Add item or increment quantity in active cart |
| `PATCH` | `/api/v1/cart/items/{id}` | CUSTOMER | Update item quantity in active cart |
| `DELETE` | `/api/v1/cart/items/{id}` | CUSTOMER | Remove item from active cart |
| `DELETE` | `/api/v1/cart` | CUSTOMER | Clear all items from active cart |

### Checkout & Orders Endpoints (Phase 4 & 5)

| Method | Path | Auth Required | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/checkout` | CUSTOMER | Atomic checkout with row locking; reserves stock and creates order in PENDING_PAYMENT |
| `GET` | `/api/v1/orders` | CUSTOMER | List authenticated customer order history (includes payment status & provider) |
| `GET` | `/api/v1/orders/{id}` | CUSTOMER | Get customer order details with line item snapshots and payment metadata |

### Payments & Webhook Endpoints (Phase 5 — PayPal Sandbox)

| Method | Path | Auth Required | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/payments/paypal/create-order` | CUSTOMER | Create server-side PayPal order for an internal PENDING_PAYMENT order |
| `POST` | `/api/v1/payments/paypal/capture` | CUSTOMER | Capture payment server-side; finalizes inventory reservation and confirms order |
| `POST` | `/api/v1/payments/paypal/cancel` | CUSTOMER | Cancel payment; releases inventory reservation and marks order CANCELLED |
| `POST` | `/api/v1/payments/paypal/webhook` | Public / Webhook | Idempotently processes PayPal events (captures, denials, reversals) |

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

## Phase 5 Payment Architecture & Inventory Lifecycle

### Corrected Inventory Lifecycle Semantics

In Phase 5, physical stock (`quantity_on_hand`) is never prematurely removed before successful payment. Stock transitions strictly follow:

```
CHECKOUT
   │
   ▼
Reserve Stock (quantity_reserved += qty, quantity_on_hand unchanged)
Order = PENDING_PAYMENT
   │
   ├──▶ PAYPAL PAYMENT SUCCESS (Capture)
   │       │
   │       ▼
   │    Finalize Inventory (quantity_on_hand -= qty, quantity_reserved -= qty)
   │    Order = CONFIRMED
   │    Payment = COMPLETED
   │
   └──▶ PAYPAL PAYMENT FAILURE / CANCEL / REVERSAL
           │
           ▼
        Release Inventory (quantity_reserved -= qty, quantity_on_hand unchanged)
        Order = CANCELLED
        Payment = FAILED or CANCELLED
```

All mutations use PostgreSQL row-level locks (`SELECT ... FOR UPDATE`) with deterministic ordering on `variant_id` to prevent deadlocks and guarantee that two concurrent customers can never oversell available stock (`quantity_available = quantity_on_hand - quantity_reserved`).

### Price Integrity & Security
* **Authoritative Order Amount**: The backend calculates Order subtotal and total exclusively from database `ProductVariant` prices. Browser amounts are strictly ignored.
* **Price Verification on Capture**: When PayPal completes capture, the backend re-verifies that captured amount and currency equal `order.total` and `order.currency`. Any discrepancy triggers immediate rollback, order cancellation, and inventory release.
* **Credentials & Secrets**: Card credentials and CVVs are never processed or stored. PayPal client credentials exist solely in environment variables and are never committed to version control.

### PayPal Sandbox Setup & Environment Variables

Add the following to your `.env` file (copied from `.env.example`):

```bash
# Backend (Sandbox only - never commit real merchant secrets)
PAYPAL_CLIENT_ID=your_paypal_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_paypal_sandbox_client_secret
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
PAYPAL_WEBHOOK_ID=your_paypal_webhook_id_optional

# Frontend
NEXT_PUBLIC_PAYPAL_CLIENT_ID=your_paypal_sandbox_client_id
```

If PayPal credentials are not provided, the application continues to build and run cleanly, displaying a clear development notification on the checkout page.


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

Tests cover 92 automated test cases across all implemented domains:
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
* Catalog Brand, Category, Product, Variant, and Media CRUD with role restrictions
* Public catalog filtering (only active products with active variants exposed)
* Variant `compare_at_price >= price` validation and Decimal precision
* SKU-level inventory tracking (`quantity_on_hand`, `quantity_reserved`, `quantity_available`)
* Low stock threshold alerts and public variant `is_in_stock` projection
* Inventory reservation, release, and row-level locking (`SELECT ... FOR UPDATE`)
* Active customer cart isolation, item addition, quantity updates, and cart clearing
* Cart validation against inactive, draft, or archived products and insufficient stock
* Transactional checkout with row-level locks, stock deduction, and atomic rollback on contention
* Immutable order line snapshots (`product_name`, `sku`, `unit_price`, `quantity`, `line_total`)
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
* [x] **Phase 2: Product Catalog & Media Foundation** (PostgreSQL + MinIO storage)
* [x] **Phase 3: Inventory & Stock Management Foundation** (SKU inventory, availability, row-level locking)
* [x] **Phase 4: Cart & Checkout Foundation** (Cart, atomic checkout, inventory deduction, order snapshots)
* [ ] **Phase 5: Payments & Order Processing** (Stripe/Payment gateway integration, webhooks)
* [ ] **Phase 6: Search & AI Recommendations** (Meilisearch + pgvector embeddings, visual search)
