import logging
import uvicorn
from app import create_app

logger = logging.getLogger(__name__)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.api.auth import router as auth_router, get_current_user
from fastapi import Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState
from app.websocket_manager import websocket_manager
from jose import JWTError

app = create_app()

@app.websocket(settings.websocket_path)
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    try:
        await websocket_manager.connect(websocket, token)
        try:
            while True:
                data = await websocket.receive_text()
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket_manager.broadcast({"message": data})
        except WebSocketDisconnect as e:
            logger.info(f"WebSocket disconnected: {e.reason}")
    except WebSocketDisconnect as e:
        logger.warning(f"WebSocket connection failed: {e.reason}")
    except Exception as e:
        logger.error(f"Unexpected WebSocket error: {e}")
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


# 初始化数据库引擎
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Register routers
app.include_router(auth_router, prefix="/auth")

# Enable CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# Example of protecting an endpoint
@app.get("/protected")
async def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello, {current_user}"}

# 示例：创建数据库表
# from app.models import Base
# Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    # 启动服务
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.websocket_port,
        reload=True,
        log_level="info"
    )
