import subprocess
from pathlib import Path
from typing import List, Union

from agents import RunContextWrapper

from app.base import RunPlaywrightFunctionResult, ScreenshotInfo
from app.common import archive
from app.logger import logger


def run_playwright(
    ctx: RunContextWrapper,
    test_dir: str,
    test_file: str,
    project: str,
    screenshot_files: Union[str, List[str]],
) -> RunPlaywrightFunctionResult:
    logger.debug("run_playwright called")

    output_dir: Path = ctx.context.output_dir
    logger.debug(f"output_dir: {str(output_dir)}")
    results_dir: Path = ctx.context.results_dir
    logger.debug(f"results_dir: {str(results_dir)}")
    logger.debug(f"test_dir: {test_dir}")
    logger.debug(f"test_file: {test_file}")
    screenshot_dir: Path = ctx.context.screenshot_dir
    logger.debug(f"screenshot_dir: {screenshot_dir}")
    logger.debug(f"screenshot_files: {screenshot_files}")
    if isinstance(screenshot_files, str):
        screenshot_files = [screenshot_files]

    ctx.context.test_file = test_file
    test_path = output_dir / test_dir / test_file
    logger.debug(f"test_path: {str(test_path)}")
    if not test_path.is_file():
        err_msg = f"{test_path} not found"
        func_result = RunPlaywrightFunctionResult(
            result=False, abort_flg=True, detail=err_msg
        )
        return func_result

    playwright_report_file = ctx.context.playwright_report_file
    logger.debug(f"playwright_report_file: {playwright_report_file}")
    playwright_report_file_path: Path = (
        output_dir / results_dir / playwright_report_file
    )
    if playwright_report_file_path.exists():
        ctx.context.before_mtime = playwright_report_file_path.stat().st_mtime
    logger.debug(f"ctx.context.before_mtime: {ctx.context.before_mtime}")

    # Editting command line
    command = ["npx", "playwright", "test"]
    command.append(str(test_path))
    screenshot_updated = False
    if project:
        command.append(f"--project={project}")

    for screenshot_file in screenshot_files:
        screenshot_path = output_dir / results_dir / screenshot_dir / screenshot_file
        logger.debug(f"screenshot_path: {screenshot_path}")
        if not screenshot_path.is_file():
            command.append("--update-snapshots")
            screenshot_updated = True
        logger.debug(f"command: {command}")
        relative_url = f"/artifacts/results/screenshot/{screenshot_file}"
        logger.debug(f"relative_url: {relative_url}")
        ctx.context.screenshots.append(
            ScreenshotInfo(
                spec=test_file, filename=screenshot_file, relative_url=relative_url
            )
        )

    # Execute npx playwright command
    flg_404 = False
    try:
        process = subprocess.Popen(
            command,
            cwd=output_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        error_detected = None
        if process.stdout is None:
            raise RuntimeError("Failed to capture Playwright stdout")
        for line in process.stdout:
            logger.debug(f"process.stdout line: {line}")
            if '"status":404' in line:
                error_detected = "Detected 404 in test output"
                flg_404 = True
                break
            if "Error:" in line and "already used" in line:
                error_detected = "Playwright server port already in use"
                break
            if "error:" in line:
                error_detected = "playwright command execution failed"
                break
        if error_detected:
            logger.debug(f"error detectd : {error_detected}")
            func_result = RunPlaywrightFunctionResult(
                result=False, abort_flg=True, detail=error_detected
            )
            return func_result
    except Exception as e:
        err_msg = f"Error running Playwright tests: {e}"
        logger.error(err_msg)
        func_result = RunPlaywrightFunctionResult(result=False, detail=err_msg)
        return func_result

    process.wait()
    return_code = process.returncode
    err_msg = f"Playwright exited with return code: {return_code}"
    logger.debug(err_msg)

    # Backup
    if not flg_404:
        logger.debug("not flg_404 : backup info/report file")
        src_dir = output_dir / results_dir
        info_file = ctx.context.playwright_info_file
        report_file = ctx.context.playwright_report_file
        logger.debug(f"dir: {dir}")
        logger.debug(f"info_file: {info_file}")
        logger.debug(f"report_file: {report_file}")
        try:
            archive(
                src_dir=src_dir,
                src_file=info_file,
                stepid_dir=ctx.context.stepid_dir,
                dir=Path("./playwright"),
            )
            archive(
                src_dir=src_dir,
                src_file=report_file,
                stepid_dir=ctx.context.stepid_dir,
                dir=Path("./playwright"),
            )
        except Exception as e:
            logger.error(f"Faild backup: {e}")
            func_result = RunPlaywrightFunctionResult(result=False, detail=err_msg)
            return func_result

    # Return
    if return_code != 0:
        func_result = RunPlaywrightFunctionResult(result=False, detail=err_msg)
        return func_result
    logger.debug("run_playwright return")
    func_result = RunPlaywrightFunctionResult(
        result=True, screenshot_updated=screenshot_updated
    )
    return func_result
