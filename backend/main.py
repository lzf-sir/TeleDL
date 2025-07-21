import uvicorn
from app import create_app

app = create_app()

if __name__ == "__main__":
    # 启动服务
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8848,
        reload=True,
        log_level="info"
    )
