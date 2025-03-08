# app/storage/redis_store.py
import json
from typing import Dict, Any, Optional
import redis.asyncio as redis

from core.config import settings
from storage.base import BaseStorage

class RedisStorage(BaseStorage):
    """Redis implementation of storage backend."""
    
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def set(self, key: str, data: Dict[str, Any], expire: Optional[int] = None) -> None:
        serialized = json.dumps(data)
        if expire:
            await self.redis.setex(key, expire, serialized)
        else:
            await self.redis.set(key, serialized)
    
    async def update(self, key: str, data: Dict[str, Any]) -> None:
        # For Redis, set and update are the same operation
        await self.set(key, data)
