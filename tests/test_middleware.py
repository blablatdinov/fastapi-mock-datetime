import pytest
from datetime import UTC, datetime
from fastapi import FastAPI, Request
import time_machine
from fastapi.testclient import TestClient
from fastapi_mock_datetime.middleware import mock_datetime_middleware


@pytest.fixture
def app():
    app = FastAPI()

    @app.middleware("http")
    async def mock_middleware(request: Request, call_next):
        return await mock_datetime_middleware(request, call_next)

    @app.get("/")
    async def root():
        return {"current_time": datetime.now(UTC).isoformat()}

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_without_mock_header(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "current_time" in response.json()
    assert (
        abs(
            (
                datetime.now(UTC)
                - datetime.fromisoformat(response.json()["current_time"])
            ).total_seconds()
        )
        < 1
    )


def test_with_valid_mock_header_utc(client):
    mock_time = "2023-10-05T12:00:00+00:00"

    response = client.get("/", headers={"X-Mock-Date": mock_time})

    assert response.status_code == 200
    assert response.json()["current_time"] == mock_time


def test_with_valid_mock_header_naive(client):
    mock_time_naive = "2023-10-05T12:00:00"
    expected_time_utc = "2023-10-05T12:00:00+00:00"

    response = client.get("/", headers={"X-Mock-Date": mock_time_naive})

    assert response.status_code == 200
    assert response.json()["current_time"] == expected_time_utc


def test_with_invalid_mock_header(client):
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
                "msg": "Invalid datetime format. Use ISO format: "
                "YYYY-MM-DDTHH:MM:SS[±HH:MM]",
                "type": "value_error",
            },
        ],
    }


def test_mock_time_affects_only_current_request(client):
    mock_time = "2023-10-05T12:00:00+00:00"
    response1 = client.get("/", headers={"X-Mock-Date": mock_time})
    assert response1.json()["current_time"] == mock_time

    response2 = client.get("/")
    current_time = datetime.fromisoformat(response2.json()["current_time"])
    assert abs((datetime.now(UTC) - current_time).total_seconds()) < 1


def test_different_endpoints_with_mock_time(client):
    mock_time = "2023-10-05T12:00:00+00:00"

    response1 = client.get("/", headers={"X-Mock-Date": mock_time})
    assert response1.json()["current_time"] == mock_time

    response2 = client.get("/test", headers={"X-Mock-Date": mock_time})
    assert response2.json()["message"] == "test"


def test_time_travel_isolation():
    original_time_before = datetime.now(UTC)

    mock_time = datetime(2023, 10, 5, 12, 0, 0, tzinfo=UTC)
    with time_machine.travel(mock_time, tick=False):
        mocked_time = datetime.now(UTC)
        assert mocked_time == mock_time

    original_time_after = datetime.now(UTC)
    time_diff = (original_time_after - original_time_before).total_seconds()
    assert time_diff < 1
