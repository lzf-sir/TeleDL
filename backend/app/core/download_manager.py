"""
下载管理器核心模块
处理所有下载任务的生命周期管理
支持HTTP/FTP等协议下载
提供任务队列、状态跟踪和通知功能
"""

import os
import uuid
import time
import json
import shutil
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import logging
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
import urllib

from app.core.config import settings
from app.core.config_manager import ConfigManager
from app.core.download_config_manager import DownloadConfigManager, DownloadConfig
from app.db.session import get_db
from app.schemas.download import (
    DownloadTask, DownloadStatus, DownloadType,
    DownloadTaskDetail, DownloadTaskListResponse
)
from app.schemas.file import FileInfo, FileListResponse
from app.utils.logger import setup_logger
from app.websocket_manager import websocket_manager

logger = setup_logger(__name__)

# 文件分类常量
FILE_CATEGORIES = {
    "video": [".mp4", ".avi", ".mkv", ".mov", ".wmv"],
    "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
    "document": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"],
    "archive": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "executable": [".exe", ".msi", ".dmg", ".pkg", ".deb"],
    "other": []
}

DEFAULT_CATEGORY = "other"

class DownloadManager:
    """单例下载管理器"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_manager()
        return cls._instance
    
    def _init_manager(self):
        """初始化管理器状态"""
        self.download_tasks: Dict[str, DownloadTask] = {}
        self.history_tasks: Dict[str, DownloadTask] = {}
        self.download_queue: Optional[asyncio.Queue] = None
        self.task_locks: Dict[str, asyncio.Lock] = {}
        self._last_notify_time: Dict[str, float] = {}  # 任务ID: 上次通知时间戳
        self._initialized = False
        self._notify_interval = 3  # 默认3秒推送间隔

# 创建单例实例
download_manager = DownloadManager()

async def init_download_manager():
    """初始化下载管理器
    1. 创建任务队列
    2. 启动后台处理任务
    """
    logger.debug(f"初始化前download_manager状态: {download_manager.__dict__}")
    
    download_manager.download_queue = asyncio.Queue()
    download_manager.download_tasks = {}
    download_manager.history_tasks = {}
    download_manager.task_locks = {}
    
    asyncio.create_task(process_download_queue())
    download_manager._initialized = True
    logger.info("下载管理器初始化完成")
    logger.debug(f"初始化后download_manager状态: {download_manager.__dict__}")

async def load_tasks_on_startup(db: Session):
    """应用启动时加载任务"""
    await _load_history(db)
    await _load_active_tasks(db)
    asyncio.create_task(_save_task_state_periodically(db))

async def create_download_task(url: str, **kwargs) -> str:
    """创建新的下载任务
    Args:
        url: 下载URL
        kwargs: 额外参数(download_type, priority等)
    Returns:
        任务ID
    """
    task_id = str(uuid.uuid4())
    # 确保download_type只传递一次
    download_type = kwargs.pop("download_type", DownloadType.HTTP)
    task = DownloadTask(
        id=task_id,
        url=url,
        download_type=download_type,
        status=DownloadStatus.QUEUED,
        **kwargs
    )
    download_manager.download_tasks[task_id] = task
    download_manager.task_locks[task_id] = asyncio.Lock()
    await download_manager.download_queue.put(task_id)
    await _notify_task_update(task_id)
    return task_id

async def get_download_tasks(
    status: Optional[DownloadStatus] = None,
    download_type: Optional[DownloadType] = None,
    limit: int = 100,
    offset: int = 0
) -> DownloadTaskListResponse:
    """获取下载任务列表"""
    tasks = list(download_manager.download_tasks.values())
    if status:
        tasks = [t for t in tasks if t.status == status]
    if download_type:
        tasks = [t for t in tasks if t.download_type == download_type]
    tasks.sort(key=lambda t: t.start_time or 0, reverse=True)
    return DownloadTaskListResponse(
        items=[DownloadTaskDetail.from_task(t) for t in tasks[offset:offset+limit]],
        total=len(tasks)
    )

async def get_download_task(task_id: str) -> DownloadTaskDetail:
    """获取单个任务详情"""
    task = download_manager.download_tasks.get(task_id) or download_manager.history_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return DownloadTaskDetail(**task.dict())

async def get_task_files(task_id: str) -> FileListResponse:
    """获取任务文件列表"""
    task = download_manager.download_tasks.get(task_id) or download_manager.history_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return FileListResponse(files=[FileInfo(
        name=Path(task.file_path).name if task.file_path else task.filename,
        path=task.file_path or "",
        size=task.total_size,
        is_dir=False
    )])

async def resume_download(task_id: str) -> Dict[str, str]:
    """恢复下载任务"""
    task = download_manager.download_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status not in [DownloadStatus.PAUSED, DownloadStatus.FAILED]:
        raise HTTPException(status_code=400, detail="任务状态不支持恢复")
    task.status = DownloadStatus.QUEUED
    await download_manager.download_queue.put(task_id)
    await _notify_task_update(task_id)
    return {
        "success": "true",
        "code": "200",
        "data": json.dumps({"message": "任务已恢复"})
    }

async def pause_download(task_id: str, db: Session = Depends(get_db)) -> Dict[str, str]:
    """暂停下载任务"""
    task = download_manager.download_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != DownloadStatus.DOWNLOADING:
        raise HTTPException(status_code=400, detail="只有正在下载的任务可以暂停")
    
    task.status = DownloadStatus.PAUSED
    await _notify_task_update(task_id)
    await _save_active_tasks(db)
    
    return {
        "success": "true",
        "code": "200",
        "data": json.dumps({"message": "任务已暂停"})
    }

async def cancel_download(task_id: str, db: Session = Depends(get_db)) -> Dict[str, str]:
    """取消下载任务"""
    task = download_manager.download_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task.status = DownloadStatus.CANCELLED
    task.end_time = datetime.now()
    
    # 清理临时文件
    temp_file = getattr(task, 'temp_file', None)
    if temp_file and os.path.exists(temp_file):
        try:
            os.remove(temp_file)
        except Exception as e:
            logger.error(f"删除临时文件失败: {str(e)}")
    
    # 移动到历史记录
    download_manager.history_tasks[task_id] = task
    download_manager.download_tasks.pop(task_id, None)
    
    await _notify_task_update(task_id)
    await _save_history(db)
    
    return {
        "success": "true",
        "code": "200",
        "data": json.dumps({"message": "任务已取消"})
    }

async def cleanup_resources(db: Session = Depends(get_db)):
    """清理资源并保存状态"""
    await _save_active_tasks(db)
    await _save_history(db)

# 私有方法
async def process_download_queue():
    """处理下载队列中的任务(公共方法)"""
    while True:
        task_id = await download_manager.download_queue.get()
        async with download_manager.task_locks[task_id]:
            await _download_file(task_id)

async def _download_file(task_id: str):
    """实际下载文件实现"""
    task = download_manager.download_tasks[task_id]
    config = DownloadConfigManager().get_config()
    
    try:
        task.status = DownloadStatus.DOWNLOADING
        task.start_time = datetime.now()
        await _notify_task_update(task_id)
        
        # 创建下载目录
        download_dir = Path(config.download_dir)
        if not download_dir.exists():
            download_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取文件名
        filename = task.filename or extract_filename_from_url(task.url)
        file_path = download_dir / filename
        
        # 断点续传支持
        temp_file = file_path.with_suffix('.part')
        downloaded_bytes = temp_file.stat().st_size if temp_file.exists() else 0
        
        # 设置HTTP头
        headers = {}
        if downloaded_bytes > 0:
            headers['Range'] = f'bytes={downloaded_bytes}-'
        
        # 下载参数
        timeout = aiohttp.ClientTimeout(total=config.timeout)
        connector = aiohttp.TCPConnector(limit=config.max_concurrent_downloads)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            async with session.get(task.url, headers=headers) as response:
                if response.status not in (200, 206):
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"下载失败: HTTP {response.status}"
                    )
                
                # 获取文件总大小
                total_size = int(response.headers.get('content-length', 0)) + downloaded_bytes
                task.total_size = total_size
                
                # 分块下载
                chunk_size = config.chunk_size
                last_update_time = time.time()
                last_downloaded_bytes = downloaded_bytes
                async with aiofiles.open(temp_file, 'ab') as f:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        await f.write(chunk)
                        downloaded_bytes += len(chunk)
                        
                        # 计算下载速度 (字节/秒)
                        now = time.time()
                        time_diff = now - last_update_time
                        if time_diff > 0.5:  # 每0.5秒更新一次速度
                            speed = (downloaded_bytes - last_downloaded_bytes) / time_diff
                            task.download_speed = int(speed)  # 使用schema中定义的download_speed字段
                            last_update_time = now
                            last_downloaded_bytes = downloaded_bytes
                        
                        task.progress = int((downloaded_bytes / total_size) * 100)
                        await _notify_task_update(task_id)
                        
                        # 检查任务是否被取消或暂停
                        if task.status != DownloadStatus.DOWNLOADING:
                            return
        
        # 下载完成，重命名临时文件
        temp_file.rename(file_path)
        task.file_path = str(file_path)
        task.status = DownloadStatus.COMPLETED
        task.end_time = datetime.now()
        
    except Exception as e:
        task.status = DownloadStatus.FAILED
        task.error = str(e)
        
        # 自动重试逻辑
        if task.retry_count < config.retry_attempts:
            task.retry_count += 1
            await asyncio.sleep(config.retry_delay)
            task.status = DownloadStatus.QUEUED
            await download_manager.download_queue.put(task_id)
        else:
            # 重试次数用完，标记为失败
            task.status = DownloadStatus.FAILED
        
    finally:
        await _notify_task_update(task_id)
        if task.status == DownloadStatus.COMPLETED:
            # 移动到历史记录
            download_manager.history_tasks[task_id] = task
            download_manager.download_tasks.pop(task_id, None)
            
            # 分类文件
            await _categorize_file(task, config)

async def _categorize_file(task: DownloadTask, config: DownloadConfig):
    """根据配置分类文件"""
    if not config.category_subdirs or not task.file_path:
        return
        
    file_path = Path(task.file_path)
    ext = file_path.suffix.lower()
    category = DEFAULT_CATEGORY
    
    for cat, exts in FILE_CATEGORIES.items():
        if ext in exts:
            category = cat
            break
            
    category_dir = file_path.parent / category
    category_dir.mkdir(exist_ok=True)
    
    new_path = category_dir / file_path.name
    shutil.move(str(file_path), str(new_path))
    task.file_path = str(new_path)

def extract_filename_from_url(url: str) -> str:
    """从URL提取文件名"""
    try:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        filename = path.split('/')[-1] if path else "unnamed"
        return filename or "unnamed"
    except:
        return "unnamed"

async def _notify_task_update(task_id: str):
    """发送WebSocket通知，限制推送频率"""
    task = download_manager.download_tasks.get(task_id) or download_manager.history_tasks.get(task_id)
    if not task:
        return
        
    current_time = time.time()
    last_notify = download_manager._last_notify_time.get(task_id, 0)
    
    # 状态变化(如完成/失败)立即通知，否则检查间隔
    status_changed = (
        task.status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED) or
        (task_id in download_manager._last_notify_time and 
         task.status != download_manager.download_tasks.get(task_id, task).status)
    )
    
    if status_changed or current_time - last_notify >= download_manager._notify_interval:
        logger.info(f"Sending WebSocket update for task {task_id}: status={task.status}, progress={task.progress}, speed={getattr(task, 'download_speed', 0)}")
        try:
            # 准备payload数据
            payload = {
                "task_id": task_id,
                "status": str(task.status),
                "progress": task.progress,
                "speed": getattr(task, 'download_speed', 0),
                "download_speed": getattr(task, 'download_speed', 0)
            }
            
            # 转换datetime字段
            if task.start_time:
                payload["start_time"] = task.start_time.isoformat()
            if task.end_time:
                payload["end_time"] = task.end_time.isoformat()
                
            await websocket_manager.broadcast({
                "type": "downloads",
                "payload": payload
            })
            
            # 更新最后通知时间
            download_manager._last_notify_time[task_id] = current_time
        except Exception as e:
            logger.error(f"Failed to send WebSocket update for task {task_id}: {str(e)}")

def _convert_datetime(obj):
    """递归转换datetime对象为字符串"""
    if isinstance(obj, dict):
        return {k: _convert_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_datetime(v) for v in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj

async def _save_active_tasks(db: Session):
    """保存活跃任务到数据库"""
    try:
        config_manager = ConfigManager(db)
        tasks_data = {
            k: _convert_datetime(v.dict()) 
            for k, v in download_manager.download_tasks.items()
        }
        config_manager.set("active_download_tasks", tasks_data, "当前活跃下载任务")
        logger.info(f"成功保存{len(tasks_data)}个活跃任务")
    except Exception as e:
        logger.error(f"保存活跃任务失败: {str(e)}")

async def _save_history(db: Session):
    """保存历史记录到数据库"""
    try:
        config_manager = ConfigManager(db)
        history_data = {k: v.dict() for k, v in download_manager.history_tasks.items()}
        config_manager.set("download_history", history_data, "下载历史记录")
        logger.info(f"成功保存{len(history_data)}条历史记录")
    except Exception as e:
        logger.error(f"保存历史记录失败: {str(e)}")

async def _load_active_tasks(db: Session):
    """从数据库加载活跃任务"""
    try:
        config_manager = ConfigManager(db)
        data = config_manager.get("active_download_tasks", {})
        loaded_count = 0
        # 清空现有任务避免重复
        download_manager.download_tasks.clear()
        download_manager.task_locks.clear()
        
        for task_id, task_data in data.items():
            try:
                # 确保task_data是字典且包含必要字段
                if not isinstance(task_data, dict):
                    logger.warning(f"任务{task_id}数据格式无效: {type(task_data)}")
                    continue
                    
                # 转换数据为DownloadTask
                logger.debug(f"正在加载任务{task_id}数据: {task_data}")
                logger.debug(f"DownloadTask模型字段: {DownloadTask.__fields__.keys()}")
                logger.debug(f"任务数据字段: {task_data.keys()}")
                
                # 检查缺失字段
                missing_fields = set(DownloadTask.__fields__.keys()) - set(task_data.keys())
                if missing_fields:
                    logger.warning(f"任务{task_id}缺失字段: {missing_fields}")
                    # 为缺失字段设置默认值
                    for field in missing_fields:
                        task_data[field] = None
                
                # 转换时间字段
                if 'start_time' in task_data and isinstance(task_data['start_time'], str):
                    try:
                        task_data['start_time'] = datetime.fromisoformat(task_data['start_time']).timestamp()
                    except:
                        task_data['start_time'] = None
                
                if 'end_time' in task_data and isinstance(task_data['end_time'], str):
                    try:
                        task_data['end_time'] = datetime.fromisoformat(task_data['end_time']).timestamp()
                    except:
                        task_data['end_time'] = None
                
                task = DownloadTask(**task_data)
                download_manager.download_tasks[task_id] = task
                download_manager.task_locks[task_id] = asyncio.Lock()
                loaded_count += 1
                logger.debug(f"成功加载任务{task_id}: {task}")
                logger.debug(f"当前download_tasks内容: {download_manager.download_tasks}")
            except Exception as e:
                logger.error(f"加载任务{task_id}失败: {str(e)}")
                logger.debug(f"失败的任务数据: {task_data}")
                logger.debug(f"DownloadTask模型字段: {DownloadTask.__fields__.keys()}")
                
        logger.info(f"成功加载{loaded_count}/{len(data)}个活跃任务")
        if loaded_count != len(data):
            logger.warning(f"有{len(data)-loaded_count}个任务加载失败")
    except Exception as e:
        logger.error(f"加载活跃任务失败: {str(e)}")

async def _load_history(db: Session):
    """从数据库加载历史记录"""
    try:
        config_manager = ConfigManager(db)
        data = config_manager.get("download_history", {})
        download_manager.history_tasks.update({k: DownloadTask(**v) for k, v in data.items()})
        logger.info(f"成功加载{len(data)}条历史记录")
    except Exception as e:
        logger.error(f"加载历史记录失败: {str(e)}")

async def _save_task_state_periodically(db: Session = Depends(get_db)):
    """定期保存任务状态"""
    while True:
        await asyncio.sleep(60)
        await _save_active_tasks(db)

# 导出接口
__all__ = [
    'init_download_manager',
    'cleanup_resources',
    'get_download_tasks',
    'get_download_task',
    'get_task_files',
    'resume_download',
    'pause_download',
    'cancel_download',
    'create_download_task',
    'process_download_queue',
    'FILE_CATEGORIES',
    'DEFAULT_CATEGORY'
]
