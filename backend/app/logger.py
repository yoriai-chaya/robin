import sys
from pathlib import Path

from loguru import logger

from app.config import get_settings

# ---------------------------------------
# Resolve project root, Setup Environment
# ---------------------------------------
project_root = Path(__file__).resolve().parent
settings = get_settings()
logger.remove()

# -------------
# Custom Format
# -------------
message_format = "\
<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> \
<level>{level: <8}</level> \
<cyan>{file.name}</cyan>\
<cyan>:{line} </cyan>\
- <level>{message}</level>\
"

# -------------
# Custom Levels
# -------------
logger.level("AGENT", no=7, color="<magenta><bold>")
logger.level("TOOL", no=15, color="<magenta>")
level = settings.log_level.upper()

# -------------------------------
# Log Output Destination (stderr)
# -------------------------------
logger.add(sys.stderr, format=message_format, level=level)

# --------------------------------
# Log Output Destination (logfile)
# --------------------------------
log_dir = project_root / settings.log_dir
log_dir.mkdir(parents=True, exist_ok=True)
filename = settings.log_filename
logfile_path = log_dir / filename
logger.add(logfile_path, format=message_format, rotation="5MB", level=level)
