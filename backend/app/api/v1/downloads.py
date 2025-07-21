from fastapi import APIRouter, HTTPException, Path, Query, Depends, WebSocket
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
    task_id: str = Path(..., description="下载任务ID")
):
    """暂停下载任务"""
    return await pause_download(task_id)


@router.post("", response_model=Dict[str, str], summary="创建下载任务")
async def create_download(request: DownloadRequest):
    """
    创建新的下载任务
    
    - 支持HTTP、磁力链接和种子文件下载
    - 可指定优先级、HTTP引用页、用户代理等
    - 对于BT/种子下载，可指定要下载的文件索引
    """
    task_id = await create_download_task(
        url=request.url,
        download_type=request.download_type,
        filename=request.filename,
        priority=request.priority,
        referer=request.referer,
        user_agent=request.user_agent,
        start_from=request.start_from,
        category=request.category,
        selected_files=request.selected_files
    )
    return {"task_id": task_id}


@router.get("", response_model=DownloadTaskListResponse, summary="获取下载任务列表")
async def list_downloads(
    status: Optional[DownloadStatus] = Query(None, description="按状态筛选"),
    download_type: Optional[DownloadType] = Query(None, description="按下载类型筛选"),
    category: Optional[str] = Query(None, description="按文件类别筛选"),
    limit: int = Query(100, ge=1, le=1000, description="最大返回数量"),
    offset: int = Query(0, ge=0, description="分页偏移量")
):
    """获取下载任务列表，支持按状态、类型和类别筛选"""
    return await get_download_tasks(
        status=status,
        download_type=download_type,
        category=category,
        limit=limit,
        offset=offset
    )


@router.get("/{task_id}", response_model=DownloadTaskDetail, summary="获取下载任务详情")
async def get_download_detail(
    task_id: str = Path(..., description="下载任务ID")
):
    """
    获取单个下载任务的详细信息
    
    包含：
    - 基本信息（进度、速度、状态等）
    - 格式化的大小、速度和时间信息
    - BT/种子任务的文件列表
    """
    task = await get_download_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/{task_id}/files", response_model=FileListResponse, summary="获取任务文件列表")
async def get_download_files(
    task_id: str = Path(..., description="下载任务ID")
):
    """
    获取任务包含的文件列表
    
    - 对于BT/种子任务：返回所有解析出的文件信息
    - 对于HTTP任务：返回单个文件信息
    - 包含文件大小、路径和选择状态
    """
    files = await get_task_files(task_id)
    if files is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return files


@router.post("/{task_id}/resume", response_model=Dict[str, str], summary="恢复下载任务")
async def resume_download_task(
    task_id: str = Path(..., description="下载任务ID")
):
    """恢复已暂停或失败的下载任务"""
    success = await resume_download(task_id)
    if success:
        return {"message": "下载任务已恢复", "task_id": task_id}
    raise HTTPException(status_code=400, detail="无法恢复任务，可能任务不存在或状态不允许")


@router.delete("/{task_id}", response_model=Dict[str, str], summary="取消/删除下载任务")
async def cancel_download_task(
    task_id: str = Path(..., description="下载任务ID")
):
    """
    取消下载任务或删除已完成任务的文件
    
    - 等待中的任务：从队列中移除
    - 下载中的任务：停止下载并清理临时文件
    - 已完成的任务：删除文件（保留历史记录）
    """
    result = await cancel_download(task_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # 保持连接
    except Exception:
        pass
    finally:
        websocket_manager.disconnect(websocket)
