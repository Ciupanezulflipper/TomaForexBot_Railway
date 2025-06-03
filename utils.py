import functools
import time
import logging

logger = logging.getLogger(__name__)

def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 2):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Max retries reached for {func.__name__}: {e}")
                        raise
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Attempt {attempt+1} failed in {func.__name__}: {e}. Retrying in {wait_time}s")
                    time.sleep(wait_time)
        return wrapper
    return decorator

# Example usage
@retry_with_backoff(max_retries=5, backoff_factor=3)
def fetch_market_data(symbol):
    # Your risky code here
    pass
