"""Custom exceptions for the RaavOne Tools framework."""

class RaavOneToolsError(Exception):
    """Base exception for all RaavOne Tools errors."""
    pass


class ToolError(RaavOneToolsError):
    """Exception raised for tool-related issues."""
    pass


class ToolNotFoundError(ToolError):
    """Exception raised when a requested tool is not registered."""
    pass


class ValidationError(ToolError):
    """Exception raised when tool input validation fails."""
    pass


class ExecutionError(ToolError):
    """Exception raised during tool execution."""
    pass


class ProviderError(RaavOneToolsError):
    """Exception raised when a tool provider encounters an error."""
    pass


class SecurityValidationError(RaavOneToolsError):
    """Exception raised when security boundaries (e.g. sandbox escapes) are violated."""
    pass
