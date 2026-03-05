import json
from typing import AsyncIterator

from app.base import (
    EventType,
    IsCodeCheckError,
    LocalContext,
    LoopAction,
    PromptRequest,
    SSEPayload,
)
from app.check_code import check_gen_code
from app.logger import logger


async def check_code_step(
    prompt: str, context: LocalContext
) -> AsyncIterator[SSEPayload]:
    logger.debug("[check_gen_code] Call check_gen_code()")

    async for line in check_gen_code(
        request=PromptRequest(prompt=prompt),
        context=context,
    ):
        try:
            data = json.loads(line)
            yield SSEPayload(
                event=EventType(data["event"]),
                payload=data.get("payload", {}),
            )
        except Exception as e:
            logger.error(f"[check_gen_code] Invalid JSON: {e}")

    if context.is_code_check_error == IsCodeCheckError.ESLINT_ERROR:
        context.loop_action = LoopAction.CONTINUE
    else:
        context.loop_action = LoopAction.BREAK
