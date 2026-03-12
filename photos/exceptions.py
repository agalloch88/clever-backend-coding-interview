"""Custom exception handler for consistent error envelope responses."""

from typing import Any

from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

EXCEPTION_MAP: dict[type, tuple[str, int]] = {
    exceptions.ValidationError: ("validation_error", status.HTTP_400_BAD_REQUEST),
    exceptions.AuthenticationFailed: ("authentication_failed", status.HTTP_401_UNAUTHORIZED),
    exceptions.NotAuthenticated: ("not_authenticated", status.HTTP_401_UNAUTHORIZED),
    exceptions.PermissionDenied: ("permission_denied", status.HTTP_403_FORBIDDEN),
    exceptions.NotFound: ("not_found", status.HTTP_404_NOT_FOUND),
    exceptions.MethodNotAllowed: ("method_not_allowed", status.HTTP_405_METHOD_NOT_ALLOWED),
}

STATUS_CODE_MAP: dict[int, str] = {
    400: "validation_error",
    401: "authentication_failed",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
}


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    """Wrap all API errors in a consistent {error: {...}} envelope."""
    response = drf_exception_handler(exc, context)

    if response is None:
        return Response(
            {
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred.",
                    "status": 500,
                    "details": {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if type(exc) in EXCEPTION_MAP:
        code, status_code = EXCEPTION_MAP[type(exc)]
    else:
        status_code = response.status_code
        code = STATUS_CODE_MAP.get(status_code, "error")

    if isinstance(exc, exceptions.ValidationError):
        message = "Validation failed."
        details = response.data
    else:
        message = response.data.get("detail", str(exc)) if isinstance(response.data, dict) else str(exc)
        details = {}

    return Response(
        {
            "error": {
                "code": code,
                "message": message,
                "status": status_code,
                "details": details,
            }
        },
        status=status_code,
    )
