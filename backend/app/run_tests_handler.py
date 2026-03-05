import asyncio
import time
from pathlib import Path
from typing import Awaitable, Callable

from agents import Runner

from app.agent_logger import AgentLogger
from app.base import (
    AgentUpdatePayload,
    DonePayload,
    DoneStatus,
    EventType,
    LocalContext,
    RunPlaywrightFunctionResult,
    SystemError,
    TestScreenshotPayload,
)
from app.common import archive
from app.config import Settings
from app.custom_agents import get_run_tests_agent
from app.eval_tests import eval_test_results
from app.logger import logger

SSEEventCallable = Callable[[str, dict], Awaitable[str]]


async def wait_for_screenshot_update(
    path: Path,
    before_mtime: float,
    timeout_sec: float = 5.0,
    interval_sec: float = 0.5,
) -> bool:
    """
    Wait until screenshot file is updated (mtime > before_mtime)
    before_mtime: playwright_report_file creation time

    Returns:
        True  : updated within timeout
        False : timeout or file not found
    """
    start = time.monotonic()
    last_mtime: float | None = None
    while True:
        if path.exists():
            mtime = path.stat().st_mtime
            last_mtime = mtime
            if mtime > before_mtime:
                return True
        if time.monotonic() - start >= timeout_sec:
            return False
        logger.debug(f"mtime: {last_mtime}, before_mtime: {before_mtime}")
        await asyncio.sleep(interval_sec)


async def handler_run_tests(
    prompt: str,
    context: LocalContext,
    settings: Settings,
    sse_event: SSEEventCallable,
):
    category = context.category
    logger.info(f"[{category}] : Run Tests Handler started")

    final_payload = DonePayload(
        status=DoneStatus.COMPLETED, message="RunTests completed"
    )

    try:
        run_tests_agent = get_run_tests_agent()
        result = Runner.run_streamed(
            starting_agent=run_tests_agent,
            input=prompt,
            context=context,
            max_turns=context.max_turns,
            hooks=AgentLogger(),
        )
        async for event in result.stream_events():
            if event.type == "agent_updated_stream_event":
                logger.debug(f"Agent updated: {event.new_agent.name}")
                agent_name = event.new_agent.name
                agent_update_payload = AgentUpdatePayload(agent_name=agent_name)
                yield await sse_event(
                    EventType.AGENT_UPDATE, agent_update_payload.model_dump()
                )
            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    logger.debug(f"Event: tool_call_item result={result}")
                elif event.item.type == "tool_call_output_item":
                    logger.debug(f"Event: tool_call_output_item result={result}")
                elif event.item.type == "message_output_item":
                    logger.debug(f"Event: message_output_item result={result}")

        final: RunPlaywrightFunctionResult = result.final_output
        logger.trace(f"final: {final}")
        if final.abort_flg:
            final_payload = DonePayload(
                status=DoneStatus.FAILED,
                message=final.detail or "run_playwright failed",
            )
        else:
            # Evaluate
            test_results = eval_test_results(context=context)
            logger.trace(f"test_results: {test_results}")
            yield await sse_event(EventType.TEST_RESULT, test_results.model_dump())
            if not final.result:
                final_payload = DonePayload(
                    status=DoneStatus.FAILED, message="RunTests failed"
                )
            output_dir = context.output_dir
            results_dir = context.results_dir
            screenshot_dir = Path(context.screenshot_dir)
            before_mtime = context.before_mtime
            for ss in context.screenshots:
                screenshot_path = (
                    output_dir / results_dir / screenshot_dir / ss.filename
                )
                if not screenshot_path.exists():
                    logger.warning(f"Screenshot file does not exist: {screenshot_path}")
                    continue
                logger.debug(f"Waiting for screenshot update: {screenshot_path}")
                updated = await wait_for_screenshot_update(
                    path=screenshot_path,
                    before_mtime=before_mtime,
                    timeout_sec=5.0,
                    interval_sec=0.5,
                )
                if not updated:
                    error_msg = f"Screenshot not updated within timeout: {ss.filename}"
                    logger.error(error_msg)
                    error_payload = SystemError(
                        error="ScreenshotTimeout", detail=error_msg
                    )
                    yield await sse_event(
                        EventType.SYSTEM_ERROR, error_payload.model_dump()
                    )
                    final_payload = DonePayload(
                        status=DoneStatus.FAILED, message="Screenshot update timeout"
                    )
                    yield await sse_event(EventType.DONE, final_payload.model_dump())
                    return
                payload = TestScreenshotPayload(
                    spec=ss.spec,
                    filename=ss.filename,
                    url=ss.relative_url,
                    updated=final.screenshot_updated,
                )
                logger.debug(f"payload: {payload}")
                src_dir = output_dir / results_dir / screenshot_dir
                src_file = ss.filename
                stepid_dir = context.stepid_dir
                dir = Path("./playwright")
                archive(
                    src_dir=src_dir, src_file=src_file, stepid_dir=stepid_dir, dir=dir
                )
                yield await sse_event(EventType.TEST_SCREENSHOT, payload.model_dump())

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug(f"name: {e.__class__.__name__}, detail: {str(e)}")
        error_payload = SystemError(error="Unexpected error", detail=str(e))
        yield await sse_event(EventType.SYSTEM_ERROR, error_payload.model_dump())
        final_payload = DonePayload(
            status=DoneStatus.FAILED, message="run tests code error occurred"
        )

    logger.info(f"[{category}] : Run Tests Handler completed")
    yield await sse_event(EventType.DONE, final_payload.model_dump())
