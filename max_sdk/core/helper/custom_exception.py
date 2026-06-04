class MaxApiError(Exception):

    def __init__(
        self,
        message: str = "",
        code: str = "API_ERROR",
        status_code: int = 500,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

    def __str__(self):
        return f"{self.code} ({self.status_code}): {self.message}"

    def to_dict(self) -> dict:
        return {
            "error": self.code,
            "message": self.message,
            "status_code": self.status_code,
        }
