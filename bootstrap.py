# bootstrap.py (streamlined & modernized)

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

BASE_DIR = Path("data")
IDEAS_DIR = BASE_DIR / "ideas"

FILES: dict[Path, Any] = {
    BASE_DIR / "memory.json": {"log": []},
    BASE_DIR / "long_term_memory.json": {"log": []},
    BASE_DIR / "weekly_review_log.txt": "",
    IDEAS_DIR / "seeds.json": {"ideas": []},
}


def create_folder(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Ensured folder exists: {path}")
    except OSError as e:
        logger.error(f"❌ Failed to create folder {path}: {e}")


def create_file(file_path: Path, content: Any) -> None:
    if not file_path.exists():
        try:
            with file_path.open("w", encoding="utf-8") as f:
                if isinstance(content, dict):
                    json.dump(content, f, indent=2)
                else:
                    f.write(content)
            logger.info(f"📄 Created file: {file_path}")
        except OSError as e:
            logger.error(f"❌ Failed to create file {file_path}: {e}")
    else:
        logger.debug(f"File already exists: {file_path}")


def bootstrap() -> None:
    logger.info("🌱 Bootstrapping Sage...")
    create_folder(BASE_DIR)
    create_folder(IDEAS_DIR)
    for file_path, content in FILES.items():
        create_file(file_path, content)
    logger.info("✅ Sage is ready.")


def needs_bootstrap() -> bool:
    exists = (BASE_DIR / "memory.json").exists()
    logger.info(f"Memory file exists: {exists}")
    return not exists
