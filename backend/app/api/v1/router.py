from fastapi import APIRouter
from app.modules.health.routes import router as health_router
from app.modules.auth.routes import router as auth_router
from app.modules.users.routes import router as users_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount modular monolith domain routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
