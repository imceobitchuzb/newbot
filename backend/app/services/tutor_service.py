"""TutorService coordinating context, conversations, security, and AI provider calls."""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.models.enums import (
    QuickPromptType,
    TutorActionType,
    TutorContextType,
    TutorMessageRole,
    TutorMode,
)
from backend.app.models.question import Question
from backend.app.models.tutor import TutorConversation, TutorMessage
from backend.app.schemas.tutor import (
    TutorConversationCreateRequest,
    TutorConversationDetailResponse,
    TutorConversationSummaryResponse,
    TutorExplainRequest,
    TutorExplainResponse,
    TutorMessageResponse,
    TutorMessageSendRequest,
)
from backend.app.services.ai import (
    AIProviderError,
    AIProviderInvalidResponseError,
    AIProviderNotConfiguredError,
    AIProviderRateLimitError,
    AIProviderResponse,
    AIProviderTimeoutError,
    get_ai_provider,
)
from backend.app.services.tutor_context_builder import TutorContextBuilder
from backend.app.services.tutor_rate_limiter import tutor_rate_limiter

logger = logging.getLogger(__name__)

QUICK_PROMPT_MAP = {
    QuickPromptType.WEAKEST_SKILL: "Explain my weakest SAT skill, where I lose points, and the best strategy to master it.",
    QuickPromptType.MISTAKE_REVIEW: "Analyze my recent mistake patterns and tell me what types of errors (concept vs calculation vs careless) I make most.",
    QuickPromptType.DIAGNOSTIC_ANALYSIS: "Review my diagnostic scores and baseline, and outline my top 3 study priorities for a 1400+.",
    QuickPromptType.DESMOS_GUIDE: "Teach me the most powerful Desmos techniques for the Digital SAT and when to prioritize them over manual algebra.",
    QuickPromptType.SAT_MATH_STRATEGY: "Give me the golden rules for pacing, avoiding College Board traps, and maximizing score on SAT Math.",
    QuickPromptType.RW_STRATEGY: "Explain key strategies for Reading & Writing: punctuation boundaries, transitions, and command of evidence.",
    QuickPromptType.STUDY_PLAN: "Generate a targeted weekly study schedule tailored to my current baseline and 1400+ target.",
}

ALLOWED_ACTION_TYPES = {
    TutorActionType.PRACTICE_SKILL.value,
    TutorActionType.REVIEW_MISTAKE.value,
    TutorActionType.OPEN_DESMOS.value,
    TutorActionType.PRACTICE_ADAPTIVE.value,
    TutorActionType.VIEW_DIAGNOSTIC.value,
}


class TutorService:
    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        user_id: UUID,
        req: TutorConversationCreateRequest,
    ) -> TutorConversation:
        """Create a new persistent conversation for the student."""
        title = req.title
        if not title:
            if req.context_type == TutorContextType.QUESTION:
                title = "Question Assistance"
            elif req.context_type == TutorContextType.MISTAKE:
                title = "Mistake Remediation"
            elif req.context_type == TutorContextType.DESMOS:
                title = "Desmos Strategy"
            elif req.context_type == TutorContextType.DIAGNOSTIC:
                title = "Diagnostic Review"
            elif req.context_type == TutorContextType.ADAPTIVE:
                title = "Adaptive Path Guidance"
            elif req.context_type == TutorContextType.SKILL:
                title = f"Skill: {req.context_id or 'Topic'}"
            else:
                title = "SAT Coaching"

        conversation = TutorConversation(
            user_id=user_id,
            title=title,
            context_type=req.context_type.value,
            context_id=req.context_id,
            subject=req.subject.value if req.subject else None,
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation

    @staticmethod
    async def list_conversations(
        db: AsyncSession,
        user_id: UUID,
    ) -> List[TutorConversationSummaryResponse]:
        """List all conversations for the user with message counts."""
        query = (
            select(TutorConversation)
            .where(TutorConversation.user_id == user_id)
            .order_by(TutorConversation.updated_at.desc())
        )
        res = await db.execute(query)
        conversations = res.scalars().all()

        results = []
        for conv in conversations:
            msg_count_res = await db.execute(
                select(func.count(TutorMessage.id)).where(TutorMessage.conversation_id == conv.id)
            )
            count = msg_count_res.scalar() or 0

            last_msg_res = await db.execute(
                select(TutorMessage.content)
                .where(TutorMessage.conversation_id == conv.id)
                .order_by(TutorMessage.created_at.desc())
                .limit(1)
            )
            last_msg = last_msg_res.scalar_one_or_none()
            preview = (last_msg[:90] + "...") if last_msg and len(last_msg) > 90 else last_msg

            results.append(
                TutorConversationSummaryResponse(
                    id=conv.id,
                    title=conv.title,
                    context_type=conv.context_type,
                    context_id=conv.context_id,
                    subject=conv.subject,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                    message_count=count,
                    last_message_preview=preview,
                )
            )
        return results

    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        user_id: UUID,
        conversation_id: UUID,
    ) -> TutorConversationDetailResponse:
        """Get conversation detail and verify user ownership."""
        query = (
            select(TutorConversation)
            .options(selectinload(TutorConversation.messages))
            .where(
                TutorConversation.id == conversation_id,
                TutorConversation.user_id == user_id,
            )
        )
        res = await db.execute(query)
        conv = res.scalar_one_or_none()
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or access denied.",
            )

        messages = [
            TutorMessageResponse(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                mode=m.mode,
                actions=m.actions,
                created_at=m.created_at,
            )
            for m in conv.messages
        ]

        return TutorConversationDetailResponse(
            id=conv.id,
            title=conv.title,
            context_type=conv.context_type,
            context_id=conv.context_id,
            subject=conv.subject,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            messages=messages,
        )

    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        user_id: UUID,
        conversation_id: UUID,
    ) -> None:
        """Delete conversation and verify user ownership."""
        res = await db.execute(
            select(TutorConversation).where(
                TutorConversation.id == conversation_id,
                TutorConversation.user_id == user_id,
            )
        )
        conv = res.scalar_one_or_none()
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or access denied.",
            )

        await db.delete(conv)
        await db.commit()

    @staticmethod
    def _sanitize_actions(raw_actions: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Validate and sanitize structured action items returned by LLM."""
        if not raw_actions or not isinstance(raw_actions, list):
            return []

        clean_actions = []
        for act in raw_actions:
            if not isinstance(act, dict):
                continue
            act_type = act.get("type", "").upper()
            if act_type not in ALLOWED_ACTION_TYPES:
                continue

            title = str(act.get("title") or act_type.replace("_", " ").title())[:100]
            target_id = str(act.get("target_id") or "")[:128] if act.get("target_id") else None
            url = str(act.get("url") or "")[:255] if act.get("url") else None

            # Generate default safe url if missing
            if not url:
                if act_type == TutorActionType.PRACTICE_SKILL.value and target_id:
                    url = f"/math?skill={target_id}"
                elif act_type == TutorActionType.REVIEW_MISTAKE.value and target_id:
                    url = f"/mistakes/{target_id}"
                elif act_type == TutorActionType.OPEN_DESMOS.value:
                    url = f"/desmos/{target_id}" if target_id else "/desmos"
                elif act_type == TutorActionType.PRACTICE_ADAPTIVE.value:
                    url = "/math/adaptive"
                elif act_type == TutorActionType.VIEW_DIAGNOSTIC.value:
                    url = "/diagnostic/result"

            clean_actions.append({
                "type": act_type,
                "title": title,
                "description": str(act.get("description") or "")[:255] if act.get("description") else None,
                "target_id": target_id,
                "url": url,
            })
        return clean_actions

    @staticmethod
    async def send_message(
        db: AsyncSession,
        user_id: UUID,
        conversation_id: UUID,
        req: TutorMessageSendRequest,
    ) -> TutorMessageResponse:
        """Process user message, execute rate limits, call AI provider, and record assistant reply."""
        # 1. Verify conversation ownership
        res = await db.execute(
            select(TutorConversation)
            .options(selectinload(TutorConversation.messages))
            .where(
                TutorConversation.id == conversation_id,
                TutorConversation.user_id == user_id,
            )
        )
        conv = res.scalar_one_or_none()
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or access denied.",
            )

        # 2. Rate limit check
        tutor_rate_limiter.check_and_record(user_id)

        # 3. Determine actual user content (including quick prompts)
        content_text = req.content
        if req.quick_prompt and req.quick_prompt in QUICK_PROMPT_MAP:
            content_text = QUICK_PROMPT_MAP[req.quick_prompt]

        if len(content_text) > settings.TUTOR_MAX_MESSAGE_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message exceeds maximum length of {settings.TUTOR_MAX_MESSAGE_LENGTH} characters.",
            )

        # 4. Fetch context and build prompt
        user_summary = await TutorContextBuilder.get_user_summary_context(db, user_id)
        context_data: Dict[str, Any] = {}

        try:
            ctx_type = TutorContextType(conv.context_type)
        except Exception:
            ctx_type = TutorContextType.GENERAL

        if ctx_type == TutorContextType.QUESTION and conv.context_id:
            try:
                qid = UUID(conv.context_id)
                context_data = await TutorContextBuilder.build_question_context(db, qid, req.mode)
            except Exception as e:
                logger.warning(f"Failed to build question context: {e}")

        elif ctx_type == TutorContextType.MISTAKE and conv.context_id:
            try:
                mid = UUID(conv.context_id)
                context_data = await TutorContextBuilder.build_mistake_context(db, mid, user_id)
            except Exception as e:
                logger.warning(f"Failed to build mistake context: {e}")

        elif ctx_type == TutorContextType.DIAGNOSTIC:
            context_data = await TutorContextBuilder.build_diagnostic_context(db, user_id)

        elif ctx_type == TutorContextType.DESMOS and conv.context_id:
            context_data = await TutorContextBuilder.build_desmos_context(db, conv.context_id)

        system_prompt = TutorContextBuilder.build_system_prompt(
            mode=req.mode,
            context_type=ctx_type,
            context_data=context_data,
            user_summary=user_summary,
        )

        # 5. Sliding window of recent chat messages
        recent_msgs = conv.messages[-settings.TUTOR_SLIDING_WINDOW_SIZE:]
        history: List[Dict[str, str]] = []
        for m in recent_msgs:
            if m.role in (TutorMessageRole.USER.value, TutorMessageRole.ASSISTANT.value):
                history.append({
                    "role": "user" if m.role == TutorMessageRole.USER.value else "assistant",
                    "content": m.content,
                })
        history.append({"role": "user", "content": content_text})

        # 6. Call AI provider
        ai_provider = get_ai_provider()
        if not ai_provider.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Tutor is not configured.",
            )

        try:
            ai_resp = await ai_provider.generate_response(
                system_prompt=system_prompt,
                messages=history,
                mode=req.mode.value,
                user_context=user_summary,
            )
        except AIProviderNotConfiguredError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Tutor is not configured.",
            ) from exc
        except AIProviderTimeoutError as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI Tutor request timed out. Please try again.",
            ) from exc
        except AIProviderRateLimitError as exc:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI Tutor is experiencing high demand. Please try again in a few moments.",
            ) from exc
        except (AIProviderInvalidResponseError, AIProviderError) as exc:
            logger.error(f"AI Provider execution failed: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI Tutor failed to generate a valid response. Please try again.",
            ) from exc

        # 7. Record user message & assistant message in DB
        user_msg = TutorMessage(
            conversation_id=conv.id,
            role=TutorMessageRole.USER.value,
            content=content_text,
            mode=req.mode.value,
        )
        db.add(user_msg)

        clean_actions = TutorService._sanitize_actions(ai_resp.actions)
        assistant_msg = TutorMessage(
            conversation_id=conv.id,
            role=TutorMessageRole.ASSISTANT.value,
            content=ai_resp.message,
            mode=ai_resp.mode,
            model=ai_resp.model,
            token_count=ai_resp.token_count,
            actions=clean_actions,
        )
        db.add(assistant_msg)

        conv.updated_at = func.now()
        await db.commit()
        await db.refresh(assistant_msg)

        return TutorMessageResponse(
            id=assistant_msg.id,
            conversation_id=assistant_msg.conversation_id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            mode=assistant_msg.mode,
            actions=assistant_msg.actions,
            created_at=assistant_msg.created_at,
        )

    @staticmethod
    async def explain_one_shot(
        db: AsyncSession,
        user_id: UUID,
        req: TutorExplainRequest,
    ) -> TutorExplainResponse:
        """One-shot explain/hint endpoint for question or mistake without creating conversation."""
        tutor_rate_limiter.check_and_record(user_id)

        user_summary = await TutorContextBuilder.get_user_summary_context(db, user_id)
        context_data: Dict[str, Any] = {}
        ctx_type = TutorContextType.GENERAL

        if req.question_id:
            ctx_type = TutorContextType.QUESTION
            context_data = await TutorContextBuilder.build_question_context(db, req.question_id, req.mode)
        elif req.mistake_id:
            ctx_type = TutorContextType.MISTAKE
            context_data = await TutorContextBuilder.build_mistake_context(db, req.mistake_id, user_id)

        system_prompt = TutorContextBuilder.build_system_prompt(
            mode=req.mode,
            context_type=ctx_type,
            context_data=context_data,
            user_summary=user_summary,
        )

        user_prompt = req.prompt or (
            "Provide a step-by-step hint for this question."
            if req.mode == TutorMode.HINT
            else "Explain the complete solution and key concepts."
        )

        ai_provider = get_ai_provider()
        if not ai_provider.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Tutor is not configured.",
            )

        try:
            ai_resp = await ai_provider.generate_response(
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                mode=req.mode.value,
                user_context=user_summary,
            )
        except AIProviderNotConfiguredError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Tutor is not configured.",
            ) from exc
        except AIProviderTimeoutError as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI Tutor request timed out.",
            ) from exc
        except (AIProviderRateLimitError, AIProviderError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI service error: {exc}",
            ) from exc

        clean_actions = TutorService._sanitize_actions(ai_resp.actions)
        return TutorExplainResponse(
            message=ai_resp.message,
            mode=ai_resp.mode,
            actions=clean_actions,
            suggested_skill=ai_resp.suggested_skill,
            suggested_technique=ai_resp.suggested_technique,
        )
