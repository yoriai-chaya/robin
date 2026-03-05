"""
A handler for code generation, ESLint checking, and build checking

Notes:
- error_payload
    In the following statement:
    error_payload = SystemError(error="Unexpected error", detail=str(e))
    The error value (e.g., "Unexpected error") is displayed in the frontend UI (Left-Panel)
    Keep this error message within 20 characters.
"""

from typing import AsyncIterator, Awaitable, Callable

from app.base import (
    DebugMode,
    DonePayload,
    DoneStatus,
    EventType,
    FunctionResult,
    LocalContext,
    LoopAction,
    SystemError,
)
from app.checkpoint import debug_checkpoint
from app.config import Settings
from app.logger import logger
from app.step_check_code import check_code_step
from app.step_gen_code import gen_code_step
from app.step_run_build import run_build_step
from app.step_run_rebuild import run_rebuild_step

SSEEventCallable = Callable[[str, dict], Awaitable[str]]


async def handle_gen_code(
    prompt: str,
    context: LocalContext,
    settings: Settings,
    sse_event: SSEEventCallable,
) -> AsyncIterator[str]:
    category = context.category
    logger.info(f"[{category}]: Start Code Generation")

    # Completed payload (may be overwritten)
    final_payload = DonePayload(
        status=DoneStatus.COMPLETED,
        message="All Tasks Completed",
    )
    try:
        debug_mode = DebugMode.CONTINUE
        next_prompt = prompt

        # =========================
        # Code Generation Loop
        # =========================
        success = False
        for i in range(settings.code_gen_retry):
            logger.debug(f"Code Gen Loop [{i}]")

            # -------------------------------
            # 1. Create Code (prepare prompt)
            # -------------------------------
            final_prompt = next_prompt
            add_prompts_len = len(context.add_prompts)

            logger.debug(
                f"[Prompt] Base prompt len={len(final_prompt)}, "
                f"number of additional prompts={add_prompts_len}"
            )

            if add_prompts_len != 0:
                logger.debug("[Prompt] Extending prompt with additional messages")
                for add_prompt in context.add_prompts:
                    logger.debug(f"[Prompt] Additional prompt: {add_prompt}")
                    final_prompt = f"{final_prompt}\n- {add_prompt}\n"
                    logger.debug(f"final_prompt: {final_prompt}")

            # --------------------------------------------
            # 2. CP1: Debug Checkpoint - before gen_code()
            # --------------------------------------------
            logger.debug(f"[CP1] Current debug_mode: {debug_mode}")
            if settings.debug:
                debug_mode = await debug_checkpoint(
                    cp_name="CP1",
                    current_mode=debug_mode,
                )
                if debug_mode == DebugMode.END:
                    logger.debug("[CP1] Exiting loop")
                    break

            # ------------------
            # 3. Call gen_code()
            # ------------------
            if debug_mode != DebugMode.SKIP_AGENT:
                logger.debug("gen_code_step called")
                async for ev in gen_code_step(
                    final_prompt=final_prompt,
                    context=context,
                ):
                    yield await sse_event(ev.event, ev.payload)

                if context.loop_action == LoopAction.CONTINUE:
                    continue
                if context.loop_action == LoopAction.BREAK:
                    break
            else:
                logger.debug("[gen_code] Skipping gen_code()")

            # --------------------------------------------------
            # 4. CP2: Debug Checkpoint - before check_gen_code()
            # --------------------------------------------------
            logger.debug(f"[CP2] Current debug_mode: {debug_mode}")
            if settings.debug:
                debug_mode = await debug_checkpoint(
                    cp_name="CP2",
                    current_mode=debug_mode,
                )
                if debug_mode == DebugMode.END:
                    logger.debug("[CP2] Exiting loop")
                    break

            # ------------------------
            # 5. Call check_gen_code()
            # ------------------------
            if debug_mode != DebugMode.SKIP_AGENT:
                logger.debug("check_code_step called")
                async for ev in check_code_step(
                    prompt=prompt,
                    context=context,
                ):
                    yield await sse_event(ev.event, ev.payload)

                if context.loop_action == LoopAction.CONTINUE:
                    continue
                if context.loop_action == LoopAction.BREAK:
                    success = True
                    break
            else:
                logger.debug("[check_gen_code] Skipping check_gen_code()")

        # ---------------------------------------------
        # 6. Retry Limit Check
        # ---------------------------------------------
        if not success:
            logger.error("[retry limit check] Retry limit exceeded")
            final_payload = DonePayload(
                status=DoneStatus.FAILED,
                message="Retry Limit exceeded",
            )
            yield await sse_event(EventType.DONE, final_payload.model_dump())
            return

        # ---------------------------------------------
        # 7. CP3: Debug Checkpoint - before run_build()
        # ---------------------------------------------
        logger.debug(f"[CP3] Current debug_mode: {debug_mode}")
        if settings.debug:
            debug_mode = await debug_checkpoint(
                cp_name="CP3",
                current_mode=debug_mode,
                context=context,
            )

        # -------------------
        # 8. Call run_build()
        # -------------------
        logger.debug(f"[run_build] context.build_check: {context.build_check}")
        rebuild_flg = True
        if context.build_check and debug_mode != DebugMode.SKIP_AGENT:
            build_step = await run_build_step(
                context=context,
                settings=settings,
            )

            for ev in build_step.sse_events:
                yield await sse_event(ev.event, ev.payload)

            _build_result = build_step.result
            if _build_result is None:
                raise RuntimeError("build_result is None")

            build_result: FunctionResult = _build_result

            # --- Case-2: abort ---
            if build_result.abort_flg:
                logger.error("build: abort_flg=True -> FAILED")
                payload = DonePayload(
                    status=DoneStatus.FAILED,
                    message="Build failed",
                )
                yield await sse_event(EventType.DONE, payload.model_dump())
                return

            if build_result.result:
                # --- Case-3: success ---
                rebuild_flg = False
            else:
                # --- Case-1: retryable -> rebuild ---
                logger.warning("build: retryable error -> run_rebuild")

        # ---------------------
        # 9. Call run_rebuild()
        # ---------------------
        if rebuild_flg and context.build_check and debug_mode != DebugMode.SKIP_AGENT:
            try:
                async for ev in run_rebuild_step(
                    context=context,
                    settings=settings,
                    build_result=build_result,
                ):
                    yield await sse_event(ev.event, ev.payload)
            except Exception as e:
                logger.error(f"run_rebuild_step exception e: {str(e)}")
                final_payload = DonePayload(
                    status=DoneStatus.FAILED, message="Unexpected Error"
                )
                yield await sse_event(EventType.DONE, final_payload.model_dump())
                return

            rebuild_result = context.rebuild_result
            if rebuild_result is None:
                raise RuntimeError("rebuild_result is None")

            # --- rebuild result handling ---
            if rebuild_result.abort_flg:
                # --- Case-2: abort ---
                logger.error("rebuild: abort_flg=True -> FAILED")
                payload = DonePayload(
                    status=DoneStatus.FAILED,
                    message="Build failed",
                )
                yield await sse_event(EventType.DONE, payload.model_dump())
                return

            if not rebuild_result.result:
                # --- Case-1: retryable -> failed ---
                logger.info("rebuild: retryable -> FAILED")
                payload = DonePayload(
                    status=DoneStatus.FAILED,
                    message="Build completed",
                )
                yield await sse_event(EventType.DONE, payload.model_dump())
                return

            # --- Case-3: success ---
            # to Done

    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        error_payload = SystemError(error="Unexpected Error", detail=str(e))
        yield await sse_event(EventType.SYSTEM_ERROR, error_payload.model_dump())
        final_payload = DonePayload(
            status=DoneStatus.FAILED, message="Unexpected Error"
        )
        yield await sse_event(EventType.DONE, final_payload.model_dump())
        return

    # =========================
    # Done
    # =========================
    logger.info(f"[{category}]: All Tasks Completed")
    yield await sse_event(
        EventType.DONE,
        final_payload.model_dump(),
    )
