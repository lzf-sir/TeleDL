
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
from app.utils.formatters import format_size, format_speed, format_duration
class DownloadTaskDetail(BaseModel):
    """下载任务详情（包含格式化信息）"""
    id: str
    url: str
    download_type: str
    filename: Optional[str]
    priority: str
    status: str
    progress: float
    total_size: int
    total_size_human: Optional[str] = ""
    downloaded_size: int
    downloaded_size_human: Optional[str] = ""
    start_time_str: Optional[str]
    end_time_str: Optional[str]
    error: Optional[str]
    file_path: Optional[str]
    category: Optional[str]
    category_description: Optional[str]
    retry_count: int
    download_speed: float
    download_speed_human: Optional[str] = ""
    upload_speed: float
    upload_speed_human: Optional[str] = ""
    peers: int
    seeds: int
    duration: float
    duration_human: Optional[str] = ""
    files: List[Dict[str, Any]]
    downloaded_files: List[Dict[str, Any]]
    download_type_display: Optional[str] = ""
    status_display: Optional[str] = ""

    @classmethod
    def from_task(cls, task: 'DownloadTask'):
        """从DownloadTask创建详情模型"""
        # 下载类型显示名称
        type_display_map = {
            "http": "HTTP下载",
            "magnet": "磁力链接",
            "torrent": "种子文件"
        }
        # 状态显示名称
        status_display_map = {
            "queued": "等待中",
            "downloading": "下载中",
            "completed": "已完成",
            "failed": "已失败",
            "paused": "已暂停",
            "cancelled": "已取消",
            "deleted": "已删除",
            "fetching_metadata": "获取元数据中",
            "downloading_torrent": "下载种子中",
            "seeding": "做种中"
        }
        return cls(
            id=task.id,
            url=task.url,
            download_type=task.download_type,
            filename=task.filename,
            priority=task.priority,
            status=task.status,
            progress=task.progress,
            total_size=task.total_size,
            total_size_human=format_size(task.total_size),
            downloaded_size=task.downloaded_size,
            downloaded_size_human=format_size(task.downloaded_size),
            start_time_str=task.start_time_str,
            end_time_str=task.end_time_str,
            error=task.error,
            file_path=task.file_path,
            category=task.category,
            category_description=task.category_description,
            retry_count=task.retry_count,
            download_speed=task.download_speed,
            download_speed_human=format_speed(task.download_speed),
            upload_speed=task.upload_speed,
            upload_speed_human=format_speed(task.upload_speed),
            peers=task.peers,
            seeds=task.seeds,
            duration=task.duration,
            duration_human=format_duration(task.duration),
            files=task.files,
            downloaded_files=task.downloaded_files,
            download_type_display=type_display_map.get(task.download_type, task.download_type),
            status_display=status_display_map.get(task.status, task.status)
        )

# 分页响应模型，放在 DownloadTaskDetail 之后，且顶格定义
class DownloadTaskListResponse(BaseModel):
    items: List[DownloadTaskDetail]
    total: int


from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.utils.formatters import format_size, format_speed, format_duration

class DownloadType(str, Enum):
    """下载类型枚举"""
    HTTP = "http"
    MAGNET = "magnet"
    TORRENT = "torrent"

class DownloadStatus(str, Enum):
    """下载状态枚举"""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    DELETED = "deleted"
    FETCHING_METADATA = "fetching_metadata"  # BT获取元数据中
    DOWNLOADING_TORRENT = "downloading_torrent"  # 下载种子文件中
    SEEDING = "seeding"  # BT做种中

class PriorityLevel(str, Enum):
    """任务优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class DownloadTask(BaseModel):
    """下载任务数据模型"""
    id: str
    url: str
    download_type: DownloadType
    filename: Optional[str] = None
    priority: PriorityLevel = PriorityLevel.NORMAL
    referer: Optional[str] = None
    user_agent: Optional[str] = None
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: float = 0.0
    total_size: int = 0
    downloaded_size: int = 0
    start_from: int = 0
    start_time: Optional[float] = None
    start_time_str: Optional[str] = None
    end_time: Optional[float] = None
    end_time_str: Optional[str] = None
    error: Optional[str] = None
    file_path: Optional[str] = None
    category: Optional[str] = None
    category_dir: Optional[str] = None
    category_description: Optional[str] = None
    retry_count: int = 0
    download_speed: float = 0.0  # KB/s
    upload_speed: float = 0.0  # KB/s (for BT)
    peers: int = 0  # (for BT)
    seeds: int = 0  # (for BT)
    duration: float = 0.0  # 持续时间（秒）
    last_updated: float = 0.0
    resumed: bool = False
    selected_files: Optional[List[int]] = None  # 选择下载的文件索引 (for BT)
    files: List[Dict[str, Any]] = Field(default_factory=list)  # 种子中的文件列表 (for BT)
    downloaded_files: List[Dict[str, Any]] = Field(default_factory=list)  # 已下载的文件列表 (for BT)
    download_dir: Optional[str] = None  # 下载目录 (for BT)

    class Config:
        use_enum_values = True


class DownloadTaskDetail(BaseModel):
    """下载任务详情（包含格式化信息）"""
    id: str
    url: str
    download_type: str
    filename: Optional[str]
    priority: str
    status: str
    progress: float
    total_size: int
    total_size_human: Optional[str] = ""
    downloaded_size: int
    downloaded_size_human: Optional[str] = ""
    start_time_str: Optional[str]
    end_time_str: Optional[str]
    error: Optional[str]
    file_path: Optional[str]
    category: Optional[str]
    category_description: Optional[str]
    retry_count: int
    download_speed: float
    download_speed_human: Optional[str] = ""
    upload_speed: float
    upload_speed_human: Optional[str] = ""
    peers: int
    seeds: int
    duration: float
    duration_human: Optional[str] = ""
    files: List[Dict[str, Any]]
    downloaded_files: List[Dict[str, Any]]
    download_type_display: Optional[str] = ""
    status_display: Optional[str] = ""

    @classmethod
    def from_task(cls, task: DownloadTask):
        """从DownloadTask创建详情模型"""
        # 下载类型显示名称
        type_display_map = {
            "http": "HTTP下载",
            "magnet": "磁力链接",
            "torrent": "种子文件"
        }
        
        # 状态显示名称
        status_display_map = {
            "queued": "等待中",
            "downloading": "下载中",
            "completed": "已完成",
            "failed": "已失败",
            "paused": "已暂停",
            "cancelled": "已取消",
            "deleted": "已删除",
            "fetching_metadata": "获取元数据中",
            "downloading_torrent": "下载种子中",
            "seeding": "做种中"
        }

        return cls(
            id=task.id,
            url=task.url,
            download_type=task.download_type,
            filename=task.filename,
            priority=task.priority,
            status=task.status,
            progress=task.progress,
            total_size=task.total_size,
            total_size_human=format_size(task.total_size),
            downloaded_size=task.downloaded_size,
            downloaded_size_human=format_size(task.downloaded_size),
            start_time_str=task.start_time_str,
            end_time_str=task.end_time_str,
            error=task.error,
            file_path=task.file_path,
            category=task.category,
            category_description=task.category_description,
            retry_count=task.retry_count,
            download_speed=task.download_speed,
            download_speed_human=format_speed(task.download_speed),
            upload_speed=task.upload_speed,
            upload_speed_human=format_speed(task.upload_speed),
            peers=task.peers,
            seeds=task.seeds,
            duration=task.duration,
            duration_human=format_duration(task.duration),
            files=task.files,
            downloaded_files=task.downloaded_files,
            download_type_display=type_display_map.get(task.download_type, task.download_type),
            status_display=status_display_map.get(task.status, task.status)
        )


class DownloadRequest(BaseModel):
    """创建下载任务请求模型"""
    url: str
    download_type: Optional[DownloadType] = None
    filename: Optional[str] = None
    priority: PriorityLevel = PriorityLevel.NORMAL
    referer: Optional[str] = None
    user_agent: Optional[str] = None
    start_from: Optional[int] = 0
    category: Optional[str] = None
    selected_files: Optional[List[int]] = None  # 仅用于BT下载
