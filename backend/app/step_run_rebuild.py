import json
from typing import AsyncIterator

from app.base import (
    BuildErrorAnalyzerResult,
    EventType,
    FunctionResult,
    LocalContext,
    SSEPayload,
    SystemError,
)
from app.build_error_analysis import analyze_build_error
from app.code_fixer import fix_code
from app.config import Settings
from app.logger import logger
from app.run_build_cmd import run_build


async def run_rebuild_step(
    context: LocalContext,
    settings: Settings,
    build_result: FunctionResult,
) -> AsyncIterator[SSEPayload]:
    logger.debug("run_rebuild_step called")
    rebuild_retry = settings.rebuild_retry
    logger.debug(f"rebuild_retry: {rebuild_retry}")

    last_build_result = build_result
    for i in range(rebuild_retry):
        try:
            # ------------------------------
            # SubStep-1: Analyze build error
            # ------------------------------
            logger.debug(f"SubStep-1: Analyze build error [{i}]")
            analyzer_result: BuildErrorAnalyzerResult | None = None
            async for line in analyze_build_error(
                context=context, build_result=last_build_result
            ):
                # Events: AGENT_UPDATE, ANALYZER_RESULT
                data = json.loads(line)
                payload = SSEPayload(
                    event=EventType(data["event"]),
                    payload=data.get("payload", {}),
                )
                # Send Immediately
                yield payload

                if data["event"] == EventType.ANALYZER_RESULT:
                    analyzer_result = BuildErrorAnalyzerResult(**data["payload"])

            if analyzer_result is None:
                raise ValueError("analyzer_result is None")
            logger.debug(f"analyzer_result: {analyzer_result}")

            # -------------------
            # SubStep-2: Fix code
            # -------------------
            logger.debug(f"SubStep-2: Fix code [{i}]")
            async for line in fix_code(
                context=context, analyzer_result=analyzer_result
            ):
                # Events: AGENT_RESULT
                data = json.loads(line)
                yield SSEPayload(
                    event=EventType(data["event"]),
                    payload=data.get("payload", {}),
                )

            # -----------------------
            # SubStep-3: Re-run build
            # -----------------------
            logger.debug(f"SubStep-3: Re-run build [{i}]")
            rebuild_result = await run_build(context, settings)
            context.rebuild_result = rebuild_result
            yield SSEPayload(
                event=EventType.CHECK_RESULT,
                payload={
                    "checker": "Build",
                    "result": rebuild_result.result,
                    "rule_id": "npm run build (rebuild)",
                    "detail": rebuild_result.detail,
                },
            )
            if rebuild_result.abort_flg:
                # --- Case-2: abort ---
                yield SSEPayload(
                    event=EventType.CHECK_RESULT,
                    payload={
                        "checker": "Build",
                        "result": rebuild_result.result,
                        "rule_id": "npm run build (rebuild)",
                        "detail": rebuild_result.detail,
                    },
                )

            if rebuild_result.result:
                # --- Case-3: success ---
                break

            # --- Case-1: retryable
            last_build_result = rebuild_result

        except Exception as e:
            logger.error(f"Exception: {e}")

            yield SSEPayload(
                event=EventType.SYSTEM_ERROR,
                payload=SystemError(
                    error="Unexpected Error",
                    detail=str(e),
                ).model_dump(),
            )
            raise
