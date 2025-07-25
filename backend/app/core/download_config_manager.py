from typing import Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.config import DownloadConfig

class DownloadConfigManager:
    """下载配置管理器"""
    
    def __init__(self):
        self._config = None
        self._load_config()

    def _load_config(self):
        """从数据库加载下载配置"""
        db = SessionLocal()
        try:
            self._config = db.query(DownloadConfig).first()
            if not self._config:
                self._config = self._initialize_default_config(db)
            # 确保会话保持打开状态以便后续使用
            self._db = db
        except Exception as e:
            db.close()
            raise e

    def _initialize_default_config(self, db: Session) -> DownloadConfig:
        """初始化默认下载配置"""
        default_config = DownloadConfig(
            download_dir=str(Path(__file__).parent.parent.parent / "downloads"),
            max_concurrent_downloads=5,
            chunk_size=1048576,
            resume_support=True,
            retry_attempts=5,
            retry_delay=60,
            timeout=60,
            category_subdirs=True,
            file_recognition_method="extension",
            bt_listen_port=6881,
            bt_max_connections=100,
            bt_max_uploads=10,
            bt_download_rate_limit=0,
            bt_upload_rate_limit=0,
            bt_seed_time=3600,
            bt_use_dht=True,
            bt_use_pex=True,
            bt_use_lsd=True,
            state_save_interval=300,
            save_history=True,
            history_max_count=100
        )
        db.add(default_config)
        db.commit()
        return default_config

    def get_config(self) -> DownloadConfig:
        """获取当前下载配置"""
        return self._config

    def update_config(self, update_data: Dict[str, Any]):
        """更新下载配置"""
        db = SessionLocal()
        try:
            config = db.query(DownloadConfig).first()
            if not config:
                config = self._initialize_default_config(db)
            
            for key, value in update_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            db.commit()
            self._config = config
        finally:
            db.close()
