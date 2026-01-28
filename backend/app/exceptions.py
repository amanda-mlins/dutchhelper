"""Custom exception classes"""
from fastapi import HTTPException

class ValidationError(HTTPException):
    """Raised when validation fails"""
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)

class NotFoundError(HTTPException):
    """Raised when resource is not found"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)

class ProcessingError(HTTPException):
    """Raised when text processing fails"""
    def __init__(self, detail: str = "Error processing text"):
        super().__init__(status_code=500, detail=detail)
