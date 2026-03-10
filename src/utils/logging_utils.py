from __future__ import annotations

from pathlib import Path
from typing import Callable
import logging


def configure_run_logging(log_path: Path, level: str = "INFO") -> tuple[logging.Logger, Callable[[], None]]:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    root_logger = logging.getLogger()
    root_logger.setLevel(min(root_logger.level or numeric_level, numeric_level))

    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)

    logger = logging.getLogger("plastdrift_app")
    logger.setLevel(numeric_level)

    def cleanup() -> None:
        root_logger.removeHandler(file_handler)
        file_handler.close()

    return logger, cleanup
