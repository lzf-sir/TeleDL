from fastapi import status
from typing import Any, Dict, Optional

def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK
) -> Dict[str, Any]:
    return {
        "success": True,
        "code": status_code,
        "message": message,
        "data": data
    }

def error_response(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    error_code: Optional[int] = None,
    details: Any = None
) -> Dict[str, Any]:
    return {
        "success": False,
        "code": error_code or status_code,
        "message": message,
        "details": details
    }
