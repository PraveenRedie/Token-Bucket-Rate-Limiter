# app/storage/memory_store.py
from typing import Dict, Any, Optional
import time
import copy

from storage.base import BaseStorage

class MemoryStorage(BaseStorage):
    """In-memory implementation for testing and development."""
    
    def __init__(self):
        self.storage: Dict[str, Dict[str, Any]] = {}
        self.expiry: Dict[str, float] = {}
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        # Check if key exists and not expired
        if key in self.expiry and time.time() > self.expiry[key]:
            del self.storage[key]
            del self.expiry[key]
            return None
            
        if key in self.storage:
            return copy.deepcopy(self.storage[key])
        return None
    
    async def set(self, key: str, data: Dict[str, Any], expire: Optional[int] = None) -> None:
        self.storage[key] = copy.deepcopy(data)
        if expire:
            self.expiry[key] = time.time() + expire
    
    async def update(self, key: str, data: Dict[str, Any]) -> None:
        if key in self.storage:
            self.storage[key].update(data)
        else:
            self.storage[key] = copy.deepcopy(data)