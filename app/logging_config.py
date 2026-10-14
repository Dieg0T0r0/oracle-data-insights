import logging
from pathlib import Path


def configure_logging():
    """Configure application logging to a local file."""
    log_directory = Path(__file__).resolve().parent.parent / "logs"
    log_directory.mkdir(exist_ok=True)

    logging.basicConfig(
        filename=log_directory / "app.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )

    return logging.getLogger("oracle_data_insights")
