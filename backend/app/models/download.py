from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class DownloadTask(Base):
    """下载任务表"""
    __tablename__ = "download_tasks"

    id = Column(String(36), primary_key=True)
    url = Column(String(512), nullable=False)
    file_path = Column(String(512))
    filename = Column(String(255))
    size = Column(Integer, default=0)
    downloaded = Column(Integer, default=0)
    progress = Column(Float, default=0.0)
    speed = Column(Float, default=0.0)
    status = Column(String(20), default="queued")  # queued, downloading, paused, completed, failed
    type = Column(String(20), default="http")  # http, ftp, bt
    category = Column(String(50))
    priority = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    error = Column(String(512))
    config_id = Column(Integer, ForeignKey("download_configs.id"))
    
    config = relationship("DownloadConfig", back_populates="tasks")
