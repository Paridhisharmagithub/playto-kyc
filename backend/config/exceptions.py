from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return Response(
            {"error": {"code": "SERVER_ERROR", "message": "Something went wrong."}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    detail = response.data
    message = ""
    error_code = "BAD_REQUEST" if response.status_code < 500 else "SERVER_ERROR"

    if isinstance(detail, dict):
        if "message" in detail:
            message = str(detail["message"])
        elif "detail" in detail:
            message = str(detail["detail"])
        if "code" in detail:
            error_code = str(detail["code"])
    else:
        message = str(detail)

    if not message and isinstance(detail, dict):
        first_value = next(iter(detail.values()), "Validation error.")
        if isinstance(first_value, list) and first_value:
            message = str(first_value[0])
        else:
            message = str(first_value)

    response.data = {
        "error": {
            "code": error_code,
            "message": str(message or "Request failed."),
            "details": detail,
        }
    }
    return response
