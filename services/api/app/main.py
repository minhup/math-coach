import logging
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from starlette.concurrency import run_in_threadpool

from app.api import router
from app.errors import register_error_handlers
from app.logging_config import configure_logging
from app.storage import get_object_storage

configure_logging()
request_logger = logging.getLogger("math_coach.request")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await run_in_threadpool(get_object_storage().ensure_bucket)
    yield


app = FastAPI(
    title="Math Coach API",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(router)
register_error_handlers(app)


@app.middleware("http")
async def request_context(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = uuid.uuid4().hex
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    request_logger.info(
        "request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "route": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response
