from fastapi import APIRouter
from app.api.v1.downloads import router as downloads_router
from app.api.v1.config import router as config_router
from app.api.v1.categories import router as categories_router


# 创建主API路由
api_router = APIRouter()

# 包含各功能模块的路由
api_router.include_router(downloads_router, prefix="/downloads")
api_router.include_router(config_router, prefix="/config")
api_router.include_router(categories_router, prefix="/categories")
