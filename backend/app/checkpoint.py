import asyncio
from pathlib import Path
from typing import Optional

from app.base import CodeGenResponse, DebugMode, LocalContext
from app.logger import logger


async def wait_for_console_input() -> DebugMode:
    """
    Wait for debug command from console and return DebugMode
    """
    loop = asyncio.get_event_loop()
    prompt = 'Enter cmd - "e":end, "s":skip agent, "c": continue, "l": load code : '
    user_input = await loop.run_in_executor(None, input, prompt)
    cmd = user_input.strip().lower()

    for mode in DebugMode:
        if cmd == mode.value:
            return mode
    return DebugMode.END


async def debug_checkpoint(
    *,
    cp_name: str,
    current_mode: DebugMode,
    context: Optional[LocalContext] = None,
) -> DebugMode:
    """
    Common debug checkpoint handler
    """
    logger.debug(f"[{cp_name}] Current debug_mode: {current_mode}")
    logger.debug(f"[{cp_name}] Waiting for input from the console")

    debug_mode = await wait_for_console_input()
    logger.debug(f"[{cp_name}] Entered debug_mode: {debug_mode}")

    if debug_mode == DebugMode.LOAD_CODE and context is not None:
        await _handle_load_code(context)

    return debug_mode


async def _handle_load_code(context: LocalContext) -> None:
    """
    LOAD_CODE command handler (used in CP3)
    """
    loop = asyncio.get_event_loop()
    src_file = await loop.run_in_executor(
        None, input, "Enter source filename to load: "
    )
    dst_file = await loop.run_in_executor(
        None, input, "Enter destination filename to save: "
    )

    src_path = Path(src_file).expanduser()
    dst_path = Path(dst_file).expanduser()

    try:
        content = src_path.read_text(encoding="utf-8")
        dst_path.write_text(content, encoding="utf-8")
        logger.debug(f"[LOAD_CODE] {src_path} -> {dst_path}")

        context.response = CodeGenResponse(
            result=True,
            detail="saved successfully (debug)",
            code=content,
        )
    except Exception as e:
        logger.error(f"[LOAD_CODE] Failed: {e}")
        raise
