# app/limiter/base.py
from abc import ABC, abstractmethod
from typing import Tuple

class RateLimiter(ABC):
    """Base abstract class for rate limiter implementations."""
    
    @abstractmethod
    async def consume(self, key: str, tokens: int = 1) -> Tuple[bool, dict]:
        """
        Consume tokens from the bucket for the given key.
        
        Args:
            key: Identifier for the bucket (e.g., user_id, IP address)
            tokens: Number of tokens to consume
            
        Returns:
            Tuple[bool, dict]: 
                - Boolean indicating if the request is allowed
                - Dictionary with metadata (remaining tokens, reset time, etc.)
        """
        pass
