def format_size(size_bytes: int) -> str:
    """将字节大小转换为人性化的显示格式"""
    if size_bytes < 0:
        return "未知"
    if size_bytes == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    
    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024
        unit_index += 1
    
    return f"{size_bytes:.2f} {units[unit_index]}"


def format_speed(speed_kb: float) -> str:
    """将KB/s的速度转换为人性化的显示格式"""
    if speed_kb < 0:
        return "0 KB/s"
    
    if speed_kb < 1024:
        return f"{speed_kb:.2f} KB/s"
    else:
        return f"{speed_kb / 1024:.2f} MB/s"


def format_duration(seconds: float) -> str:
    """将秒数转换为人性化的时间格式"""
    if seconds < 0:
        return "0s"
    if seconds == 0:
        return "0s"
    
    days = int(seconds // 86400)
    seconds %= 86400
    
    hours = int(seconds // 3600)
    seconds %= 3600
    
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    
    return " ".join(parts)
