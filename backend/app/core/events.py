import logging
import asyncio
from fastapi import FastAPI
from app.core.download_manager import init_download_manager, cleanup_resources
from app.utils.logger import setup_logger

# 初始化日志
logger = setup_logger(__name__)


async def startup_event(app: FastAPI):
    """应用启动时执行的事件"""
    logger.info("应用启动中...")
    
    # 初始化下载管理器
    await init_download_manager()
    # 用当前事件循环启动下载队列处理器，避免loop冲突
    import asyncio
    from app.core.download_manager import process_download_queue
    loop = asyncio.get_running_loop()
    loop.create_task(process_download_queue())
    
    logger.info("应用启动完成")


async def shutdown_event(app: FastAPI):
    """应用关闭时执行的事件"""
    logger.info("应用关闭中...")
    
    # 清理资源
    await cleanup_resources()
    
    logger.info("应用已关闭")
