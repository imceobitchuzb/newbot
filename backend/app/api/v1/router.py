from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    adaptive,
    auth,
    desmos,
    diagnostics,
    health,
    math,
    mistakes,
    questions,
    users,
)

api_router = APIRouter()

# Register core v1 sub-routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(questions.router, prefix="/questions", tags=["Questions"])
api_router.include_router(diagnostics.router, prefix="/diagnostics", tags=["Diagnostics"])
api_router.include_router(math.router, prefix="/math", tags=["Math"])
api_router.include_router(mistakes.router, prefix="/mistakes", tags=["Mistakes"])
api_router.include_router(adaptive.router)
api_router.include_router(desmos.router)



