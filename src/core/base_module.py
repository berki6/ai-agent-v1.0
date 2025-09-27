from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ModuleConfig(BaseModel):
    """Base configuration for all modules"""

    name: str
    enabled: bool = True
    priority: int = 0


class ModuleResult(BaseModel):
    """Standardized result format for module execution"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseModule(ABC):
    """Abstract base class for all CodeForge AI modules"""

    def __init__(self, config: ModuleConfig):
        self.config = config
        self.name = config.name

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> ModuleResult:
        """Execute the module's main functionality"""
        pass

    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data before execution"""
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get module information"""
        return {
            "name": self.name,
            "enabled": self.config.enabled,
            "priority": self.config.priority,
            "description": self.get_description(),
        }

    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable description of the module"""
        pass

    async def initialize(self) -> bool:
        """Optional initialization method"""
        return True

    async def cleanup(self) -> bool:
        """Optional cleanup method"""
        return True
