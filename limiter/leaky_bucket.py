# app/limiter/leaky_bucket.py
import time
from typing import Dict, Any, Tuple

from limiter.base import RateLimiter
from storage.base import BaseStorage
from core.config import settings


class LeakyBucket(RateLimiter):
    """
    Leaky Bucket Rate Limiter Implementation.
    
    The leaky bucket algorithm models a bucket with a constant outflow rate.
    Requests are added to the bucket, and if the bucket would overflow, the request is denied.
    """
    
    def __init__(
        self, 
        storage: BaseStorage,
        capacity: int = settings.DEFAULT_TOKENS,
        leak_rate: float = settings.DEFAULT_REFILL_RATE,
        time_window: int = settings.DEFAULT_TIME_WINDOW
    ):
        """
        Initialize a new leaky bucket.
        
        Args:
            storage: Storage backend for buckets
            capacity: Maximum capacity of the bucket
            leak_rate: Rate at which the bucket leaks (requests per second)
            time_window: Time window for rate limiting in seconds
        """
        self.storage = storage
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.time_window = time_window
    
    async def get_bucket(self, key: str) -> Dict[str, Any]:
        """Get the bucket data for a key or create a new one."""
        bucket = await self.storage.get(key)
        
        now = time.time()
        
        if not bucket:
            # Create a new empty bucket
            bucket = {
                "water_level": 0,
                "last_leak": now,
                "capacity": self.capacity,
                "leak_rate": self.leak_rate,
            }
            await self.storage.set(key, bucket, expire=self.time_window)
            return bucket
            
        # Calculate leakage based on time elapsed
        elapsed = now - bucket["last_leak"]
        leakage = elapsed * bucket["leak_rate"]
        
        # Update bucket state
        if leakage > 0:
            bucket["water_level"] = max(0, bucket["water_level"] - leakage)
            bucket["last_leak"] = now
            await self.storage.update(key, bucket)
            
        return bucket
    
    async def consume(self, key: str, tokens: int = 1) -> Tuple[bool, dict]:
        """
        Try to add tokens to the bucket.
        
        Args:
            key: Bucket identifier
            tokens: Number of tokens to add to the bucket
            
        Returns:
            Tuple containing:
                - Whether the request is allowed (True if bucket doesn't overflow, False otherwise)
                - Metadata dict with rate limit information
        """
        bucket = await self.get_bucket(key)
        
        # Check if adding tokens would overflow the bucket
        if bucket["water_level"] + tokens <= bucket["capacity"]:
            # Add tokens to bucket
            bucket["water_level"] += tokens
            await self.storage.update(key, bucket)
            allowed = True
        else:
            allowed = False
        
        # Calculate time until bucket has space
        if bucket["water_level"] > 0:
            time_to_empty = bucket["water_level"] / bucket["leak_rate"]
        else:
            time_to_empty = 0
        
        # Return metadata for headers
        metadata = {
            "remaining": int(bucket["capacity"] - bucket["water_level"]),
            "limit": bucket["capacity"],
            "reset": int(time.time() + time_to_empty),
        }
        
        return allowed, metadata
