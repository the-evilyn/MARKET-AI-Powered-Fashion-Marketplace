# Architecture & Engineering Standards

## 1. Modular Monolith Principles

To achieve fast iteration velocity without premature microservices complexity, the AI Fashion Marketplace adheres to a strict modular-monolith pattern:

### Module Isolation
* Every domain feature (e.g. `auth`, `products`, `orders`) lives in its own self-contained directory under `backend/app/modules/<module_name>/`.
* A module encapsulates its own:
  * `routes.py`: API endpoints for the module
  * `schemas.py`: Pydantic request and response models
  * `models.py`: SQLAlchemy database models
  * `services.py`: Domain business logic and orchestrations
  * `dependencies.py`: Module-specific route dependencies
* Cross-module communication occurs strictly via public module service interfaces or in-process domain events, never through private internals.

### Shared Core (`backend/app/core/`)
Cross-cutting infrastructure concerns reside in `app/core/`:
* `config.py`: Environment configuration and validation
* `database.py`: Async SQLAlchemy session lifecycle
* `redis.py`: Redis client connection pooling
* `storage.py`: MinIO/S3 object storage client
* Future cross-cutting utilities (security, logging, rate limiting)

---

## 2. AI-Readiness Strategy

The foundation is purposefully designed for seamless extension into AI capabilities:
1. **Vector Embeddings**: PostgreSQL is initialized with `pgvector`, providing native vector indexes (HNSW / IVFFlat) for similarity search and visual fashion recommendations.
2. **Media Pipelines**: MinIO provides an S3-compatible asset store to handle fashion garment photography, segmentation masks, user reference photos, and generative try-on assets.
3. **Async Performance**: Asynchronous Python (FastAPI + asyncpg) handles long-polling or webhook notifications from asynchronous AI inference workers cleanly.
