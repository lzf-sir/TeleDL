from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.events import startup_event, shutdown_event
from app.api.api import api_router


def create_app() -> FastAPI:
    """创建并配置FastAPI应用实例"""
    app = FastAPI(
        title=settings.project_name,
        description="远程下载服务（支持HTTP/BT/种子，断点续传）",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(api_router, prefix=settings.api_prefix)



    # 推荐方式：用 on_event 装饰器注册事件，保证 await
    @app.on_event("startup")
    async def _startup():
        await startup_event(app)

    @app.on_event("shutdown")
    async def _shutdown():
        await shutdown_event(app)

    return app
