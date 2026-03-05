import json
from typing import AsyncIterator

from agents.exceptions import AgentsException, ModelBehaviorError

from app.base import (
    EventType,
    LocalContext,
    LoopAction,
    PromptRequest,
    SSEPayload,
    SystemError,
)
from app.create_code import gen_code
from app.logger import logger


async def gen_code_step(
    final_prompt: str,
    context: LocalContext,
) -> AsyncIterator[SSEPayload]:
    try:
        logger.debug("gen_code_step called")
        async for line in gen_code(
            request=PromptRequest(prompt=final_prompt),
            context=context,
        ):
            try:
                data = json.loads(line)
                yield SSEPayload(
                    event=EventType(data["event"]),
                    payload=data.get("payload", {}),
                )
                context.loop_action = LoopAction.NORMAL
            except Exception as e:
                logger.error(f"[gen_code] Invalid JSON: {e}")

    except ModelBehaviorError as e:
        logger.warning(f"[gen_code] ModelBehaviorError: {e}")
        yield SSEPayload(
            event=EventType.SYSTEM_ERROR,
            payload=SystemError(
                error="ModelBehaviorError",
                detail=str(e),
            ).model_dump(),
        )
        context.loop_action = LoopAction.CONTINUE

    except AgentsException as e:
        logger.error(f"[gen_code] AgentsException: {e}")
        yield SSEPayload(
            event=EventType.SYSTEM_ERROR,
            payload=SystemError(
                error="AgentsException",
                detail=str(e),
            ).model_dump(),
        )
        context.loop_action = LoopAction.BREAK
