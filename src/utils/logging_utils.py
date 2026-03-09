from __future__ import annotations

from pathlib import Path
from typing import Callable
import logging


class InMemoryLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(self.format(record))


def configure_run_logging(log_path: Path, level: str = "INFO") -> tuple[logging.Logger, InMemoryLogHandler, Callable[[], None]]:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    root_logger = logging.getLogger()
    root_logger.setLevel(min(root_logger.level or numeric_level, numeric_level))

    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)

    memory_handler = InMemoryLogHandler()
    memory_handler.setLevel(numeric_level)
    memory_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(memory_handler)

    logger = logging.getLogger("plastdrift_app")
    logger.setLevel(numeric_level)

    def cleanup() -> None:
        for handler in (file_handler, memory_handler):
            root_logger.removeHandler(handler)
            handler.close()

    return logger, memory_handler, cleanup
