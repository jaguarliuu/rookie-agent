"""Type definitions for HTTP module."""

from typing import Any, Dict, Optional, Union
from enum import Enum


class HTTPMethod(str, Enum):
    """HTTP request methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


# Type aliases for better readability
Headers = Dict[str, str]
QueryParams = Dict[str, Union[str, int, float, bool]]
JSONData = Dict[str, Any]
Timeout = Union[float, None]
