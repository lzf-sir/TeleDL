from pathlib import Path
from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.download import DownloadTask

class Config(Base):
    """系统配置表"""
    __tablename__ = "configs"

    key = Column(String(64), primary_key=True)
    value = Column(JSON, nullable=False)
    description = Column(String(255))
    is_default = Column(Boolean, default=False)

class DownloadConfig(Base):
    """下载任务特定配置表"""
    __tablename__ = "download_configs"

    id = Column(Integer, primary_key=True)
    download_dir = Column(String(512), default=str(Path(__file__).parent.parent.parent / "downloads"))
    max_concurrent_downloads = Column(Integer, default=5)
    chunk_size = Column(Integer, default=1048576)
    resume_support = Column(Boolean, default=True)
    retry_attempts = Column(Integer, default=5)
    retry_delay = Column(Integer, default=60)
    timeout = Column(Integer, default=60)
    category_subdirs = Column(Boolean, default=True)
    file_recognition_method = Column(String(50), default="extension")
    bt_listen_port = Column(Integer, default=6881)
    bt_max_connections = Column(Integer, default=100)
    bt_max_uploads = Column(Integer, default=10)
    bt_download_rate_limit = Column(Integer, default=0)
    bt_upload_rate_limit = Column(Integer, default=0)
    bt_seed_time = Column(Integer, default=3600)
    bt_use_dht = Column(Boolean, default=True)
    bt_use_pex = Column(Boolean, default=True)
    bt_use_lsd = Column(Boolean, default=True)
    state_save_interval = Column(Integer, default=300)
    save_history = Column(Boolean, default=True)
    history_max_count = Column(Integer, default=100)

    # 单向查询关联的下载任务
    tasks = relationship("DownloadTask", viewonly=True)
