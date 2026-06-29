from fastapi import APIRouter
from app.api.v1.auth import router

auth_router: APIRouter = router

api_router = APIRouter()
api_router.include_router(auth_router)
