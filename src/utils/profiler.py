import time
import functools
import logging

logger = logging.getLogger(__name__)

def profile_performance(func):
    """Decorator to measure execution time of pipeline steps."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        logger.info(f"⏱️ [PERFORMANCE] '{func.__name__}' executed in {execution_time:.4f} seconds.")
        return result
    return wrapper