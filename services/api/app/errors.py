import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

error_logger = logging.getLogger("math_coach.error")


class AppError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def error_body(*, code: str, message: str, request_id: str | None) -> dict[str, Any]:
    error: dict[str, str] = {"code": code, "message": message}
    if request_id is not None:
        error["requestId"] = request_id
    return {"error": error}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        error_logger.exception(
            "unhandled request error",
            exc_info=error,
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=500,
            headers={"X-Request-ID": request_id} if request_id is not None else None,
            content=error_body(
                code="internal_error",
                message="Something went wrong. Try again.",
                request_id=request_id,
            ),
        )

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, error: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content=error_body(
                code=error.code,
                message=error.message,
                request_id=getattr(request.state, "request_id", None),
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(
        request: Request, _error: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_body(
                code="invalid_request",
                message="Check the submitted values and try again.",
                request_id=getattr(request.state, "request_id", None),
            ),
        )
