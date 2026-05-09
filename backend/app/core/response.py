from fastapi.responses import JSONResponse
from datetime import datetime


class Response:
    @staticmethod
    def success(data=None, message="success", code=200):
        return JSONResponse(
            content={
                "success": True,
                "code": code,
                "message": message,
                "data": data,
                "timestamp": int(datetime.now().timestamp() * 1000),
            }
        )

    @staticmethod
    def error(message="error", code=400, data=None):
        return JSONResponse(
            content={
                "success": False,
                "code": code,
                "message": message,
                "data": data,
                "timestamp": int(datetime.now().timestamp() * 1000),
            }
        )