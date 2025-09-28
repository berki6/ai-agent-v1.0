import logging
from .config import settings


def get_logger(name=None):
    """
    Returns a logger with the specified name, configured for the project.
    Honors LOG_LEVEL from settings and initializes Sentry if SENTRY_DSN is set.
    """

    # Configure root logger
    log_level = getattr(settings, "LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=numeric_level,
        filename=getattr(
            settings,
            "LOG_FILE",
            numeric_level >= logging.WARNING and "log/error.log" or "log/flask_app.log",
        ),
        filemode="w",
        encoding="utf-8",
    )

    # Optional Sentry integration
    try:
        if getattr(settings, "SENTRY_DSN", ""):
            import sentry_sdk

            sentry_sdk.init(dsn=settings.SENTRY_DSN)
    except Exception:
        # Do not fail startup if sentry isn't installed or fails to init
        pass

    return logging.getLogger(name)


# --- Timing Decorators ---
import functools
import time


def log_timing(logger=None):
    """
    Decorator to log execution time of sync and async functions.
    """
    import asyncio

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            result = await func(*args, **kwargs)
            elapsed = time.time() - start
            log = logger or get_logger(func.__module__)
            log.info(f"[TIMING] {func.__name__} took {elapsed:.2f}s")
            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            log = logger or get_logger(func.__module__)
            log.info(f"[TIMING] {func.__name__} took {elapsed:.2f}s")
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
