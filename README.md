# FastAPI Mock DateTime Middleware

Middleware for FastAPI that allows mocking the current time through HTTP headers. Perfect for testing time-dependent functionality.

## Features

- 🕒 Time mocking via HTTP headers
- 🧪 Perfect for testing
- ⚡ Easy integration with FastAPI applications
- 🎯 Timezone support
- 🔒 Date format validation
- 🚀 Async support

## Installation

```bash
pip install fastapi-mock-datetime
```

Or using poetry:

```bash
poetry add fastapi-mock-datetime
```

## Quick Start

```python
from datetime import datetime, UTC
from fastapi import FastAPI
from fastapi_mock_datetime import mock_datetime_middleware

app = FastAPI()

# Add middleware
app.add_middleware(mock_datetime_middleware)

@app.get("/")
async def root():
    return {"current_time": datetime.now(UTC).isoformat()}

@app.get("/time-dependent")
async def time_dependent_endpoint():
    current_time = datetime.now(UTC)
    if current_time.hour < 12:
        return {"message": "Good morning!"}
    else:
        return {"message": "Good afternoon!"}
```

## Usage

### Without Time Mocking

Normal request returns current time:

```bash
curl http://localhost:8000/
# Response: {"current_time":"2023-10-05T10:30:00+00:00"}
```

### With Time Mocking

Use the X-Mock-Date header to set mock time:

```bash
curl -H "X-Mock-Date: 2023-10-05T08:00:00+00:00" http://localhost:8000/
# Response: {"current_time":"2023-10-05T08:00:00+00:00"}
```

```bash
curl -H "X-Mock-Date: 2023-10-05T08:00:00+00:00" http://localhost:8000/time-dependent
# Response: {"message":"Good morning!"}
```

## Supported Date Formats

With timezone: 2023-10-05T08:00:00+00:00

Without timezone: 2023-10-05T08:00:00 (automatically converted to UTC)

## Error Handling

When passing an invalid date format, the middleware returns HTTP 422 error:

```bash
curl -H "X-Mock-Date: invalid-date" http://localhost:8000/
# Response:
# {
#   "detail": [
#     {
#       "type": "value_error",
#       "loc": ["header", "x-mock-date"],
#       "msg": "Invalid datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS[±HH:MM]",
#       "input": "invalid-date"
#     }
#   ]
# }
```

## License

MIT License - see [LICENSE](./LICENSE) file for details.


## Support

If you have any questions or issues, please create an issue in the GitHub repository.
