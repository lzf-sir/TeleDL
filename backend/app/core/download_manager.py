async def pause_download(task_id: str):
    """暂停下载任务（仅HTTP）"""
    task = download_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status not in [DownloadStatus.QUEUED, DownloadStatus.DOWNLOADING]:
        raise HTTPException(status_code=400, detail="任务状态不支持暂停")
    task.status = DownloadStatus.PAUSED
    await notify_task_update(task_id)
    return {"message": "任务已暂停"}
# ========== 分类常量 ==========
DEFAULT_CATEGORY = "other"
FILE_CATEGORIES = {
    "http": {"description": "普通文件（HTTP/HTTPS下载）"},
    DEFAULT_CATEGORY: {"description": "其他文件"}
}
# ========== 任务管理API接口 ==========
from fastapi import HTTPException

async def get_download_tasks(status=None, download_type=None, category=None, limit=100, offset=0):
    """获取下载任务列表，支持筛选和分页"""
    tasks = list(download_tasks.values())
    if status:
        tasks = [t for t in tasks if t.status == status]
    if download_type:
        tasks = [t for t in tasks if t.download_type == download_type]
    if category:
        tasks = [t for t in tasks if t.category == category]
    # 按创建时间降序
    tasks.sort(key=lambda t: t.start_time or 0, reverse=True)
    total = len(tasks)
    items = [DownloadTaskDetail(**t.dict()) for t in tasks[offset:offset+limit]]
    return {"items": items, "total": total}

async def get_download_task(task_id: str):
    """获取单个下载任务详情"""
    task = download_tasks.get(task_id) or history_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return DownloadTaskDetail(**task.dict())

async def get_task_files(task_id: str):
    """获取下载任务的文件列表（HTTP只返回主文件）"""
    task = download_tasks.get(task_id) or history_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    file_info = FileInfo(
        name=Path(task.file_path).name if task.file_path else task.filename,
        path=task.file_path or "",
        size=task.total_size,
        is_dir=False
    )
    return FileListResponse(files=[file_info])

async def resume_download(task_id: str):
    """恢复暂停/失败的下载任务（仅HTTP）"""
    task = download_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status not in [DownloadStatus.PAUSED, DownloadStatus.FAILED]:
        raise HTTPException(status_code=400, detail="任务状态不支持恢复")
    task.status = DownloadStatus.QUEUED
    await download_queue.put(task_id)
    await notify_task_update(task_id)
    return {"message": "任务已恢复"}

async def cancel_download(task_id: str):
    """取消下载任务（仅HTTP）"""
    task = download_tasks.get(task_id)
    if task:
        # 只要任务存在于活跃任务，直接标记为已取消并移除
        task.status = DownloadStatus.CANCELLED
        await notify_task_update(task_id)
        # 可选：移除文件、清理资源等
        del download_tasks[task_id]
        return {"message": "任务已取消"}
    # 如果不在活跃任务，尝试从历史记录中删除
    if task_id in history_tasks:
        del history_tasks[task_id]
        return {"message": "历史任务已删除"}
    raise HTTPException(status_code=404, detail="任务不存在")
async def init_download_manager():
    """初始化下载管理器，加载历史和活跃任务，启动定时保存任务状态协程。"""
    await load_history()
    await load_active_tasks()
    # 启动定时保存任务状态的后台任务
    asyncio.create_task(save_task_state_periodically())

async def cleanup_resources():
    """清理资源，保存当前任务和历史记录。"""
    await save_active_tasks()
    await save_history()
import os
import uuid
import time
import json
import shutil
import asyncio
import aiohttp
import aiofiles
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal, Tuple
import magic
import logging

from app.core.config import settings
from app.schemas.download import (
    DownloadTask, DownloadStatus, DownloadType, 
    PriorityLevel, DownloadTaskDetail
)
from app.schemas.file import FileInfo, FileListResponse
from app.utils.formatters import format_size, format_speed, format_duration
from app.utils.logger import setup_logger
from app.websocket_manager import websocket_manager

# 初始化日志
logger = setup_logger(__name__)

# 全局存储
download_tasks: Dict[str, DownloadTask] = {}
history_tasks: Dict[str, DownloadTask] = {}
download_queue = None

async def init_download_manager():
    global download_queue
    download_queue = asyncio.Queue()
task_locks: Dict[str, asyncio.Lock] = {}


async def load_history():
    global history_tasks
    """加载历史记录"""
    history_path = settings.history_file
    
    if history_path.exists():
        try:
            async with aiofiles.open(history_path, "r") as f:
                content = await f.read()
                history_data = json.loads(content)
                
                # 转换为DownloadTask对象
                history_tasks = {
                    task_id: DownloadTask(**task_data)
                    for task_id, task_data in history_data.items()
                }
                
                logger.info(f"已加载 {len(history_tasks)} 条历史记录")
        except Exception as e:
            logger.error(f"加载历史记录失败: {str(e)}")
            history_tasks = {}
    else:
        logger.info("没有找到历史记录文件，将创建新的")
        history_tasks = {}


async def save_history():
    global history_tasks
    """保存历史记录"""
    if not settings.save_history:
        return
        
    history_path = settings.history_file
    try:
        # 限制历史记录数量
        if len(history_tasks) > settings.history_max_count:
            # 按结束时间排序，保留最新的记录
            sorted_tasks = sorted(
                history_tasks.values(), 
                key=lambda x: x.end_time if x.end_time else 0, 
                reverse=True
            )
            keep_tasks = sorted_tasks[:settings.history_max_count]
            history_tasks = {task.id: task for task in keep_tasks}
        
        # 转换为字典并保存
        history_data = {
            task_id: task.dict()
            for task_id, task in history_tasks.items()
        }
        
        async with aiofiles.open(history_path, "w") as f:
            await f.write(json.dumps(history_data, indent=4))
        
        logger.debug(f"已保存 {len(history_tasks)} 条历史记录")
    except Exception as e:
        logger.error(f"保存历史记录失败: {str(e)}")


async def load_active_tasks():
    """加载活跃任务"""
    tasks_path = settings.tasks_file
    
    if tasks_path.exists():
        try:
            async with aiofiles.open(tasks_path, "r") as f:
                content = await f.read()
                tasks_data = json.loads(content)
                
                # 转换为DownloadTask对象并重置状态
                download_tasks = {}
                for task_id, task_data in tasks_data.items():
                    if task_data["status"] == DownloadStatus.DOWNLOADING:
                        task_data["status"] = DownloadStatus.QUEUED
                        task_data["retry_count"] = 0
                    
                    download_tasks[task_id] = DownloadTask(** task_data)
                    task_locks[task_id] = asyncio.Lock()
                    
                    # 添加到队列
                    if task_data["status"] == DownloadStatus.QUEUED:
                        await download_queue.put(task_id)
                
                logger.info(f"已加载 {len(download_tasks)} 个活跃任务")
        except Exception as e:
            logger.error(f"加载活跃任务失败: {str(e)}")
            download_tasks = {}
            task_locks = {}
    else:
        logger.info("没有找到活跃任务文件，将创建新的")
        download_tasks = {}
        task_locks = {}


async def save_active_tasks():
    """保存活跃任务"""
    tasks_path = settings.tasks_file
    try:
        active_tasks = {
            task_id: task.dict()
            for task_id, task in download_tasks.items()
            if task.status in [DownloadStatus.QUEUED, DownloadStatus.DOWNLOADING]
        }
        
        async with aiofiles.open(tasks_path, "w") as f:
            await f.write(json.dumps(active_tasks, indent=4))
        
        logger.debug(f"已保存 {len(active_tasks)} 个活跃任务")
    except Exception as e:
        logger.error(f"保存活跃任务失败: {str(e)}")


async def save_task_state_periodically():
    """定期保存任务状态"""
    while True:
        await save_active_tasks()
        await asyncio.sleep(settings.state_save_interval)


async def process_download_queue():
    """处理下载队列（异步）"""
    logger.info("下载队列处理器已启动")
    
    # 创建信号量控制并发下载数
    semaphore = asyncio.Semaphore(settings.max_concurrent_downloads)
    
    while True:
        # 获取任务ID
        task_id = await download_queue.get()
        task = download_tasks.get(task_id)
        
        if not task or task.status != DownloadStatus.QUEUED:
            download_queue.task_done()
            continue
        
        logger.info(f"开始处理任务: {task_id} ({task.url})")
        
        # 使用信号量控制并发
        async with semaphore:
            try:
                await download_file(task_id)
            except Exception as e:
                logger.error(f"处理任务 {task_id} 时出错: {str(e)}")
                if task_id in download_tasks:
                    download_tasks[task_id].status = DownloadStatus.FAILED
                    download_tasks[task_id].error = str(e)
        
        download_queue.task_done()
        logger.info(f"任务处理完成: {task_id}")


async def create_download_task(url: str, **kwargs) -> str:
    """创建下载任务"""
    task_id = str(uuid.uuid4())
    
    # 检测下载类型（如果未指定）
    download_type = kwargs.get("download_type") or DownloadType.HTTP
    
    # 创建任务数据
    task_data = {
        "id": task_id,
        "url": url,
        "download_type": download_type,
        "filename": kwargs.get("filename"),
        "priority": kwargs.get("priority", PriorityLevel.NORMAL),
        "referer": kwargs.get("referer"),
        "user_agent": kwargs.get("user_agent"),
        "status": DownloadStatus.QUEUED,
        "progress": 0.0,
        "total_size": 0,
        "downloaded_size": kwargs.get("start_from", 0),
        "start_from": kwargs.get("start_from", 0),
        "start_time": None,
        "start_time_str": None,
        "end_time": None,
        "end_time_str": None,
        "error": None,
        "file_path": None,
        "category": kwargs.get("category"),
        "category_dir": None,
        "category_description": None,
        "retry_count": 0,
        "download_speed": 0.0,
        "upload_speed": 0.0,
        "peers": 0,
        "seeds": 0,
        "duration": 0.0,
        "last_updated": time.time(),
        "resumed": False,
        "selected_files": kwargs.get("selected_files"),
        "files": []
    }
    
    # 创建任务对象
    task = DownloadTask(** task_data)
    download_tasks[task_id] = task
    task_locks[task_id] = asyncio.Lock()
    
    # 添加到队列
    await download_queue.put(task_id)
    
    logger.info(f"已创建新下载任务: {task_id} ({download_type.value}: {url})")
    return task_id


async def download_file(task_id: str):
    """异步HTTP下载"""
    task = download_tasks.get(task_id)
    
    if not task:
        logger.warning(f"任务 {task_id} 不存在，无法下载")
        return
    
    # 获取任务锁
    task = download_tasks.get(task_id)
    if not task:
        logger.warning(f"任务 {task_id} 不存在，无法下载")
        return
    lock = task_locks.get(task_id)
    if not lock:
        lock = asyncio.Lock()
        task_locks[task_id] = lock
    async with lock:
        try:
            # 更新任务状态为下载中
            task.status = DownloadStatus.DOWNLOADING
            if not task.start_time:
                task.start_time = time.time()
                task.start_time_str = datetime.fromtimestamp(task.start_time).strftime("%Y-%m-%d %H:%M:%S")
            task.error = None
            task.download_speed = 0.0
            task.last_updated = time.time()
            logger.info(f"开始HTTP下载: {task_id} ({task.url})")
            # 获取文件名
            if not task.filename:
                filename = task.url.split("/")[-1]
                if not filename:
                    filename = f"download_{task_id}"
                task.filename = filename
            base_dir = settings.download_dir
            if settings.category_subdirs and task.category:
                file_dir = base_dir / task.category
            else:
                file_dir = base_dir
            file_path = file_dir / task.filename
            temp_file_path = f"{file_path}.part"
            task.file_path = str(file_path)
            task.category_dir = str(file_dir)
            resume_position = 0
            if os.path.exists(temp_file_path):
                resume_position = os.path.getsize(temp_file_path)
                task.downloaded_size = resume_position
                logger.info(f"检测到临时文件，将从 {resume_position} 字节开始续传")
            if task.start_from and task.start_from > resume_position:
                resume_position = task.start_from
                task.downloaded_size = resume_position
            headers = {}
            if task.referer:
                headers["Referer"] = task.referer
            if task.user_agent:
                headers["User-Agent"] = task.user_agent
            else:
                headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            if resume_position > 0 and settings.resume_support:
                headers["Range"] = f"bytes={resume_position}-"
                task.resumed = True
            else:
                task.resumed = False
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    logger.info(f"删除旧临时文件: {temp_file_path}")
            for attempt in range(settings.retry_attempts + 1):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            task.url,
                            headers=headers,
                            timeout=settings.timeout,
                            ssl=False
                        ) as response:
                            response.raise_for_status()
                            content_length = response.headers.get('Content-Length')
                            if content_length:
                                if response.status == 206:
                                    content_range = response.headers.get('Content-Range', '')
                                    if content_range.startswith('bytes'):
                                        total_size = int(content_range.split('/')[-1])
                                else:
                                    total_size = int(content_length)
                                task.total_size = total_size
                                if total_size > 0:
                                    task.progress = round((resume_position / total_size) * 100, 2)
                            mode = 'ab' if resume_position > 0 else 'wb'
                            async with aiofiles.open(temp_file_path, mode) as f:
                                start_time = time.time()
                                chunk_count = 0
                                async for chunk in response.content.iter_chunked(settings.chunk_size):
                                    if task.status == DownloadStatus.CANCELLED:
                                        task.status = DownloadStatus.PAUSED
                                        task.end_time = time.time()
                                        task.end_time_str = datetime.fromtimestamp(task.end_time).strftime("%Y-%m-%d %H:%M:%S")
                                        logger.info(f"任务 {task_id} 已被取消")
                                        return
                                    if chunk:
                                        await f.write(chunk)
                                        chunk_size = len(chunk)
                                        task.downloaded_size += chunk_size
                                        resume_position += chunk_size
                                        chunk_count += 1
                                        if chunk_count % 5 == 0:
                                            elapsed = time.time() - start_time
                                            if elapsed > 0:
                                                task.download_speed = round((chunk_size * 5) / (1024 * elapsed), 2)
                                                start_time = time.time()
                                        if task.total_size > 0:
                                            progress = (task.downloaded_size / task.total_size) * 100
                                            task.progress = round(progress, 2)
                                        task.last_updated = time.time()
                                        # 实时保存进度
                                        await save_active_tasks()
                    if task.total_size > 0 and task.downloaded_size >= task.total_size:
                        counter = 1
                        while file_path.exists():
                            name = task.filename
                            ext = Path(name).suffix
                            name_without_ext = Path(name).stem
                            file_path = file_dir / f"{name_without_ext}_{counter}{ext}"
                            counter += 1
                        os.rename(temp_file_path, str(file_path))
                        task.file_path = str(file_path)
                        logger.info(f"HTTP下载完成: {task_id} ({task.file_path})")
                        break
                    elif task.total_size == 0:
                        if os.path.exists(temp_file_path):
                            counter = 1
                            while file_path.exists():
                                name = task.filename
                                ext = Path(name).suffix
                                name_without_ext = Path(name).stem
                                file_path = file_dir / f"{name_without_ext}_{counter}{ext}"
                                counter += 1
                            os.rename(temp_file_path, str(file_path))
                            task.file_path = str(file_path)
                        logger.info(f"HTTP下载完成（未知大小）: {task_id}")
                        break
                    else:
                        raise Exception(f"下载中断，已完成 {task.downloaded_size}/{task.total_size}")
                except Exception as e:
                    task.error = str(e)
                    task.retry_count = attempt + 1
                    logger.warning(f"下载尝试 {attempt + 1} 失败: {str(e)}")
                    if attempt == settings.retry_attempts:
                        raise e
                    await asyncio.sleep(settings.retry_delay * (attempt + 1))
            task.status = DownloadStatus.COMPLETED
            task.end_time = time.time()
            task.end_time_str = datetime.fromtimestamp(task.end_time).strftime("%Y-%m-%d %H:%M:%S")
            task.download_speed = 0.0
            task.duration = round(task.end_time - task.start_time, 2)
            history_tasks[task_id] = task.copy()
            await save_history()
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.debug(f"已删除临时文件: {temp_file_path}")
            logger.info(f"任务 {task_id} 已完成，耗时 {format_duration(task.duration)}")
        except Exception as e:
            if task_id in download_tasks:
                task.status = DownloadStatus.FAILED
                task.error = str(e)
                task.end_time = time.time()
                task.end_time_str = datetime.fromtimestamp(task.end_time).strftime("%Y-%m-%d %H:%M:%S")
                task.download_speed = 0.0
                logger.error(f"HTTP下载失败: {task_id} - {str(e)}")
                history_tasks[task_id] = task.copy()
                await save_history()
                return
            # 如果请求中指定了开始位置，使用该位置
            if task.start_from and task.start_from > resume_position:
                resume_position = task.start_from
                task.downloaded_size = resume_position
            
            # 添加Range头以支持断点续传
            headers = {}
            if task.referer:
                headers["Referer"] = task.referer
            if task.user_agent:
                headers["User-Agent"] = task.user_agent
            else:
                headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            
            if resume_position > 0 and settings.resume_support:
                headers["Range"] = f"bytes={resume_position}-"
                task.resumed = True
            else:
                task.resumed = False
                # 如果不需要续传但临时文件存在，删除它
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    logger.info(f"删除旧临时文件: {temp_file_path}")
            
            # 多次尝试下载
            for attempt in range(settings.retry_attempts + 1):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            task.url, 
                            headers=headers,
                            timeout=settings.timeout,
                            ssl=False
                        ) as response:
                            response.raise_for_status()
                            
                            # 获取文件总大小
                            content_length = response.headers.get('Content-Length')
                            if content_length:
                                # 处理Range响应的情况
                                if response.status == 206:  # 部分内容
                                    content_range = response.headers.get('Content-Range', '')
                                    if content_range.startswith('bytes'):
                                        total_size = int(content_range.split('/')[-1])
                                else:  # 200 OK
                                    total_size = int(content_length)
                                
                                # 更新任务总大小
                                task.total_size = total_size
                                
                                # 计算初始进度
                                if total_size > 0:
                                    task.progress = round((resume_position / total_size) * 100, 2)
                            
                            # 打开文件（追加模式，如果是续传）
                            mode = 'ab' if resume_position > 0 else 'wb'
                            async with aiofiles.open(temp_file_path, mode) as f:
                                start_time = time.time()
                                chunk_count = 0
                                async for chunk in response.content.iter_chunked(settings.chunk_size):
                                    # 检查任务是否已被取消
                                    if task.status == DownloadStatus.CANCELLED:
                                        task.status = DownloadStatus.PAUSED
                                        task.end_time = time.time()
                                        task.end_time_str = datetime.fromtimestamp(task.end_time).strftime("%Y-%m-%d %H:%M:%S")
                                        logger.info(f"任务 {task_id} 已被取消")
                                        return
                                    
                                    if chunk:  # 过滤掉保持连接的空块
                                        await f.write(chunk)
                                        chunk_size = len(chunk)
                                        task.downloaded_size += chunk_size
                                        resume_position += chunk_size
                                        
                                        # 计算下载速度
                                        chunk_count += 1
                                        if chunk_count % 5 == 0:  # 每5个块计算一次速度
                                            elapsed = time.time() - start_time
                                            if elapsed > 0:
                                                task.download_speed = round((chunk_size * 5) / (1024 * elapsed), 2)  # KB/s
                                                start_time = time.time()
                                        
                                        # 更新进度
                                        if task.total_size > 0:
                                            progress = (task.downloaded_size / task.total_size) * 100
                                            task.progress = round(progress, 2)
                                        
                                        task.last_updated = time.time()
                        
                    # 检查是否下载完成
                    if task.total_size > 0 and task.downloaded_size >= task.total_size:
                        # 处理文件重名
                        counter = 1
                        while file_path.exists():
                            name = task.filename
                            ext = Path(name).suffix
                            name_without_ext = Path(name).stem
                            file_path = file_dir / f"{name_without_ext}_{counter}{ext}"
                            counter += 1
                        # 仅使用扩展名识别，直接重命名
                        os.rename(temp_file_path, str(file_path))
                        task.file_path = str(file_path)
                        
                        logger.info(f"HTTP下载完成: {task_id} ({task.file_path})")
                        break
                    elif task.total_size == 0:
                        # 未知文件大小，认为下载完成
                        if os.path.exists(temp_file_path):
                            # 处理文件重名
                            counter = 1
                            while file_path.exists():
                                name = task.filename
                                ext = Path(name).suffix
                                name_without_ext = Path(name).stem
                                file_path = file_dir / f"{name_without_ext}_{counter}{ext}"
                                counter += 1
                            
                            os.rename(temp_file_path, str(file_path))
                            task.file_path = str(file_path)
                        logger.info(f"HTTP下载完成（未知大小）: {task_id}")
                        break
                    else:
                        # 未完成，可能是连接中断，准备重试
                        raise Exception(f"下载中断，已完成 {task.downloaded_size}/{task.total_size}")
                
                except Exception as e:
                    task.error = str(e)
                    task.retry_count = attempt + 1
                    logger.warning(f"下载尝试 {attempt + 1} 失败: {str(e)}")
                    
                    # 如果达到最大重试次数，标记为失败
                    if attempt == settings.retry_attempts:
                        raise e
                    
                    # 等待一段时间后重试
                    await asyncio.sleep(settings.retry_delay * (attempt + 1))  # 递增延迟
        
        except Exception as e:
            # 处理错误
            if task_id in download_tasks:
                task.status = DownloadStatus.FAILED
                task.error = str(e)
                task.end_time = time.time()
                task.end_time_str = datetime.fromtimestamp(task.end_time).strftime("%Y-%m-%d %H:%M:%S")
                task.download_speed = 0.0
                
                logger.error(f"HTTP下载失败: {task_id} - {str(e)}")
                
                # 添加到历史记录
                history_tasks[task_id] = task.copy()
                await save_history()
                return
    
    # 下载完成
    task.status = DownloadStatus.COMPLETED
    task.end_time = time.time()
    task.end_time_str = datetime.fromtimestamp(task.end_time).strftime("%Y-%m-%d %H:%M:%S")
    task.download_speed = 0.0  # 下载完成，速度归零
    task.duration = round(task.end_time - task.start_time, 2)
    
    # 添加到历史记录
    history_tasks[task_id] = task.copy()
    await save_history()
    
    # 如果存在临时文件，删除它
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
        logger.debug(f"已删除临时文件: {temp_file_path}")
    
    logger.info(f"任务 {task_id} 已完成，耗时 {format_duration(task.duration)}")


async def notify_task_update(task_id: str):
    """通知 WebSocket 客户端任务更新"""
    task = download_tasks.get(task_id) or history_tasks.get(task_id)
    if task:
        await websocket_manager.broadcast({"task_id": task_id, "status": task.status, "progress": task.progress})

