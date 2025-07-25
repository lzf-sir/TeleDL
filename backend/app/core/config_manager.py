from typing import Any, Dict
from sqlalchemy.orm import Session
from app.models.config import Config
from app.db.session import SessionLocal
from app.core.config import settings
from fastapi import Depends
from app.db.session import get_db

class ConfigManager:
    """动态配置管理器，只管理需要运行时修改的配置"""
    
    def __init__(self, db: Session):
        self.db = db
        self._config_cache = {}
        self._load_configs()

    def _load_configs(self):
        """从数据库加载动态配置"""
        self._config_cache = {
            config.key: config.value 
            for config in self.db.query(Config).all()
            if not hasattr(settings, config.key)  # 跳过已在settings定义的配置
        }

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，优先返回settings中的静态配置"""
        if hasattr(settings, key):
            return getattr(settings, key)
        return self._config_cache.get(key, default)

    def set(self, key: str, value: Any, description: str = None):
        """设置动态配置值"""
        if hasattr(settings, key):
            raise ValueError(f"Cannot override static setting: {key}")
            
        config = self.db.query(Config).filter(Config.key == key).first()
        if config:
            config.value = value
            if description:
                config.description = description
        else:
            config = Config(
                key=key,
                value=value,
                description=description
            )
            self.db.add(config)
        self.db.commit()
        self._config_cache[key] = value

    def get_dynamic_configs(self) -> Dict[str, Any]:
        """获取所有动态配置(不包括settings中的配置)"""
        return self._config_cache.copy()

def get_config_manager(db: Session = Depends(get_db)):
    """依赖注入获取配置管理器"""
    return ConfigManager(db)
