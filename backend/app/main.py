import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from app.base import (
    DonePayload,
    DoneStatus,
    EventType,
    PromptCategory,
    PromptHeaderKey,
    PromptRequest,
    PromptResponse,
    StartedPayload,
    StartedStatus,
    SystemError,
    TreeNode,
)
from app.build_tree import build_tree
from app.config import get_settings
from app.context_factory import create_local_context
from app.gen_code_handler import handle_gen_code
from app.logger import logger
from app.place_files_handler import handle_place_files
from app.prompt_parser import (
    extract_from_prompt,
    parse_build_check,
    resolve_placeholders,
)
from app.run_tests_handler import handler_run_tests

DIR_USER = "user"


async def sse_event(event_name: str, payload: dict) -> str:
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def sse_system_error(error: str, detail: str, sse_event):
    error_payload = SystemError(error=error, detail=detail)
    return await sse_event(EventType.SYSTEM_ERROR, error_payload.model_dump())


async def sse_failed_done(message: str, sse_event):
    fainal_payload = DonePayload(status=DoneStatus.FAILED, message=message)
    return await sse_event(EventType.DONE, fainal_payload.model_dump())


# Settings
settings = get_settings()

# Session Store
sessions: Dict[str, str] = {}

# FastAPI Main
logger.info("===== Robin start =====")
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# FastAPI Starter
@app.get("/")
async def root():
    logger.info("[Hello]")
    return {"message": "Hello World"}


# Echo Service (for test)
@app.post("/prompt", response_model=PromptRequest)
async def prompt_service(request: PromptRequest):
    logger.info(f"[Echo] request: {request}")
    return PromptResponse(prompt=request.prompt)


# Create Session
@app.post("/main")
async def create_session(request: PromptRequest):
    logger.trace(f"create session request: {request}")
    session_id = str(uuid4())
    sessions[session_id] = request.prompt
    logger.debug(f"session_id: {session_id}")
    return JSONResponse({"session_id": session_id})


# Main Service
@app.get("/main/stream/{session_id}")
async def stream_service_get(session_id: str):
    logger.debug("stream_service_get called")
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="session not found")

    prompt = sessions.pop(session_id)
    category = extract_from_prompt(prompt, PromptHeaderKey.CATEGORY)
    logger.debug(f"category: {category}")
    build_check_value = extract_from_prompt(prompt, PromptHeaderKey.BUILD_CHECK)
    logger.debug(f"build_check_value: {build_check_value}")
    build_check = parse_build_check(build_check_value)
    logger.debug(f"build_check: {build_check}")

    async def generator(prompt: str):
        # Heartbeat
        async def heartbeat():
            while True:
                yield ": keep-alive\n\n"  # SSE Comment Frame
                await asyncio.sleep(15)

        hb = heartbeat()
        yield await hb.__anext__()

        # Start
        logger.debug("Agents starting ...")
        now = datetime.now()
        formatted_time = now.strftime("%Y%m%d-%H%M%S")
        step_id = f"StepID-{formatted_time}"
        started_payload = StartedPayload(
            status=StartedStatus.STARTED, message="Started Tasks", step_id=step_id
        )
        yield await sse_event(EventType.STARTED, started_payload.model_dump())

        if not category:
            logger.error("Category not found")
            yield await sse_system_error(
                error="InvalidPrompt", detail="Category not found", sse_event=sse_event
            )
            yield await sse_failed_done("Invalid prompt", sse_event=sse_event)
            return

        if category == PromptCategory.GEN_CODE:
            if build_check is None:
                logger.error("Invalid or not specified BuildCheck value")
                yield await sse_system_error(
                    error="InvalidPrompt",
                    detail="Invalid or not specified BuildCheck value (expected: - BuildCheck: On/Off)",
                    sse_event=sse_event,
                )
                yield await sse_failed_done("Invalid prompt", sse_event=sse_event)
                return

        try:
            context = create_local_context(
                category=category, build_check=build_check, settings=settings
            )
        except Exception as e:
            logger.error(f"create_local_context error: {e}")
            yield await sse_system_error(
                error="ContextError",
                detail=str(e),
                sse_event=sse_event,
            )
            yield await sse_failed_done("Context error", sse_event=sse_event)
            return
        logger.debug(f"context: {context}")

        try:
            resolved_prompt = resolve_placeholders(prompt=prompt, context=context)
        except Exception as e:
            logger.error("_resolve_placeholders failed")
            yield await sse_system_error(
                error="InvalidPrompt",
                detail=str(e),
                sse_event=sse_event,
            )
            yield await sse_failed_done("Invalid prompt", sse_event=sse_event)
            return

        handler_map = {
            PromptCategory.GEN_CODE: handle_gen_code,
            PromptCategory.PLACE_FILES: handle_place_files,
            PromptCategory.RUN_TESTS: handler_run_tests,
        }

        handler = handler_map.get(category)  # type: ignore
        if not handler:
            logger.error("InvalidCategory")
            yield await sse_system_error(
                error="InvalidCategory",
                detail="Unknown category: {category}",
                sse_event=sse_event,
            )
            yield await sse_failed_done("Invalid category", sse_event=sse_event)
            return

        logger.trace(f"handler call: resolved_prompt: {resolved_prompt}")
        async for event in handler(resolved_prompt, context, settings, sse_event):
            yield event

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
    }
    return StreamingResponse(
        content=generator(prompt=prompt),
        media_type="text/event-stream",
        headers=headers,
    )


@app.get("/artifacts/results/screenshot/{filename}")
def get_screenshot(filename: str):
    logger.debug("get_screenshot called")
    path = settings.output_dir / "results" / "screenshot" / filename
    logger.debug(f"path: {path}")
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(
        path, media_type="image/png", headers={"Cache-Control": "no-store"}
    )


@app.get(
    "/autorun/filelist", response_model=List[TreeNode], summary="Get AutoRun file list"
)
def get_autorun_filelist(autorun_id: str):
    logger.debug(f"get_autorun_filelist autorun_id: {autorun_id}")

    project_root = Path.cwd()
    target_dir = project_root / settings.prompts_dir / DIR_USER / autorun_id

    if not target_dir.exists() or not target_dir.is_dir():
        not_found_message = (
            f"Specified AutoRun-ID directory does not exist. dir={target_dir}"
        )
        logger.warning(not_found_message)
        raise HTTPException(status_code=404, detail=not_found_message)
    try:
        return build_tree(target_dir, current_depth=1)
    except HTTPException as e:
        logger.warning(f"HTTPException : {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected internal error e:{e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
