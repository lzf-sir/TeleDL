from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class FileInfo(BaseModel):
    """文件信息模型"""
    index: int
    name: str
    path: str
    size: int
    size_human: str
    selected: bool
    final_path: Optional[str] = None
    category: Optional[str] = None
    category_description: Optional[str] = None


class FileListResponse(BaseModel):
    """文件列表响应模型"""
    total: int
    files: List[Dict[str, Any]]
