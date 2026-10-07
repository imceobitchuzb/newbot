from typing import Optional
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.diagnostic import (
    CurrentDiagnosticResponse,
    DiagnosticAnswerRequest,
    DiagnosticAnswerResponse,
    DiagnosticResultResponse,
    DiagnosticSessionResponse,
)
from backend.app.api.deps import get_current_user
from backend.app.services.diagnostic_service import diagnostic_service


router = APIRouter()


@router.post(
    "",
    response_model=DiagnosticSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start or resume a diagnostic test",
    description="Initializes a new 40-question SAT Master Diagnostic session or resumes an ongoing session.",
)
async def start_or_resume_diagnostic(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DiagnosticSessionResponse:
    return await diagnostic_service.start_or_resume(db=db, user_id=current_user.id)


@router.get(
    "/current",
    response_model=Optional[CurrentDiagnosticResponse],
    summary="Get current active diagnostic session and current question",
    description="Returns the active diagnostic session state and next question to solve without leaking answers.",
)
async def get_current_diagnostic(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[CurrentDiagnosticResponse]:
    return await diagnostic_service.get_current_diagnostic(db=db, user_id=current_user.id)


@router.post(
    "/{diagnostic_id}/questions/{question_id}/answer",
    response_model=DiagnosticAnswerResponse,
    summary="Submit answer to a diagnostic question",
    description="Submits the chosen option for a diagnostic question, validating question assignment and advancing test state.",
)
async def submit_diagnostic_answer(
    diagnostic_id: uuid.UUID,
    question_id: uuid.UUID,
    request: DiagnosticAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DiagnosticAnswerResponse:
    return await diagnostic_service.submit_answer(
        db=db,
        user_id=current_user.id,
        diagnostic_id=diagnostic_id,
        question_id=question_id,
        selected_option_id=request.selected_option_id,
        time_spent_seconds=request.time_spent_seconds,
    )


@router.get(
    "/latest/result",
    response_model=DiagnosticResultResponse,
    summary="Get latest completed diagnostic result for current user",
    description="Retrieves the most recent completed diagnostic result for the authenticated user.",
)
async def get_latest_diagnostic_result(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DiagnosticResultResponse:
    return await diagnostic_service.get_latest_result(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{diagnostic_id}/result",

    response_model=DiagnosticResultResponse,
    summary="Get diagnostic test result",
    description="Retrieves estimated SAT score range, section breakdown, and weak/strong domain classification.",
)
async def get_diagnostic_result(
    diagnostic_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DiagnosticResultResponse:
    return await diagnostic_service.get_result(
        db=db,
        user_id=current_user.id,
        diagnostic_id=diagnostic_id,
    )
