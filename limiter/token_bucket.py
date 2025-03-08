
# app/limiter/token_bucket.py
import time
from typing import Dict, Any, Tuple, Optional

from limiter.base import RateLimiter
from storage.base import BaseStorage
from core.config import settings


class TokenBucket(RateLimiter):
    """
    Token Bucket Rate Limiter Implementation.
    
    A token bucket has a capacity (max_tokens) and refills at a constant rate (refill_rate).
    Each request consumes one or more tokens from the bucket.
    If the bucket contains enough tokens, the request is allowed.
    """
    
    def __init__(
        self, 
        storage: BaseStorage,
        max_tokens: int = settings.DEFAULT_TOKENS,
        refill_rate: float = settings.DEFAULT_REFILL_RATE,
        time_window: int = settings.DEFAULT_TIME_WINDOW
    ):
        """
        Initialize a new token bucket.
        
        Args:
            storage: Storage backend for token buckets
            max_tokens: Maximum tokens the bucket can hold
            refill_rate: Rate at which tokens are added to the bucket (tokens per second)
            time_window: Time window for rate limiting in seconds
        """
        self.storage = storage
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.time_window = time_window
    
    async def get_bucket(self, key: str) -> Dict[str, Any]:
        """Get the bucket data for a key or create a new one."""
        bucket = await self.storage.get(key)
        
        now = time.time()
        
        if not bucket:
            # Create a new bucket with maximum tokens
            bucket = {
                "tokens": self.max_tokens,
                "last_refill": now,
                "max_tokens": self.max_tokens,
                "refill_rate": self.refill_rate,
            }
            await self.storage.set(key, bucket, expire=self.time_window)
            return bucket
            
        # Calculate token refill based on time elapsed
        elapsed = now - bucket["last_refill"]
        new_tokens = elapsed * bucket["refill_rate"]
        
        # Update bucket state
        if new_tokens > 0:
            bucket["tokens"] = min(bucket["max_tokens"], bucket["tokens"] + new_tokens)
            bucket["last_refill"] = now
            await self.storage.update(key, bucket)
            
        return bucket
    
    async def consume(self, key: str, tokens: int = 1) -> Tuple[bool, dict]:
        """
        Consume tokens from the bucket.
        
        Args:
            key: Bucket identifier
            tokens: Number of tokens to consume
            
        Returns:
            Tuple containing:
                - Whether the request is allowed (True if enough tokens, False otherwise)
                - Metadata dict with rate limit information
        """
        bucket = await self.get_bucket(key)
        
        # Check if enough tokens are available
        if bucket["tokens"] >= tokens:
            # Consume tokens
            bucket["tokens"] -= tokens
            await self.storage.update(key, bucket)
            allowed = True
        else:
            allowed = False
        
        # Calculate time until bucket is refilled
        if bucket["tokens"] < bucket["max_tokens"]:
            time_to_refill = (bucket["max_tokens"] - bucket["tokens"]) / bucket["refill_rate"]
        else:
            time_to_refill = 0
        
        # Return metadata for headers
        metadata = {
            "remaining": int(bucket["tokens"]),
            "limit": bucket["max_tokens"],
            "reset": int(time.time() + time_to_refill),
        }
        
        return allowed, metadata
