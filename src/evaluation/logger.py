"""Logging utilities for evaluation runs."""

import logging
from datetime import datetime
from pathlib import Path


class EvaluationLogger:
    """Logger for evaluation runs with file output and optional console printing."""

    def __init__(self, log_dir: str, pipeline_name: str):
        """
        Initialize evaluation logger.

        Args:
            log_dir: Directory to save log files
            pipeline_name: Name of the evaluation pipeline
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"{pipeline_name}_{timestamp}.log"

        # Setup logger
        self.logger = logging.getLogger(f"evaluation_{pipeline_name}_{timestamp}")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()

        # File handler
        file_handler = logging.FileHandler(self.log_file, mode="w")
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def log(self, message: str, also_print: bool = False) -> None:
        """
        Log message to file, optionally print to console.

        Args:
            message: Message to log
            also_print: If True, also print to console
        """
        self.logger.info(message)
        if also_print:
            print(message)

    def print_and_log(self, message: str) -> None:
        """
        Print to console and log to file.

        Args:
            message: Message to print and log
        """
        self.log(message, also_print=True)

    def get_log_path(self) -> str:
        """Get the path to the log file."""
        return str(self.log_file)
