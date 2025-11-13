# The MIT License (MIT).
#
# Copyright (c) 2025 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

"""Tests for FastAPI mock datetime middleware."""

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

import pytest
import time_machine
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.testclient import TestClient

from fastapi_mock_datetime.middleware import mock_datetime_middleware


@pytest.fixture
def app() -> FastAPI:
    """Fastapi app for test."""
    app = FastAPI()

    @app.middleware("http")
    async def mock_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        return await mock_datetime_middleware(request, call_next)

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {"current_time": datetime.now(timezone.utc).isoformat()}

    @app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        """Test endpoint."""
        return {"message": "test"}

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Test client."""
    return TestClient(app)


def test_without_mock_header(client: TestClient) -> None:
    """Test request without X-Mock-Date header returns current time."""
    response = client.get("/")

    assert response.status_code == 200
    assert "current_time" in response.json()
    assert (
        abs((datetime.now(timezone.utc) - datetime.fromisoformat(response.json()["current_time"])).total_seconds()) < 1
    )


def test_with_valid_mock_header_utc(client: TestClient) -> None:
    """Test request with valid UTC X-Mock-Date header returns mocked time."""
    mock_time = "2023-10-05T12:00:00+00:00"

    response = client.get("/", headers={"X-Mock-Date": mock_time})

    assert response.status_code == 200
    assert response.json()["current_time"] == mock_time


def test_with_valid_mock_header_naive(client: TestClient) -> None:
    """Test request with naive datetime header converts to UTC."""
    mock_time_naive = "2023-10-05T12:00:00"
    expected_time_utc = "2023-10-05T12:00:00+00:00"

    response = client.get("/", headers={"X-Mock-Date": mock_time_naive})

    assert response.status_code == 200
    assert response.json()["current_time"] == expected_time_utc


def test_with_invalid_mock_header(client: TestClient) -> None:
    """Test request with invalid X-Mock-Date header returns 422 error."""
    invalid_time = "invalid-date-format"

    response = client.get("/", headers={"X-Mock-Date": invalid_time})

    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "input": "invalid-date-format",
                "loc": [
                    "header",
                    "x-mock-date",
                ],
                "msg": "Invalid datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS[±HH:MM]",
                "type": "value_error",
            },
        ],
    }


def test_mock_time_affects_only_current_request(client: TestClient) -> None:
    """Test that time mocking is isolated to individual requests."""
    mock_time = "2023-10-05T12:00:00+00:00"
    response1 = client.get("/", headers={"X-Mock-Date": mock_time})
    assert response1.json()["current_time"] == mock_time

    response2 = client.get("/")
    current_time = datetime.fromisoformat(response2.json()["current_time"])
    assert abs((datetime.now(timezone.utc) - current_time).total_seconds()) < 1


def test_different_endpoints_with_mock_time(client: TestClient) -> None:
    """Test that time mocking works across different endpoints."""
    mock_time = "2023-10-05T12:00:00+00:00"

    response1 = client.get("/", headers={"X-Mock-Date": mock_time})
    assert response1.json()["current_time"] == mock_time

    response2 = client.get("/test", headers={"X-Mock-Date": mock_time})
    assert response2.json()["message"] == "test"


def test_time_travel_isolation() -> None:
    """Test that time_machine travel context properly isolates time mocking."""
    original_time_before = datetime.now(timezone.utc)

    mock_time = datetime(2023, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    with time_machine.travel(mock_time, tick=False):
        mocked_time = datetime.now(timezone.utc)
        assert mocked_time == mock_time

    original_time_after = datetime.now(timezone.utc)
    time_diff = (original_time_after - original_time_before).total_seconds()
    assert time_diff < 1
