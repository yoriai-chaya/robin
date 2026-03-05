import shutil
from datetime import datetime
from pathlib import Path

from app.logger import logger


def resolve_path(dir_name: Path) -> Path:
    """
    Resolves the specified dir_name into an absolute path.
    """
    logger.debug(f"resolve_path called: dir_name={dir_name}")
    if dir_name.is_absolute():
        # Absolute path
        if not dir_name.exists():
            raise FileNotFoundError(f"dir_name '{dir_name}' not found")
        logger.debug(f"Absolute path resolved: {dir_name}")
        return dir_name
    # Relative path
    base = Path().resolve()
    logger.debug(f"base: {base}")
    abs_path = (base / dir_name).resolve()
    logger.debug(f"abs_path: {abs_path}")
    if not abs_path.exists():
        raise FileNotFoundError(f"Path '{abs_path}' not found")
    return abs_path


def archive(src_dir: Path, src_file: str, stepid_dir: Path, dir: Path):
    """
    archive: back up the generated source files, test report files, etc.

    Args:
        src_dir: directory of source file
        src_file: source file to be backed up
        stepid_dir: stepid directory (contained in the local context)
        dir: relative directory from stepid_dir
    """
    logger.debug("archive called")
    src_path = src_dir / src_file
    logger.debug(f"src_path : {src_path}")

    backup_dir = stepid_dir / dir
    logger.debug(f"backup_dir : {backup_dir}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / src_file
    logger.debug(f"backup_path : {backup_path}")

    if backup_path.exists():
        try:
            mtime = backup_path.stat().st_mtime
            dt = datetime.fromtimestamp(mtime)
            timestamp = dt.strftime("%Y%m%d_%H%M%S")

            stem = backup_path.stem
            suffix = backup_path.suffix
            archived_name = f"{stem}_{timestamp}{suffix}"
            archived_path = backup_dir / archived_name

            # Rename
            backup_path.rename(archived_path)
            logger.debug(f"Archived old backup: {backup_path} -> {archived_path}")

        except Exception as e:
            logger.error(f"Failed to archive existing file: {backup_path}, {e}")
            raise e
    try:
        shutil.copy2(str(src_path), str(backup_path))
        logger.debug(f"backup: {src_path} -> {backup_path}")
    except Exception as e:
        logger.error(f"Failed to backup file: {backup_path}, {e}")
        raise e
