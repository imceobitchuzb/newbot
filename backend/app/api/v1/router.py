from fastapi import APIRouter
from backend.app.api.v1.endpoints import auth, health, users

api_router = APIRouter()

# Register core v1 sub-routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
