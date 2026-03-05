import time
from pathlib import Path

from app.base import (
    FunctionResult,
    LoadPlaywrightReport,
    LocalContext,
    RunTestsResultPayload,
)
from app.common import archive
from app.edit_playwright_report import (
    create_summary_report_file,
    load_playwright_report,
)
from app.logger import logger

EVAL_TESTS_TIMEOUT = 10
EVAL_TESTS_POLL_INTERVAL = 0.5
EVAL_TESTS_STABLE_CHECKS = 2


def _wait_for_update(
    path: Path,
    before_mtime: float,
    timeout: float,
    poll_interval: float,
    stable_checks: int,
) -> bool:
    """
    playright_report file update checkpoint

    (1) current_mtime > before_mtime
    (2) check the file size remains unchanged for 'stable_checks' times
    """
    logger.debug(
        f"_wait_for_update called: path={path}, before_mtime={before_mtime}, timeout={timeout}, poll_interval={poll_interval}, stable_checks={stable_checks}"
    )
    deadline = time.time() + timeout
    last_size = None
    stable_count = 0

    while time.time() < deadline:
        current_mtime = path.stat().st_mtime
        logger.debug(
            f"while loop: stable_count={stable_count}, current_mtime={current_mtime}, before_mtime={before_mtime}, last_size={last_size}"
        )
        if current_mtime > before_mtime:
            size = path.stat().st_size
            if size == last_size and size >= 0:
                stable_count += 1
            else:
                stable_count = 1 if size >= 0 else 0
            last_size = size

            if stable_count >= stable_checks:
                logger.debug("_wait_for_update return : True")
                return True
        else:
            pass

        time.sleep(poll_interval)

    logger.debug("_wait_for_update return : False")
    return False


def eval_test_results(context: LocalContext) -> RunTestsResultPayload:
    logger.debug("eval_test_results called")

    output_dir: Path = context.output_dir
    logger.debug(f"output_dir: {str(output_dir)}")
    results_dir: Path = context.results_dir
    logger.debug(f"results_dir: {str(results_dir)}")
    playwright_report_file = context.playwright_report_file
    logger.debug(f"playwright_report_file: {playwright_report_file}")
    playwright_report_summary_file = context.playwright_report_summary_file
    logger.debug(f"playwright_report_summary_file: {playwright_report_summary_file}")
    test_file = context.test_file
    logger.debug(f"test_file: {test_file}")

    report_path: Path = output_dir / results_dir / playwright_report_file
    logger.debug(f"report_path: {report_path}")

    if report_path.exists():
        timeout = EVAL_TESTS_TIMEOUT
        poll_interval = EVAL_TESTS_POLL_INTERVAL
        stable_checks = EVAL_TESTS_STABLE_CHECKS
        updated = _wait_for_update(
            report_path, context.before_mtime, timeout, poll_interval, stable_checks
        )
        if not updated:
            detail = "Timeout waiting for playwright report file update"
            test_results = RunTestsResultPayload(result=False, detail=detail)
            return test_results

    result: LoadPlaywrightReport = load_playwright_report(str(report_path))
    if not result.result:
        test_results = RunTestsResultPayload(result=False, detail=result.detail)
        return test_results
    if result.suites:
        create_result: FunctionResult = create_summary_report_file(
            result.suites, report_path
        )
        src_dir = output_dir / results_dir
        try:
            archive(
                src_dir=src_dir,
                src_file=playwright_report_summary_file,
                dir=Path("./playwright"),
                stepid_dir=context.stepid_dir,
            )
        except Exception as e:
            logger.error(f"Failed backup: {e}")
            test_results = RunTestsResultPayload(
                result=False, detail=create_result.detail
            )
            return test_results

        if not create_result.result:
            test_results = RunTestsResultPayload(
                result=False, detail=create_result.detail
            )
            return test_results

        test_results = RunTestsResultPayload(
            result=result.suites.result,
            name=result.suites.name,
            file=result.suites.file,
            total=result.suites.total,
            ok=result.suites.ok,
            ng=result.suites.ng,
            specs=result.suites.specs.copy(),
        )

    logger.debug("return test_results")
    return test_results
