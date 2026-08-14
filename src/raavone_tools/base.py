"""Base classes and interfaces for RaavOne Tools."""

from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, Type, TypeVar
from pydantic import BaseModel


class BaseProvider(ABC):
    """Abstract base class for resource and system providers."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider, opening connections or acquiring system resources."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the provider, cleaning up open connections and resources."""
        pass


TProvider = TypeVar("TProvider", bound=BaseProvider)


class BaseTool(ABC, Generic[TProvider]):
    """Abstract base class for all tools."""

    name: str
    description: str
    input_schema: Type[BaseModel]

    def __init__(self, provider: Optional[TProvider] = None) -> None:
        """Initialize the tool with an optional resource provider."""
        self.provider = provider

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with keyword arguments corresponding to input_schema."""
        pass
