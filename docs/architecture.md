# Architecture & Engineering Standards

## 1. Modular Monolith Principles

To achieve fast iteration velocity without premature microservices complexity, the AI Fashion Marketplace adheres to a strict modular-monolith pattern:

### Module Isolation
* Every domain feature (e.g. `auth`, `users`, `products`, `orders`) lives in its own self-contained directory under `backend/app/modules/<module_name>/`.
* A module encapsulates its own:
  * `routes.py`: API endpoints for the module
  * `schemas.py`: Pydantic request and response models
  * `models.py`: SQLAlchemy database models
  * `service.py`: Domain business logic and orchestrations
  * `dependencies.py`: Module-specific route dependencies
  * `enums.py`: Domain-specific enumerations and value types
* Cross-module communication occurs strictly via public module service interfaces or in-process domain events, never through private internals.

### Shared Core (`backend/app/core/`)
Cross-cutting infrastructure concerns reside in `app/core/`:
* `config.py`: Environment configuration and validation (pydantic-settings)
* `database.py`: Async SQLAlchemy session lifecycle
* `redis.py`: Redis client connection pooling
* `storage.py`: MinIO/S3 object storage client
* `security.py`: Argon2id password hashing and cryptographic JWT token signing

---

## 2. Identity & Access Control Architecture (Phase 1)

### Role Hierarchy & Matrix
* `CUSTOMER`: Standard shopper account. Permitted to browse, purchase, review, and maintain cart/orders.
* `SELLER`: Multi-vendor store owner. Permitted to manage storefront inventory, catalog entries, and view incoming order fulfillments.
* `ADMIN`: Platform administrator with full access to moderation, user auditing, and configuration.

### Security Guarantees
* **Argon2id Hashing**: High-memory-cost key derivation (`argon2-cffi`) protects stored credentials against hardware-accelerated dictionary attacks.
* **Stateless Tokens**: RFC 7519 JSON Web Tokens (JWT) signed with HS256 and configurable expiration window (`JWT_ACCESS_EXPIRE_MINUTES`).
* **Safe Error Surfaces**: Authentication routes avoid account enumeration by returning unified HTTP 401 error messages.

---

## 3. Product Catalog & Media Foundation (Phase 2)

### Domain Conceptual Model
```
Seller (User: role=SELLER)
  └── Product (status: DRAFT | ACTIVE | ARCHIVED, base_price: Numeric)
        ├── Brand (optional foreign key)
        ├── Category (hierarchical taxonomy with parent_id)
        ├── ProductVariant (SKU-level: size, color, price, compare_at_price)
        └── ProductMedia (media_type: IMAGE | VIDEO | LOOKBOOK, object_key / url)
```

### Key Architectural Decisions

1. **Brand Modality**:
   - `brand_id` is an optional foreign key (`nullable=True`) with `ON DELETE SET NULL`. This architectural decision accommodates independent boutique creators, custom tailors, and emerging sustainable fashion lines that lack formal brand registrations.
2. **Category Hierarchy**:
   - Modeled via self-referential `parent_id` foreign key referencing `categories.id` (`ON DELETE SET NULL`).
   - Prevents self-parenting (`parent_id != id`) and circular ancestry traversals in service logic, supporting arbitrary tree depth (e.g. `Women` &rarr; `Dresses` &rarr; `Evening Dresses`).
3. **Monetary Precision**:
   - Currency amounts (`base_price`, `variant.price`, `variant.compare_at_price`) strictly utilize PostgreSQL `NUMERIC(10, 2)` and Python `Decimal`. Floating-point arithmetic is prohibited to prevent rounding inaccuracies in pricing calculations.
   - Enforced by database `CHECK` constraints (`price >= 0`) and Pydantic model validators.
4. **SKU-Level Variants**:
   - Purchasable combinations (color, size) are modeled as discrete `ProductVariant` entities with globally unique `sku` codes.
   - Variants inherit parent product lifecycle and cascade on delete.
5. **Object Storage-First Media Strategy**:
   - Binary media files are never stored in PostgreSQL.
   - Images and videos reside in S3-compatible MinIO object storage (`fashion-media` bucket). The database records metadata, CDN URLs, accessibility alt-text, sort sequence, and primary hero flags.
   - Schema is prepared for downstream AI pipelines (e.g. CLIP feature vectors, background matting, virtual try-on masks).
6. **Multi-Vendor Ownership Enforcement**:
   - `SELLER` permissions strictly enforce row-level ownership: sellers can only mutate products, variants, and media where `product.seller_id == current_user.id`.
   - `ADMIN` retains platform-wide catalog governance.
   - `CUSTOMER` and unauthenticated users are restricted to read operations on active catalog items.

---

## 4. AI-Readiness Strategy

The foundation is purposefully designed for seamless extension into AI capabilities:
1. **Vector Embeddings**: PostgreSQL is initialized with `pgvector`, providing native vector indexes (HNSW / IVFFlat) for similarity search and visual fashion recommendations.
2. **Media Pipelines**: MinIO provides an S3-compatible asset store to handle fashion garment photography, segmentation masks, user reference photos, and generative try-on assets.
3. **Async Performance**: Asynchronous Python (FastAPI + asyncpg) handles long-polling or webhook notifications from asynchronous AI inference workers cleanly.

