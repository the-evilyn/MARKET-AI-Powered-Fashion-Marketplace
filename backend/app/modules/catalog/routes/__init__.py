from app.modules.catalog.routes.brands import router as brands_router
from app.modules.catalog.routes.categories import router as categories_router
from app.modules.catalog.routes.products import router as products_router

__all__ = ["brands_router", "categories_router", "products_router"]
