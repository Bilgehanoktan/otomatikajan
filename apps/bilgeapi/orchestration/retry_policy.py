import os
import logging
from typing import Dict, Any

logger = logging.getLogger("bilgeapi.orchestration.retry_policy")

class RetryPolicy:
    def __init__(self):
        # Configuration with env fallbacks
        try:
            self.base_delay = float(os.getenv("BILGEAPI_RETRY_BASE_DELAY", "5.0"))
        except ValueError:
            self.base_delay = 5.0

        try:
            self.factor = float(os.getenv("BILGEAPI_RETRY_FACTOR", "2.0"))
        except ValueError:
            self.factor = 2.0

        try:
            self.max_delay = float(os.getenv("BILGEAPI_RETRY_MAX_DELAY", "3600.0"))
        except ValueError:
            self.max_delay = 3600.0

    def should_retry(self, task: Dict[str, Any]) -> bool:
        """
        Determines if a task should be retried based on attempt counts.
        """
        attempt_count = task.get("attempt_count", 0)
        max_attempts = task.get("max_attempts", 3)
        return attempt_count < max_attempts

    def get_backoff_delay(self, attempt_count: int) -> float:
        """
        Calculates exponential backoff delay with a cap.
        For attempt_count = 1: base_delay
        For attempt_count = 2: base_delay * factor, etc.
        """
        if attempt_count <= 0:
            return 0.0
        
        delay = self.base_delay * (self.factor ** (attempt_count - 1))
        return min(delay, self.max_delay)
