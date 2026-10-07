from fastapi import APIRouter, Depends
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.user import UserResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get authenticated student profile and learning state",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the currently authenticated user's profile, including learning goals and diagnostic status.
    Requires Bearer authorization.
    """
    return UserResponse.model_validate(current_user)
