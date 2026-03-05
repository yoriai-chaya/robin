import json
from pathlib import Path
from subprocess import CompletedProcess
from typing import List

from app.base import FunctionResult, LocalContext
from app.common import archive
from app.config import Settings
from app.logger import logger
from app.run_command import run_cmd

BUILD_LOGFILE = "build.log"
BUILD_DIR = Path("build")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def extract_stderr_messages(records: List[dict]) -> List[str]:
    return [r.get("message", "") for r in records if r.get("stream") == "stderr"]


async def run_build(context: LocalContext, settings: Settings) -> FunctionResult:
    """
    Case-1: result=False, abort_flg=False  # retryable
    Case-2: result=False, abort_flg=True   # abort
    Case-3: result=True, abort_flg=False   # success
    """
    logger.debug("run_build called")
    cwd = str(context.output_dir)
    logger.debug(f"cwd: {cwd}")
    build_dir = context.output_dir / settings.test_results_dir
    build_dir.mkdir(exist_ok=True)

    output_path = build_dir / BUILD_LOGFILE
    logger.debug(f"output_path: {output_path}")

    option = f"--logs-dir={str(build_dir)}"
    command = ["npm", "run", "build:agent", "--", option]
    logger.debug(f"stepid_dir: {context.stepid_dir}")

    try:
        cmd_result: CompletedProcess = run_cmd(
            stepid_dir=context.stepid_dir,
            command=command,
            output_path=output_path,
            cwd=cwd,
        )
        logger.debug(f"cmd_result: {cmd_result}")
    except FileNotFoundError as e:
        logger.error(f"Build failed : {e}")
        detail = str(e)
        # Case-2: result=False, abort_flg=True   # abort
        return FunctionResult(result=False, abort_flg=True, detail=detail)

    if cmd_result.returncode != 0:
        stderr = cmd_result.stderr or ""
        stderr = stderr.strip()

        if "Missing script" in stderr:
            detail = f"Build command configuration error: {stderr}"
            logger.error(detail)
            return FunctionResult(result=False, abort_flg=True, detail=detail)

    customconfig_dir = context.output_dir
    customconfig_file = settings.build_customconfig_file
    customconfig_path = customconfig_dir / customconfig_file
    logger.debug(f"customconfig_path: {customconfig_path}")

    try:
        with open(customconfig_path, "r", encoding="utf-8") as f:
            customconfig = json.load(f)
        build_report_file = customconfig.get("build_report_file")
        if not build_report_file:
            # Case-2: result=False, abort_flg=True   # abort
            detail = "Failed to get build_report_file"
            logger.error(detail)
            return FunctionResult(result=False, abort_flg=True, detail=detail)
    except Exception as e:
        # Case-2: result=False, abort_flg=True   # abort
        detail = f"Failed to build-customconfig file: {e}"
        logger.error(detail)
        return FunctionResult(result=False, abort_flg=True, detail=detail)

    logger.debug(f"build_report_file: {build_report_file}")
    build_report_path = build_dir / build_report_file
    logger.debug(f"build_report_path: {build_report_path}")
    if not build_report_path.exists():
        # Case-2: result=False, abort_flg=True   # abort
        detail = f"{build_report_path} does not exist."
        return FunctionResult(result=False, abort_flg=True, detail=detail)

    result_data = load_json(build_report_path)

    error_count = int(result_data.get("summary", {}).get("errorCount", 0))
    if error_count == 0:
        # Case-3: result=True, abort_flg=False   # success
        archive(build_dir, BUILD_LOGFILE, context.stepid_dir, BUILD_DIR)
        archive(build_dir, build_report_file, context.stepid_dir, BUILD_DIR)
        logger.debug(f"No errors : error_count={error_count}")
        return FunctionResult(result=True, abort_flg=False, detail="")

    # Case-1: result=False, abort_flg=False  # retryable
    records = result_data.get("records", [])
    messages = extract_stderr_messages(records)

    result_detail = "".join(m + "\n" for m in messages)
    archive(build_dir, BUILD_LOGFILE, context.stepid_dir, BUILD_DIR)
    archive(build_dir, build_report_file, context.stepid_dir, BUILD_DIR)
    logger.debug(f"Build Errors - result_detail: {result_detail}")
    return FunctionResult(result=False, abort_flg=False, detail=result_detail)
