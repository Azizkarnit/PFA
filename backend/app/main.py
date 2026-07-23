from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1 import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

from app.core.websockets import manager

@app.on_event("startup")
async def startup_event():
    manager.start_redis_listener()

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Upload size limit middleware ───────────────────────────────────────────────
MAX_UPLOAD_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    """Reject requests whose Content-Length exceeds the configured limit."""
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_UPLOAD_BYTES:
        return JSONResponse(
            status_code=413,
            content={"detail": f"File too large. Maximum allowed size is {settings.MAX_UPLOAD_SIZE_MB} MB."},
        )
    return await call_next(request)

# ── Routes ───────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def read_root():
    return {"status": "online", "project": settings.PROJECT_NAME}


@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy"}
