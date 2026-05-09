import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from contextlib import asynccontextmanager
from app.core.config import settings
from app.database.connection import init_db
from app.utils.cache import init_redis, close_redis
from app.utils.rate_limiter import init_rate_limiter
from app.api.auth import router as auth_router
from app.api.persona import router as persona_router
from app.api.comment import router as comment_router
from app.api.style import router as style_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_redis()
    await init_rate_limiter()
    yield
    await close_redis()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(persona_router)
app.include_router(comment_router)
app.include_router(style_router)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "code": 500,
            "message": "系统繁忙，请稍后重试",
            "data": None,
            "timestamp": int(__import__('datetime').datetime.now().timestamp() * 1000)
        },
    )


@app.get("/")
async def root():
    return {"message": "Reddit Comment Assistant API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/style-test")
async def style_test():
    html_path = os.path.join(os.path.dirname(__file__), "..", "..", "launcher-page", "style-test.html")
    with open(html_path, "r") as f:
        return HTMLResponse(content=f.read())