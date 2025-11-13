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

"""FastAPI middleware for mocking datetime in requests."""

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

import time_machine
from fastapi import Request
from fastapi.responses import JSONResponse, Response


async def mock_datetime_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """FastAPI middleware for mocking the current datetime in request processing.

    This middleware allows you to override the current datetime for individual requests
    by providing an 'X-Mock-Date' header with an ISO 8601 formatted datetime string.
    Useful for testing time-dependent functionality without modifying system clock.

    Args:
        request: The incoming FastAPI request object.
        call_next: The next middleware or route handler in the chain.

    Returns:
        Response: The response from the next handler, or a 422 error if date format is invalid.

    Example:
        >>> # Mock time to a specific UTC datetime
        >>> headers = {"X-Mock-Date": "2023-10-05T12:00:00+00:00"}
        >>> response = client.get("/api/endpoint", headers=headers)

    """
    mock_time_header = request.headers.get("X-Mock-Date")
    if not mock_time_header:
        return await call_next(request)
    try:
        mock_time = datetime.fromisoformat(mock_time_header)
        if mock_time.tzinfo is None:
            mock_time = mock_time.replace(tzinfo=timezone.utc)
        with time_machine.travel(mock_time, tick=False):
            return await call_next(request)
    except ValueError:
        return JSONResponse(
            status_code=422,
            content={
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["header", "x-mock-date"],
                        "msg": "Invalid datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS[±HH:MM]",
                        "input": mock_time_header,
                    },
                ],
            },
        )
