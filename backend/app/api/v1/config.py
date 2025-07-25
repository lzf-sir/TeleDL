from fastapi import APIRouter, HTTPException, status, Depends
from app.utils.response import success_response, error_response
from typing import Dict, Any

from app.core.download_config_manager import DownloadConfigManager
from app.schemas.config import ConfigUpdate, ConfigResponse

def get_download_config_manager():
    return DownloadConfigManager()

router = APIRouter(tags=["config"])


DEFAULT_CONFIG = {
    "download_dir": "/downloads",
    "max_concurrent_downloads": 5,
    "retry_attempts": 3,
    "timeout": 60,
    "bt_listen_port": 6881,
    "bt_max_connections": 100,
    "bt_download_rate_limit": 0,
    "bt_upload_rate_limit": 0
}

@router.get("", response_model=ConfigResponse, summary="获取当前配置")
async def get_config(
    config_manager: DownloadConfigManager = Depends(get_download_config_manager)
):
    """获取应用当前配置信息"""
    from app.core.config import settings
    download_config = config_manager.get_config()
    config = {
        "project_name": settings.project_name,
        "api_prefix": settings.api_prefix,
        "cors_origins": [str(url) for url in settings.cors_origins],
        "download_dir": str(settings.download_dir),
        "max_concurrent_downloads": settings.max_concurrent_downloads,
        "chunk_size": settings.chunk_size,
        "resume_support": settings.resume_support,
        "retry_attempts": settings.retry_attempts,
        "retry_delay": settings.retry_delay,
        "timeout": settings.timeout,
        "category_subdirs": download_config.category_subdirs if hasattr(download_config, 'category_subdirs') else True,
        "file_recognition_method": download_config.file_recognition_method if hasattr(download_config, 'file_recognition_method') else "extension",
        "bt_max_connections": settings.bt_max_connections,
        "bt_max_uploads": settings.bt_max_uploads,
        "bt_download_rate_limit": settings.bt_download_rate_limit,
        "bt_upload_rate_limit": settings.bt_upload_rate_limit,
        "bt_listen_port": settings.bt_listen_port,
        "bt_seed_time": settings.bt_seed_time,
        "bt_use_dht": settings.bt_use_dht,
        "bt_use_pex": settings.bt_use_pex,
        "bt_use_lsd": settings.bt_use_lsd,
        "state_save_interval": settings.state_save_interval,
        "save_history": download_config.save_history if hasattr(download_config, 'save_history') else True,
        "history_max_count": download_config.history_max_count if hasattr(download_config, 'history_max_count') else 100
    }
    
    # 如果配置为空，则返回默认配置
    if not any(config.values()):
        return success_response(DEFAULT_CONFIG)
        
    return success_response(config)


@router.put("", response_model=ConfigResponse, summary="更新配置")
async def update_config(
    new_config: ConfigUpdate,
    config_manager: DownloadConfigManager = Depends(get_download_config_manager)
):
    """更新应用配置"""
    try:
        update_data = new_config.dict(exclude_unset=True)
        
        # 如果传入空配置，则使用默认配置
        if not update_data:
            update_data = DEFAULT_CONFIG
            
        config_manager.update_config(update_data)
        
        # 返回更新后的配置
        return await get_config(config_manager)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=error_response(f"更新配置失败: {str(e)}", 400)
        )
