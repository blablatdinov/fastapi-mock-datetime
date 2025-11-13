from datetime import UTC, datetime

import time_machine
from fastapi import Request
from fastapi.responses import JSONResponse


async def mock_datetime_middleware(request: Request, call_next):
    mock_time_header = request.headers.get('X-Mock-Date')
    if not mock_time_header:
        return await call_next(request)
    try:
        mock_time = datetime.fromisoformat(mock_time_header)
        if mock_time.tzinfo is None:
            mock_time = mock_time.replace(tzinfo=UTC)
        with time_machine.travel(mock_time, tick=False):
            return await call_next(request)
    except ValueError:
        return JSONResponse(
            status_code=422,
            content={
                'detail': [
                    {
                        'type': 'value_error',
                        'loc': ['header', 'x-mock-date'],
                        'msg': 'Invalid datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS[±HH:MM]',
                        'input': mock_time_header,
                    }
                ]
            },
        )
