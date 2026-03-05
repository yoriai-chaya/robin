import json
from pathlib import Path

from agents import RunContextWrapper

from app.base import CodeCheckResult, ESLintInfo
from app.logger import logger
from app.run_command import run_cmd

APP_DIR = "app"
RESULTS_DIR = "results"
ESLINT_OUTPUT_FILENAME = "eslint_result.json"
PACKAGE_JSON = "package.json"


def run_eslint(ctx: RunContextWrapper, filename: str) -> CodeCheckResult:
    logger.debug("run_eslint called")

    eslint_dir: Path = ctx.context.output_dir
    file_path = eslint_dir / APP_DIR / filename
    results_dir = eslint_dir / RESULTS_DIR
    output_path = results_dir / ESLINT_OUTPUT_FILENAME
    logger.debug(f"eslint_dir: {eslint_dir}")
    logger.debug(f"file_path: {file_path}")
    logger.debug(f"results_dir: {results_dir}")
    logger.debug(f"output_path: {output_path}")

    # for Directory check
    if not eslint_dir.exists():
        error_msg = f"ESLint directory not found : {eslint_dir}"
        eslint_result = CodeCheckResult(
            result=False, output_filename=None, error_detail=error_msg
        )
        return eslint_result
    results_dir.mkdir(exist_ok=True)

    # for Next.js install check (package.json check)
    package_json = eslint_dir / PACKAGE_JSON
    logger.debug(f"package_json: {package_json}")
    if not package_json.exists():
        error_msg = (
            f"{package_json} not found in {eslint_dir}. Next.js may not be installed."
        )
        eslint_result = CodeCheckResult(
            result=False, output_filename=None, error_detail=error_msg
        )
        return eslint_result

    # Run eslint command
    if not output_path.exists():
        with output_path.open("w", encoding="utf-8") as f:
            f.write("[]")

    command = ["npx", "eslint", str(file_path), "--format", "./eslint.formatter.mjs"]
    try:
        result = run_cmd(
            stepid_dir=ctx.context.stepid_dir,
            command=command,
            output_path=output_path,
            cwd=str(eslint_dir),
        )
    except FileNotFoundError as e:
        eslint_result = CodeCheckResult(
            result=False, output_filename=None, error_detail=str(e)
        )
        return eslint_result

    # Check Return Code
    logger.debug(f"npx eslint returncode: {result.returncode}")
    if result.returncode not in (0, 1):
        eslint_result = CodeCheckResult(
            result=False, output_filename=None, error_detail=result.stderr
        )
        return eslint_result

    try:
        with output_path.open("r", encoding="utf-8") as f:
            eslint_output = json.load(f)

        logger.debug(f"eslint_output: {eslint_output}")
        eslint_info_list = []
        for file_result in eslint_output:
            messages = file_result.get("messages", [])
            is_check_ok = len(messages) == 0

            logger.debug(f"messages: {messages}")
            for msg in messages:
                rule_id = msg.get("ruleId", "")
                logger.debug(f"rule_id: {rule_id}")
                description = ""

                rules_meta = msg.get("rulesMeta", {})
                if rule_id in rules_meta:
                    description = (
                        rules_meta[rule_id].get("docs", {}).get("description", "")
                    )
                    logger.debug(f"description: {description}")

                raw_message = msg.get("message", "")
                parsed_message = raw_message
                parsed_instruction = ""
                try:
                    parsed_json = json.loads(raw_message)
                    parsed_message = parsed_json.get("message", raw_message)
                    parsed_instruction = parsed_json.get("instruction", "")
                except json.JSONDecodeError, TypeError:
                    parsed_message = raw_message

                full_message = parsed_message
                if parsed_instruction:
                    full_message += f" ({parsed_instruction})"
                logger.debug(f"full_message: {full_message}")

                eslint_info_list.append(
                    ESLintInfo(
                        message=full_message,
                        description=description,
                        rule_id=rule_id,
                    )
                )

        logger.debug("formatted eslint output:")
        formatted_json = json.dumps(eslint_output, indent=2, ensure_ascii=False)

        with output_path.open("w", encoding="utf-8") as f:
            f.write(formatted_json)

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse JSON from {output_path} : {e}"
        eslint_result = CodeCheckResult(
            result=False, output_filename=None, error_detail=error_msg
        )
        return eslint_result

    eslint_result = CodeCheckResult(
        result=True,
        output_filename=str(output_path),
        error_detail=None,
        eslint_result=is_check_ok,
        eslint_info=eslint_info_list,
    )
    return eslint_result
