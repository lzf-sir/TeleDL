import uvicorn
from app import create_app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

app = create_app()

# 初始化数据库引擎
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 示例：创建数据库表
# from app.models import Base
# Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    # 启动服务
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8848,
        reload=True,
        log_level="info"
    )
