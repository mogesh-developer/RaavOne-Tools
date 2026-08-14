"""Central manager for registering and executing tools."""

from typing import Any, Dict, List, Set
from pydantic import ValidationError as PydanticValidationError

from raavone_tools.base import BaseProvider, BaseTool
from raavone_tools.exceptions import ExecutionError, ToolNotFoundError, ValidationError


class ToolManager:
    """Manages tool registration, input validation, execution, and provider lifecycle."""

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}
        self._providers: Set[BaseProvider] = set()

    def register_tool(self, tool: BaseTool) -> None:
        """Register a new tool and its associated provider (if any)."""
        self._tools[tool.name] = tool
        if tool.provider:
            self._providers.add(tool.provider)

    def get_tool(self, name: str) -> BaseTool:
        """Retrieve a registered tool by its name."""
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' is not registered.")
        return self._tools[name]

    def list_tools(self) -> List[BaseTool]:
        """Return a list of all registered tools."""
        return list(self._tools.values())

    async def initialize_providers(self) -> None:
        """Initialize all registered providers."""
        for provider in self._providers:
            await provider.initialize()

    async def close_providers(self) -> None:
        """Close all registered providers."""
        for provider in self._providers:
            await provider.close()

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Validate input arguments and execute the specified tool."""
        tool = self.get_tool(tool_name)
        
        try:
            # Pydantic v2 validation
            validated_args = tool.input_schema(**arguments)
        except PydanticValidationError as e:
            raise ValidationError(f"Validation failed for tool '{tool_name}': {e}") from e

        try:
            # model_dump() is standard for Pydantic v2
            return await tool.execute(**validated_args.model_dump())
        except Exception as e:
            raise ExecutionError(f"Error during execution of tool '{tool_name}': {e}") from e
