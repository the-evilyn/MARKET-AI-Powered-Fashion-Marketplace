from fastapi import APIRouter
from app.modules.health.routes import router as health_router
from app.modules.auth.routes import router as auth_router
from app.modules.users.routes import router as users_router
from app.modules.catalog.routes.brands import router as brands_router
from app.modules.catalog.routes.categories import router as categories_router
from app.modules.catalog.routes.products import router as products_router
from app.modules.inventory.routes import router as inventory_router
from app.modules.cart.routes import router as cart_router
from app.modules.orders.routes import router as orders_router
from app.modules.payments.routes import router as payments_router
from app.modules.seller.routes import router as seller_router
from app.modules.search.routes import router as search_router
from app.modules.stores.routes import router as stores_router
from app.modules.admin.routes import router as admin_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount modular monolith domain routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(brands_router)
api_v1_router.include_router(categories_router)
api_v1_router.include_router(products_router)
api_v1_router.include_router(inventory_router)
api_v1_router.include_router(cart_router)
api_v1_router.include_router(orders_router)
api_v1_router.include_router(payments_router)
api_v1_router.include_router(seller_router)
api_v1_router.include_router(search_router)
api_v1_router.include_router(stores_router)
api_v1_router.include_router(admin_router)
