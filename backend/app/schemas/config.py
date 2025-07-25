from typing import Optional, List, Literal
from pydantic import BaseModel, AnyHttpUrl


class ConfigUpdate(BaseModel):
    """配置更新请求模型"""
    # 基本配置
    project_name: Optional[str] = None
    cors_origins: Optional[List[AnyHttpUrl]] = None
    
    # 下载配置
    max_concurrent_downloads: Optional[int] = None
    chunk_size: Optional[int] = None
    resume_support: Optional[bool] = None
    retry_attempts: Optional[int] = None
    retry_delay: Optional[int] = None
    timeout: Optional[int] = None
    
    # 文件分类配置
    category_subdirs: Optional[bool] = None
    file_recognition_method: Optional[Literal["extension", "content", "extension_and_content"]] = None
    
    # BT配置
    bt_max_connections: Optional[int] = None
    bt_max_uploads: Optional[int] = None
    bt_download_rate_limit: Optional[int] = None
    bt_upload_rate_limit: Optional[int] = None
    bt_listen_port: Optional[int] = None
    bt_seed_time: Optional[int] = None
    bt_use_dht: Optional[bool] = None
    bt_use_pex: Optional[bool] = None
    bt_use_lsd: Optional[bool] = None
    
    # 存储配置
    state_save_interval: Optional[int] = None
    save_history: Optional[bool] = None
    history_max_count: Optional[int] = None


class ConfigData(BaseModel):
    """配置数据模型"""
    project_name: str
    api_prefix: str
    cors_origins: List[str]
    download_dir: str
    max_concurrent_downloads: int
    chunk_size: int
    resume_support: bool
    retry_attempts: int
    retry_delay: int
    timeout: int
    category_subdirs: bool
    file_recognition_method: str
    bt_max_connections: int
    bt_max_uploads: int
    bt_download_rate_limit: int
    bt_upload_rate_limit: int
    bt_listen_port: int
    bt_seed_time: int
    bt_use_dht: bool
    bt_use_pex: bool
    bt_use_lsd: bool
    state_save_interval: int
    save_history: bool
    history_max_count: int

class ConfigResponse(BaseModel):
    """配置响应模型"""
    success: bool
    code: int
    message: str
    data: ConfigData
