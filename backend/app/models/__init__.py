# 确保所有模型被正确导入和注册
from .config import Config, DownloadConfig
from .download import DownloadTask

__all__ = ['Config', 'DownloadConfig', 'DownloadTask']
