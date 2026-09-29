from fastapi import APIRouter
from app.modules.health.routes import router as health_router
from app.modules.auth.routes import router as auth_router
from app.modules.users.routes import router as users_router
from app.modules.catalog.routes.brands import router as brands_router
from app.modules.catalog.routes.categories import router as categories_router
from app.modules.catalog.routes.products import router as products_router
from app.modules.inventory.routes import router as inventory_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount modular monolith domain routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(brands_router)
api_v1_router.include_router(categories_router)
api_v1_router.include_router(products_router)
api_v1_router.include_router(inventory_router)
