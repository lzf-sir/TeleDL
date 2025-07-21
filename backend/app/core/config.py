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

    # 路径配置
    base_dir: Path = Path(__file__).parent.parent.parent
    download_dir: Path = base_dir / "downloads"
    torrent_temp_dir: Path = download_dir / ".torrents"
    data_dir: Path = base_dir / "data"
    history_file: Path = data_dir / "history.json"
    tasks_file: Path = data_dir / "active_tasks.json"
    log_dir: Path = base_dir / "logs"

    # 下载核心配置
    max_concurrent_downloads: int = 5
    chunk_size: int = 1024 * 1024  # 1MB
    resume_support: bool = True
    retry_attempts: int = 5
    retry_delay: int = 5  # 基础重试延迟（秒）
    timeout: int = 60  # 网络请求超时（秒）

    # 文件分类配置
    category_subdirs: bool = True
    file_recognition_method: str = "extension_and_content"  # 扩展+内容识别

    # BT/种子配置
    bt_max_connections: int = 100
    bt_max_uploads: int = 20
    bt_download_rate_limit: int = 0  # 0=无限制（字节/秒）
    bt_upload_rate_limit: int = 100 * 1024  # 100KB/s（字节/秒）
    bt_listen_port: int = 6881
    bt_seed_time: int = 3600  # 做种时间（秒）
    bt_use_dht: bool = True
    bt_use_pex: bool = True
    bt_use_lsd: bool = True

    # 状态存储配置
    state_save_interval: int = 30  # 任务状态保存间隔（秒）
    save_history: bool = True
    history_max_count: int = 1000

    class Config:
        case_sensitive = False
        env_file = ".env"


# 创建单例配置对象
settings = Settings()

# 自动创建必要目录
for dir_path in [
    settings.download_dir,
    settings.torrent_temp_dir,
    settings.data_dir,
    settings.log_dir
]:
    dir_path.mkdir(parents=True, exist_ok=True)
