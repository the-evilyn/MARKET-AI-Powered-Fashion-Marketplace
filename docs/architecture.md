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

## 3. AI-Readiness Strategy

The foundation is purposefully designed for seamless extension into AI capabilities:
1. **Vector Embeddings**: PostgreSQL is initialized with `pgvector`, providing native vector indexes (HNSW / IVFFlat) for similarity search and visual fashion recommendations.
2. **Media Pipelines**: MinIO provides an S3-compatible asset store to handle fashion garment photography, segmentation masks, user reference photos, and generative try-on assets.
3. **Async Performance**: Asynchronous Python (FastAPI + asyncpg) handles long-polling or webhook notifications from asynchronous AI inference workers cleanly.
