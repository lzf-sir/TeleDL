from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List, Optional
from pathlib import Path


class Settings(BaseSettings):
    """应用配置管理类"""
    # 项目基本信息
    project_name: str = "远程下载服务"
    api_prefix: str = "/api/v1"
    cors_origins: List[AnyHttpUrl] = ["http://localhost:8080"]
    
    # WebSocket配置
    websocket_port: int = 8848
    websocket_path: str = "/ws"
    websocket_reconnect_interval: int = 5  # 重连间隔(秒)
    websocket_max_connections: int = 100  # 最大连接数
    websocket_timeout: int = 60  # 超时时间(秒)

    # 路径配置
    base_dir: Path = Path(__file__).parent.parent.parent
    data_dir: Path = base_dir / "data"
    log_dir: Path = base_dir / "logs"

    # 数据库配置
    database_url: str = "sqlite:///data/db.sqlite3"
    
    # 下载配置
    download_dir: Path = base_dir / "downloads"
    max_concurrent_downloads: int = 5
    chunk_size: int = 1048576  # 1MB
    resume_support: bool = True
    retry_attempts: int = 5
    retry_delay: int = 60
    timeout: int = 60
    category_subdirs: bool = True
    file_recognition_method: str = "extension"
    bt_listen_port: int = 6881
    bt_max_connections: int = 100
    bt_max_uploads: int = 10
    bt_download_rate_limit: int = 0  # 0表示无限制
    bt_upload_rate_limit: int = 0  # 0表示无限制
    bt_seed_time: int = 3600  # 1小时
    bt_use_dht: bool = True
    bt_use_pex: bool = True
    bt_use_lsd: bool = True
    state_save_interval: int = 300  # 5分钟
    save_history: bool = True
    history_max_count: int = 100

    class Config:
        case_sensitive = False
        env_file = ".env"
        extra = "ignore"  # 忽略未定义的配置项


# 创建单例配置对象
settings = Settings()

# 自动创建必要目录
for dir_path in [
    settings.data_dir,
    settings.log_dir,
    settings.download_dir
]:
    dir_path.mkdir(parents=True, exist_ok=True)
