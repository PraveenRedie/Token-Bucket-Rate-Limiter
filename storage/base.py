# app/storage/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseStorage(ABC):
    """Base abstract class for storage implementations."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data for a particular key."""
        pass
    
    @abstractmethod
    async def set(self, key: str, data: Dict[str, Any], expire: Optional[int] = None) -> None:
        """Set data for a key with optional expiration in seconds."""
        pass
    
    @abstractmethod
    async def update(self, key: str, data: Dict[str, Any]) -> None:
        """Update existing data for a key."""
        pass
