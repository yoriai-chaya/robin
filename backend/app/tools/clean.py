from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import shutil
from datetime import datetime
from typing import Any, Dict

from app.config import get_settings
from app.logger import logger


def resolve_path() -> Dict[str, Path]:
    # base_dir
    base_dir = Path.cwd()

    # output_path
    settings = get_settings()
    output_dir = settings.output_dir
    output_path = base_dir / output_dir

    # app_path
    app_path = output_path / "app"

    # tests_path
    tests_path = output_path / "tests"

    # public_path
    public_path = output_path / "public"

    # results_path
    results_dir = settings.test_results_dir
    results_path = base_dir / output_dir / results_dir

    # sample_path
    sample_path = base_dir.parent / "sample"

    # backup_path
    backup_path = base_dir / "backup"

    # input_images_path
    input_images_path = base_dir / "input" / "images"

    paths = {
        "output_path": output_path,
        "app_path": app_path,
        "tests_path": tests_path,
        "public_path": public_path,
        "results_path": results_path,
        "sample_path": sample_path,
        "backup_path": backup_path,
        "input_images_path": input_images_path,
    }
    return paths


def precheck_required_files(paths: Dict[str, Any]) -> None:
    # --- check directories ---
    # (a) check output/app
    app_path = paths["app_path"]
    if not app_path.is_dir():
        raise RuntimeError(f"{app_path} not found.")

    # (b) check output/tests
    tests_path = paths["tests_path"]
    if not tests_path.is_dir():
        raise RuntimeError(f"{tests_path} not found.")

    # (c) check output/public
    public_path = paths["public_path"]
    if not public_path.is_dir():
        raise RuntimeError(f"{public_path} not found.")

    # (d) check backup directory
    backup_path: Path = paths["backup_path"]
    backup_path.mkdir(exist_ok=True)

    # --- check files ---
    # (a) check output/tests/base.spec.ts
    base_spec_file = paths["tests_path"] / "base.spec.ts"
    if not base_spec_file.is_file():
        raise RuntimeError(f"{base_spec_file} not found.")
    # (b) check output/tests/screenshot.ts
    screenshot_file = paths["tests_path"] / "screenshot.ts"
    if not screenshot_file.is_file():
        raise RuntimeError(f"{screenshot_file} not found.")
    # (c) check input/images/hotel.png
    hotel_image_file = paths["input_images_path"] / "hotel.png"
    if not hotel_image_file.is_file():
        raise RuntimeError(f"{hotel_image_file} not found.")


def backup_targets(paths: Dict[str, Path]) -> None:
    backup_root = paths["backup_path"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / timestamp
    logger.info(f"Backup directory: {backup_dir}")

    for key in ["app_path", "tests_path", "results_path"]:
        src = paths[key]

        if not src.is_dir():
            continue
        dst = backup_dir / src.name
        shutil.copytree(src, dst, copy_function=shutil.copy2)


def restore_app_page(paths: Dict[str, Path]) -> None:
    # copy sample/org/app/page.tsx -> output/app/page.tsx
    sample_path = paths["sample_path"]
    sample_page = sample_path / "org" / "app" / "page.tsx"
    if not sample_page.is_file():
        raise RuntimeError(f"{sample_page} not found.")

    app_path = paths["app_path"]
    app_page = app_path / "page.tsx"
    logger.log("TOOL", f"Initial page.tsx Copy: {sample_page} -> {app_page}")
    shutil.copy2(sample_page, app_page)

    # copy sample/org/app/layout.tsx -> output/app/layout.tsx
    sample_layout = sample_path / "org" / "app" / "layout.tsx"
    if not sample_layout.is_file():
        raise RuntimeError(f"{sample_layout} not found.")

    app_layout = app_path / "layout.tsx"
    logger.log("TOOL", f"Initial layout.tsx Copy: {sample_layout} -> {app_layout}")
    shutil.copy2(sample_layout, app_layout)


def clean_dot_next(paths: Dict[str, Path]) -> None:
    logger.log("TOOL", "Clean Next.js cache (.next)")

    output_path = paths["output_path"]
    dot_next_dir = output_path / ".next"

    if not dot_next_dir.is_dir():
        return
    shutil.rmtree(dot_next_dir)


def clean_app_booking(paths: Dict[str, Path]) -> None:
    logger.log("TOOL", "Clean output/app/booking/*")
    booking_dir = paths["app_path"] / "booking"
    if booking_dir.is_dir():
        shutil.rmtree(booking_dir)


def clean_components(paths: Dict[str, Path]) -> None:
    logger.log("TOOL", "Clean output/app/components")
    compo_path = paths["app_path"] / "components"
    if compo_path.is_dir():
        shutil.rmtree(compo_path)


def clean_public_hotel(paths: Dict[str, Path]) -> None:
    logger.log("TOOL", "Clean output/public/hotel.png")
    public_path = paths["public_path"]
    hotel_path = public_path / "hotel.png"
    if hotel_path.is_file():
        hotel_path.unlink()


def clean_tests(paths: Dict[str, Path]) -> None:
    logger.log("TOOL", "Clean output/tests/*.spec.ts")
    tests_dir = paths["tests_path"]

    spec_files = list(tests_dir.glob("*.spec.ts"))
    for spec in spec_files:
        if spec.name == "base.spec.ts":
            continue
        else:
            spec.unlink()
    return


def clean_results(paths: Dict[str, Path]) -> None:
    logger.log("TOOL", "Clean output/results/*.json, screenshot")
    results_dir = paths["results_path"]

    # remove output/results/*.json
    json_files = list(results_dir.glob("*.json"))
    for json_file in json_files:
        json_file.unlink()

    # remove output/results/screenshot/*.png
    screenshot_dir = paths["results_path"] / "screenshot"
    if screenshot_dir.is_dir():
        shutil.rmtree(screenshot_dir)


def main() -> int:
    logger.info("Cleaning output and setup start")
    paths = resolve_path()

    try:
        # precheck
        error_message = "precheck_required_files"
        precheck_required_files(paths=paths)

        # backup
        error_message = "backup_targets"
        backup_targets(paths=paths)

        # restore page
        error_message = "restore_app_page"
        restore_app_page(paths=paths)

        # clean .next
        error_message = "clean_dot_next"
        clean_dot_next(paths=paths)

        # clean output/app/booking/*
        error_message = "clean_app_booking"
        clean_app_booking(paths=paths)

        # clean output/app/components/*.tsx
        error_message = "clean_components"
        clean_components(paths=paths)

        # clean output/public/hotel.png
        error_message = "clean_public_hotel"
        clean_public_hotel(paths=paths)

        # clean output/tests/*.spec.ts
        error_message = "clean_tests"
        clean_tests(paths=paths)

        # clean output/results/*.json, output/results/screenshot/*.png
        error_message = "clean_results"
        clean_results(paths=paths)

    except Exception as e:
        logger.error(f"{error_message}: {e}")
        return 1

    logger.info("Cleaning output and setup end")
    return 0


if __name__ == "__main__":
    sys.exit(main())
