import time
from typing import Dict, List, Tuple
from src.config import settings

class SlidingWindowRateLimiter:
    """Sliding-window in-memory rate limiter per user/client."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.window_seconds = 60.0
        self._history: Dict[str, List[float]] = {}

    def is_rate_limited(self, client_key: str) -> Tuple[bool, int]:
        """
        Check if client_key has exceeded allowed requests.
        Returns: (is_limited, remaining_requests)
        """
        now = time.time()
        cutoff = now - self.window_seconds
        
        if client_key not in self._history:
            self._history[client_key] = [now]
            return False, self.rpm - 1
            
        # Clean older requests outside the window
        valid_requests = [t for t in self._history[client_key] if t > cutoff]
        
        if len(valid_requests) >= self.rpm:
            self._history[client_key] = valid_requests
            return True, 0
            
        valid_requests.append(now)
        self._history[client_key] = valid_requests
        remaining = self.rpm - len(valid_requests)
        return False, remaining

    def reset_for_key(self, client_key: str):
        if client_key in self._history:
            del self._history[client_key]

rate_limiter = SlidingWindowRateLimiter(requests_per_minute=settings.RATE_LIMIT_REQUESTS_PER_MINUTE)
