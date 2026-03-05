import json
import sys
from pathlib import Path

from app.base import LoadPlaywrightReport
from app.config import get_settings
from app.edit_playwright_report import load_playwright_report
from app.logger import logger

if __name__ == "__main__":
    # Get Settings / Config Data
    settings = get_settings()
    # output_dir = base_dir / settings.output_dir
    output_dir = settings.output_dir
    logger.debug(f"output_dir: {output_dir}")
    custom_config_file = output_dir / settings.playwright_customconfig_file
    logger.debug(f"custom_config_file: {custom_config_file}")
    if not custom_config_file.exists():
        logger.error(f"{custom_config_file} not found")
        sys.exit(1)
    try:
        with open(custom_config_file, "r") as f:
            custom_config = json.load(f)
    except Exception as e:
        logger.error(f"{custom_config_file} open failed: {e}")
        sys.exit(1)

    results = custom_config["results"]
    logger.debug(f"results: {results}")
    playwright_report_file = custom_config["playwright_report_file"]
    logger.debug(f"playwright_report_file: {playwright_report_file}")
    playwright_report_summary_file = custom_config["playwright_report_summary_file"]
    logger.debug(f"playwright_report_summary_file: {playwright_report_summary_file}")
    playwright_report_path = output_dir / results / playwright_report_file
    playwright_report_summary_path = (
        output_dir / results / playwright_report_summary_file
    )

    # Load Playwright Report File
    my_name = Path(__file__).name
    logger.info(f"{my_name} Started")
    result: LoadPlaywrightReport = load_playwright_report(playwright_report_path)
    if not result.result:
        logger.error(f"Playwright report file loading error: detail={result.detail}")
        sys.exit(1)

    # Output
    if result.suites:
        input_path = Path(playwright_report_path)
        print(json.dumps(result.suites.model_dump(), indent=2, ensure_ascii=False))
