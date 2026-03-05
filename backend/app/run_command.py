import subprocess
from pathlib import Path
from subprocess import CompletedProcess

from app.common import archive
from app.logger import logger


def run_cmd(
    stepid_dir: Path, command: list[str], output_path: Path, cwd: str
) -> CompletedProcess:
    logger.debug("run_cmd called")

    # Check output directory
    output_dir = output_path.parent
    logger.debug(f"output_dir: {output_dir}")
    if not output_dir.exists():
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")

    # Run command
    logger.debug(f"output_path: {output_path}")
    logger.debug(f"Run! : command={command}, cwd={cwd}")
    with output_path.open("w", encoding="utf-8") as f:
        result = subprocess.run(
            command, cwd=cwd, stdout=f, stderr=subprocess.PIPE, text=True
        )
    logger.debug("Run finished")

    # Archive
    filename = output_path.name
    logger.debug(f"filename: {filename}")
    archive(
        src_dir=output_dir,
        src_file=filename,
        stepid_dir=stepid_dir,
        dir=Path("eslint"),
    )

    return result
