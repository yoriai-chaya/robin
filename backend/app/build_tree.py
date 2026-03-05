from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import HTTPException

from app.base import AutoRunFilelist, DirectoryNode, FileNode, TreeNode
from app.logger import logger

MAX_DIR_DEPTH = 3


def isoformat_from_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def build_tree(current_dir: Path, current_depth: int) -> List[TreeNode]:
    logger.debug(
        f"build_tree called. current_dir: {current_dir}, current_depth: {current_depth}"
    )
    if current_depth > MAX_DIR_DEPTH:
        raise HTTPException(
            status_code=422,
            detail=f"Directory depth exceeds the maximum allowed level: {MAX_DIR_DEPTH}",
        )
    nodes: List[TreeNode] = []

    entries = sorted(current_dir.iterdir(), key=lambda p: p.name)

    for entry in entries:
        if entry.is_dir():
            children = build_tree(entry, current_depth + 1)
            nodes.append(
                DirectoryNode(type="directory", name=entry.name, children=children)
            )
        elif entry.is_file() and entry.suffix == ".md":
            try:
                content = entry.read_text(encoding="utf-8")
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to read file: {entry.name}, e:{e}"
                ) from e

            nodes.append(
                FileNode(
                    type="file",
                    name=entry.name,
                    data=AutoRunFilelist(
                        name=entry.name,
                        content=content,
                        mtime=isoformat_from_mtime(entry),
                    ),
                )
            )

    logger.debug(f"return. nodes: {nodes}")
    return nodes
