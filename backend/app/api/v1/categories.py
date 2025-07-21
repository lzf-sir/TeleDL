from fastapi import APIRouter
from typing import Dict

from app.core.download_manager import FILE_CATEGORIES, DEFAULT_CATEGORY

router = APIRouter(tags=["categories"])


@router.get("", response_model=Dict[str, str], summary="获取文件分类列表")
async def get_file_categories():
    """获取所有支持的文件分类及其描述"""
    result = {category: info["description"] for category, info in FILE_CATEGORIES.items()}
    result[DEFAULT_CATEGORY] = "其他文件"
    return result
