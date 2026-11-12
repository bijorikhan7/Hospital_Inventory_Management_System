from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, APIException


def _first_message(detail) -> str:
    if isinstance(detail, list) and detail:
        return _first_message(detail[0])
    if isinstance(detail, dict) and detail:
        key = next(iter(detail))
        prefix = "" if key in {"non_field_errors", "detail"} else f"{key}: "
        return prefix + _first_message(detail[key])
    return str(detail)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    message = "Request failed."
    if isinstance(exc, ValidationError):
        message = _first_message(exc.detail)
    elif isinstance(exc, APIException):
        message = _first_message(exc.detail)
    elif isinstance(response.data, dict) and "detail" in response.data:
        message = str(response.data["detail"])

    response.data = {"success": False, "message": message}
    return response
