import json
import re
from pathlib import Path
from typing import List

from app.base import (
    FunctionResult,
    LoadPlaywrightReport,
    PlaywrightSpecs,
    PlaywrightSuites,
)
from app.logger import logger
from app.playwright_base import PwReport


def _strip_ansi_codes(text: str | None) -> str | None:
    if text is None:
        return None
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def load_playwright_report(
    report_path: str,
) -> LoadPlaywrightReport:
    logger.debug(f"load_playwright_report called  report_path: {report_path}")

    # Load Report File
    path = Path(report_path)
    if not path.exists():
        result = LoadPlaywrightReport(
            result=False, detail=f"File not found: {report_path}"
        )
        return result
    try:
        report_data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        result = LoadPlaywrightReport(
            result=False, detail=f"Failed to open file: {report_path}: {e}"
        )
        return result
    except json.JSONDecodeError as e:
        result = LoadPlaywrightReport(
            result=False, detail=f"Failed to parse JSON in {report_path}: {e}"
        )
        return result

    report = PwReport(**report_data)
    logger.debug(f"report: {report}")

    # Analyze
    error_detail = None
    if report.errors:
        for err in report.errors:
            if err.message:
                error_detail = _strip_ansi_codes(err.message)
                break

    if report.suites:
        if not report.suites[0].suites:
            error_detail = "Unexpected error in parsing playwright report"
        else:
            specs_data = report.suites[0].suites[0].specs

    # Return
    if error_detail:
        result = LoadPlaywrightReport(result=False, detail=error_detail)
        logger.debug(f"load_playwright_report return  result: {result}")
        return result

    specs: List[PlaywrightSpecs] = []

    for spec in specs_data:
        ok = spec.ok
        error_message = None
        error_stack = None
        error_summary = None

        if not ok:
            try:
                first_result = spec.tests[0].results[0].errors
                logger.debug(f"first_result: {first_result}")
                error_message = _strip_ansi_codes(first_result[0].message)
                logger.debug(f"error_message: {error_message}")
                error_stack = _strip_ansi_codes(first_result[0].stack)

            except Exception as e:
                logger.debug(f"Unexpected error: {e}")
                result = LoadPlaywrightReport(
                    result=False, detail=f"Unexpected error: {e}"
                )
                return result

        specs.append(
            PlaywrightSpecs(
                title=spec.title,
                result=ok,
                error_summary=error_summary,
                error_message=error_message,
                error_stack=error_stack,
            )
        )

    ok_count = sum(1 for s in specs if s.result)
    ng_count = sum(1 for s in specs if not s.result)

    suite_result = all(s.result for s in specs)

    playwright_suites = PlaywrightSuites(
        name=report.suites[0].suites[0].title,
        file=report.suites[0].suites[0].file,
        result=suite_result,
        total=len(specs),
        ok=ok_count,
        ng=ng_count,
        specs=specs,
    )
    result = LoadPlaywrightReport(result=True, suites=playwright_suites)
    logger.debug(f"load_playwright_report return  result: {result}")
    return result


def create_summary_report_file(
    suites: PlaywrightSuites,
    report_file_path: Path,
) -> FunctionResult:
    logger.debug(
        f"create_summary_report_file called  report_file_path: {report_file_path}"
    )
    output_file = report_file_path.with_name(
        f"{report_file_path.stem}_summary{report_file_path.suffix}"
    )
    try:
        output_file.write_text(
            json.dumps(suites.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        result = FunctionResult(result=True)
        return result
    except Exception as e:
        result = FunctionResult(result=False, detail=str(e))
        return result
