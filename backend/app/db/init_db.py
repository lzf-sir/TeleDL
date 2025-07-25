from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models import *  # 确保所有模型都被注册
from app.core.config import settings

def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)
    
    # 初始化动态配置示例
    db = SessionLocal()
    try:
        # 这里只添加真正需要动态修改的配置
        if not db.query(Config).filter(Config.key == "ui_theme").first():
            db.add(Config(
                key="ui_theme",
                value="dark",
                description="界面主题"
            ))
            db.commit()
    finally:
        db.close()
