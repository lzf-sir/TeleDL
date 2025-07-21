from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.core.config import settings
from app.schemas.config import ConfigUpdate, ConfigResponse

router = APIRouter(tags=["config"])


@router.get("", response_model=ConfigResponse, summary="获取当前配置")
async def get_config():
    """获取应用当前配置信息"""
    return {
        "project_name": settings.project_name,
        "api_prefix": settings.api_prefix,
        "cors_origins": [str(origin) for origin in settings.cors_origins],
        "download_dir": str(settings.download_dir),
        "max_concurrent_downloads": settings.max_concurrent_downloads,
        "chunk_size": settings.chunk_size,
        "resume_support": settings.resume_support,
        "retry_attempts": settings.retry_attempts,
        "retry_delay": settings.retry_delay,
        "timeout": settings.timeout,
        "category_subdirs": settings.category_subdirs,
        "file_recognition_method": settings.file_recognition_method,
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
        "save_history": settings.save_history,
        "history_max_count": settings.history_max_count
    }


@router.put("", response_model=ConfigResponse, summary="更新配置")
async def update_config(new_config: ConfigUpdate):
    """更新应用配置"""
    try:
        # 更新配置
        for key, value in new_config.dict(exclude_unset=True).items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        # 返回更新后的配置
        return await get_config()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新配置失败: {str(e)}")
