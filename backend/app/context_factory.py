import json
from datetime import datetime

from app.base import FunctionResult, IsCodeCheckError, LocalContext, LoopAction
from app.common import resolve_path
from app.config import Settings
from app.logger import logger


def create_local_context(
    category: str,
    build_check: bool,
    settings: Settings,
) -> LocalContext:
    """
    Load config files, prepare directories, and create LocalContext.
    """
    # output_dir
    output_dir = resolve_path(settings.output_dir)

    # load custom config
    custom_config_file = output_dir / settings.playwright_customconfig_file
    if not custom_config_file.exists():
        logger.error(f"{custom_config_file} not found")
        raise FileNotFoundError(f"{custom_config_file} not found")

    logger.debug(f"custom_config_file: {custom_config_file}")
    with open(custom_config_file, "r") as f:
        custom_config = json.load(f)

    # extract config values
    results = custom_config["results"]
    logger.debug(f"results: {results}")
    playwright_info_file = custom_config["playwright_info_file"]
    logger.debug(f"playwright_info_file: {playwright_info_file}")
    playwright_report_file = custom_config["playwright_report_file"]
    logger.debug(f"playwright_report_file: {playwright_report_file}")
    playwright_report_summary_file = custom_config["playwright_report_summary_file"]
    logger.debug(f"playwright_report_summary_file: {playwright_report_summary_file}")
    screenshot_dir = custom_config["screenshot_dir"]
    logger.debug(f"screenshot_dir: {screenshot_dir}")

    now = datetime.now()
    formatted_time = now.strftime("%Y%m%d-%H%M%S")
    step_id = f"StepID-{formatted_time}"
    logger.debug(f"step_id: {step_id}")

    archive_dir = settings.archive_dir
    logger.debug(f"archive_dir: {archive_dir}")
    archive_dir.mkdir(exist_ok=True)
    abs_archive_dir = resolve_path(archive_dir)
    logger.debug(f"abs_archive_dir: {abs_archive_dir}")
    stepid_dir = abs_archive_dir / step_id
    logger.debug(f"stepid_dir: {stepid_dir}")
    stepid_dir.mkdir(exist_ok=False)

    return LocalContext(
        category=category,
        output_dir=output_dir,
        max_turns=settings.openai_max_turns,
        gen_code_filepath="",
        is_code_check_error=IsCodeCheckError.NO_ERROR,
        add_prompts=[],
        results_dir=results,
        playwright_info_file=playwright_info_file,
        playwright_report_file=playwright_report_file,
        playwright_report_summary_file=playwright_report_summary_file,
        screenshot_dir=screenshot_dir,
        test_file="dummy.spec.ts",
        before_mtime=0,
        step_id=step_id,
        stepid_dir=stepid_dir,
        build_check=build_check,
        loop_action=LoopAction.NORMAL,
        rebuild_result=FunctionResult(result=True),
    )
