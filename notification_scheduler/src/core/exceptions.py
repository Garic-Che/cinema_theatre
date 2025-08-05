# src/core/exceptions.py

class ExternalAPIError(Exception):
    """
    Исключение для ошибок при работе с внешними API.
    """
    def __init__(
        self,
        message: str,
        service_name: str,
        status_code: int = 500,
        details: dict | None = None,
    ):
        self.message = message
        self.service_name = service_name
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def __str__(self):
        return (
            f"[{self.service_name}] ExternalAPIError {self.status_code}: {self.message} "
            f"Details: {self.details}"
        )
