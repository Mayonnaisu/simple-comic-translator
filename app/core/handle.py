import sys
from loguru import logger
import traceback

def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    """
    Handler for unhandled exceptions that will log the error with Loguru.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # If it's a KeyboardInterrupt (Ctrl+C), call the default hook so the program exits normally
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Log the unhandled exception as an error with full traceback to all sinks
    logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical("Uncaught exception occured!")

    # Optional: You can also use traceback.format_exception to get a formatted string
    # full_traceback = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    # logger.critical(f"An unhandled exception occurred:\n{full_traceback}")