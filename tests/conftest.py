"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    class MockResponse:
        def __init__(self, status_code=200, json_data=None, text=""):
            self.status_code = status_code
            self._json_data = json_data or {}
            self.text = text
            self.content = text.encode()

        def json(self):
            return self._json_data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code} error")

    return MockResponse
