"""Core interfaces for Rookie Agent.

This module defines the fundamental interfaces that all components
in the Rookie Agent framework should implement.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Generic, Iterator, TypeVar, Any, Dict

# Type variables for generic interfaces
Input = TypeVar("Input")
Output = TypeVar("Output")


class Runnable(ABC, Generic[Input, Output]):
    """Base interface for all executable components.

    This interface defines the contract for components that can process
    input and produce output, both synchronously and asynchronously.

    The Runnable interface is the foundation of the Rookie Agent framework,
    allowing for composable and chainable operations.

    Examples:
        >>> class Echo(Runnable[str, str]):
        ...     def invoke(self, input: str) -> str:
        ...         return input
        ...
        ...     async def ainvoke(self, input: str) -> str:
        ...         return input
        ...
        >>> echo = Echo()
        >>> result = echo.invoke("Hello")
        >>> print(result)
        Hello
    """

    @abstractmethod
    def invoke(self, input: Input, **kwargs: Any) -> Output:
        """Synchronously process input and return output.

        Args:
            input: The input to process
            **kwargs: Additional keyword arguments

        Returns:
            The processed output

        Raises:
            ExecutionError: If execution fails
        """
        pass

    @abstractmethod
    async def ainvoke(self, input: Input, **kwargs: Any) -> Output:
        """Asynchronously process input and return output.

        Args:
            input: The input to process
            **kwargs: Additional keyword arguments

        Returns:
            The processed output

        Raises:
            ExecutionError: If execution fails
        """
        pass


class Streamable(Runnable[Input, Output]):
    """Interface for components that support streaming output.

    This interface extends Runnable to support streaming/chunked output,
    which is essential for real-time responses from LLMs.

    Examples:
        >>> class StreamingEcho(Streamable[str, str]):
        ...     def invoke(self, input: str) -> str:
        ...         return input
        ...
        ...     async def ainvoke(self, input: str) -> str:
        ...         return input
        ...
        ...     def stream(self, input: str) -> Iterator[str]:
        ...         for char in input:
        ...             yield char
        ...
        ...     async def astream(self, input: str) -> AsyncIterator[str]:
        ...         for char in input:
        ...             yield char
    """

    @abstractmethod
    def stream(self, input: Input, **kwargs: Any) -> Iterator[Output]:
        """Synchronously stream output chunks.

        Args:
            input: The input to process
            **kwargs: Additional keyword arguments

        Yields:
            Output chunks

        Raises:
            ExecutionError: If streaming fails
        """
        pass

    @abstractmethod
    async def astream(self, input: Input, **kwargs: Any) -> AsyncIterator[Output]:
        """Asynchronously stream output chunks.

        Args:
            input: The input to process
            **kwargs: Additional keyword arguments

        Yields:
            Output chunks

        Raises:
            ExecutionError: If streaming fails
        """
        pass


class Configurable(ABC):
    """Interface for components that support configuration.

    This interface allows components to be configured with custom settings
    without modifying the component itself (immutable configuration pattern).

    Examples:
        >>> class MyComponent(Configurable):
        ...     def __init__(self, config: dict):
        ...         self.config = config
        ...
        ...     def with_config(self, config: dict) -> 'MyComponent':
        ...         new_config = {**self.config, **config}
        ...         return MyComponent(new_config)
        ...
        >>> component = MyComponent({"timeout": 30})
        >>> new_component = component.with_config({"timeout": 60})
        >>> print(new_component.config["timeout"])
        60
    """

    @abstractmethod
    def with_config(self, config: Dict[str, Any]) -> "Configurable":
        """Create a new instance with updated configuration.

        This method should return a new instance rather than modifying
        the current instance (immutable pattern).

        Args:
            config: Configuration dictionary to merge with existing config

        Returns:
            A new instance with updated configuration
        """
        pass


class Observable(ABC):
    """Interface for components that can be observed.

    This interface allows components to emit events and metrics
    for monitoring and debugging purposes.
    """

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics.

        Returns:
            Dictionary of metric name to value
        """
        pass

    @abstractmethod
    def reset_metrics(self) -> None:
        """Reset all metrics to their initial state."""
        pass
