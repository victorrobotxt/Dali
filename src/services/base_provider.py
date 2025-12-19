from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseRegistryProvider(ABC):
    @abstractmethod
    def fetch_details(self, address: str) -> Optional[Dict[str, Any]]:
        """Fetch official property data from a government registry."""
        pass

class BaseGeoProvider(ABC):
    @abstractmethod
    def geocode(self, address: str) -> Dict[str, Any]:
        """Convert address to GPS coordinates."""
        pass
