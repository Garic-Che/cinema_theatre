# src/utils/retry.py
"""
Retry utilities for handling transient failures in external API calls.
"""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Optional, Type, Union

import httpx

from core.config import settings


logger = logging.getLogger(__name__)


def with_retry(
    max_attempts: Optional[int] = None,
    delay: Optional[float] = None,
    backoff_factor: float = 2.0,
    exceptions: tuple = (httpx.RequestError, httpx.HTTPStatusError),
    retry_on_status: tuple = (500, 502, 503, 504, 429),
):
    """
    Decorator to add retry logic to async functions.
    
    Args:
        max_attempts: Maximum number of retry attempts (uses config default if None)
        delay: Initial delay between retries in seconds (uses config default if None)
        backoff_factor: Factor to multiply delay by after each failed attempt
        exceptions: Tuple of exception types to retry on
        retry_on_status: HTTP status codes that should trigger a retry
    
    Returns:
        Decorated function with retry logic
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            attempts = max_attempts or settings.API_RETRY_ATTEMPTS
            initial_delay = delay or settings.API_RETRY_DELAY
            current_delay = initial_delay
            
            last_exception = None
            
            for attempt in range(attempts):
                try:
                    result = await func(*args, **kwargs)
                    
                    # If the result is an httpx.Response, check status code
                    if hasattr(result, 'status_code') and result.status_code in retry_on_status:
                        if attempt < attempts - 1:
                            logger.warning(
                                f"HTTP {result.status_code} from {func.__name__}, "
                                f"retrying in {current_delay}s (attempt {attempt + 1}/{attempts})"
                            )
                            await asyncio.sleep(current_delay)
                            current_delay *= backoff_factor
                            continue
                        else:
                            logger.error(
                                f"HTTP {result.status_code} from {func.__name__}, "
                                f"max retries ({attempts}) exceeded"
                            )
                            return result
                    
                    # Success case
                    if attempt > 0:
                        logger.info(f"{func.__name__} succeeded on attempt {attempt + 1}")
                    
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < attempts - 1:
                        logger.warning(
                            f"Exception in {func.__name__}: {str(e)}, "
                            f"retrying in {current_delay}s (attempt {attempt + 1}/{attempts})"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"Exception in {func.__name__}: {str(e)}, "
                            f"max retries ({attempts}) exceeded"
                        )
                        raise e
                        
                except Exception as e:
                    # For non-retryable exceptions, raise immediately
                    logger.error(f"Non-retryable exception in {func.__name__}: {str(e)}")
                    raise e
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


class ExponentialBackoff:
    """
    Helper class for implementing exponential backoff with jitter.
    """
    
    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.current_delay = initial_delay
    
    def reset(self) -> None:
        """Reset the delay to the initial value."""
        self.current_delay = self.initial_delay
    
    def get_delay(self) -> float:
        """Get the current delay value."""
        delay = min(self.current_delay, self.max_delay)
        
        if self.jitter:
            # Add jitter to avoid thundering herd problem
            import random
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay
    
    def next_delay(self) -> float:
        """Get the current delay and increment for next time."""
        delay = self.get_delay()
        self.current_delay *= self.backoff_factor
        return delay