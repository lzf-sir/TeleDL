from fastapi import APIRouter, HTTPException, Path, Query, Depends, WebSocket, Security, status
from sqlalchemy.orm import Session
from app.utils.response import success_response, error_response
from app.api.auth import get_current_user
from app.db.session import get_db
from typing import List, Dict, Any, Optional
from app.core.download_manager import (
    create_download_task,
    get_download_tasks,
    get_download_task,
    get_task_files,
    resume_download,
    cancel_download,
    pause_download
)
from app.schemas.download import DownloadRequest, DownloadTaskDetail, DownloadStatus, DownloadType, DownloadTaskListResponse
from app.schemas.file import FileListResponse
from app.websocket_manager import websocket_manager

router = APIRouter(tags=["downloads"])

# 暂停下载任务
@router.post("/{task_id}/pause", response_model=Dict[str, str], summary="暂停下载任务")
async def pause_download_task(
    task_id: str = Path(..., description="下载任务ID"),
    current_user: str = Security(get_current_user),
    db: Session = Depends(get_db)
):
    """暂停下载任务"""
    result = await pause_download(task_id, db)
    if "error" in result:
        raise HTTPException(
            status_code=400,
            detail=error_response(result["error"], 400)
        )
    return success_response(result)


@router.post("", response_model=Dict[str, str], summary="创建下载任务")
async def create_download(request: DownloadRequest):
    """
    创建新的HTTP下载任务
    
    - 可指定优先级、HTTP引用页、用户代理等
    """
    task_id = await create_download_task(
        url=request.url,
        download_type=request.download_type or DownloadType.HTTP,
        filename=request.filename,
        priority=request.priority,
        referer=request.referer,
        user_agent=request.user_agent,
        start_from=request.start_from,
        category=request.category,
        selected_files=None
    )
    return {"task_id": task_id}


@router.get("", response_model=DownloadTaskListResponse, summary="获取下载任务列表")
async def list_downloads(
    status: Optional[DownloadStatus] = Query(None, description="按状态筛选"),
    download_type: Optional[DownloadType] = Query(None, description="按下载类型筛选"),
    current_user: str = Security(get_current_user)
):
    """获取下载任务列表，支持按状态和类型筛选"""
    response = await get_download_tasks(
        status=status,
        download_type=download_type
    )
    # Return the response directly without success_response wrapper
    # since DownloadTaskListResponse already includes success/error handling
    return response


@router.get("/{task_id}", response_model=DownloadTaskDetail, summary="获取下载任务详情")
async def get_download_detail(
    task_id: str = Path(..., description="下载任务ID"),
    current_user: str = Security(get_current_user)
):
    """
    获取单个下载任务的详细信息
    
    包含：
    - 基本信息（进度、速度、状态等）
    - 格式化的大小、速度和时间信息
    """
    response = await get_download_task(task_id)
    if not response:
        raise HTTPException(
            status_code=404,
            detail=error_response("任务不存在", 404)
        )
    # Return the response directly without success_response wrapper
    # since DownloadTaskDetail already includes success/error handling
    return response


@router.get("/{task_id}/files", response_model=FileListResponse, summary="获取任务文件列表")
async def get_download_files(
    task_id: str = Path(..., description="下载任务ID"),
    current_user: str = Security(get_current_user)
):
    """
    获取下载任务的文件信息
    
    - 返回单个文件信息
    - 包含文件大小和路径
    """
    files = await get_task_files(task_id)
    if files is None:
        raise HTTPException(
            status_code=404,
            detail=error_response("任务不存在", 404)
        )
    return success_response(files)


@router.post("/{task_id}/resume", response_model=Dict[str, str], summary="恢复下载任务")
async def resume_download_task(
    task_id: str = Path(..., description="下载任务ID"),
    current_user: str = Security(get_current_user)
):
    """恢复已暂停或失败的下载任务"""
    success = await resume_download(task_id)
    if success:
        return success_response({
            "message": "下载任务已恢复",
            "task_id": task_id
        })
    raise HTTPException(
        status_code=400,
        detail=error_response("无法恢复任务，可能任务不存在或状态不允许", 400)
    )


@router.delete("/{task_id}", response_model=Dict[str, str], summary="取消/删除下载任务")
async def cancel_download_task(
    task_id: str = Path(..., description="下载任务ID"),
    current_user: str = Security(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取消下载任务或删除已完成任务的文件
    
    - 等待中的任务：从队列中移除
    - 下载中的任务：停止下载并清理临时文件
    - 已完成的任务：删除文件（保留历史记录）
    """
    result = await cancel_download(task_id, db)
    if "error" in result:
        raise HTTPException(
            status_code=404,
            detail=error_response(result["error"], 404)
        )
    return success_response(result)


# WebSocket端点已移至main.py统一处理
