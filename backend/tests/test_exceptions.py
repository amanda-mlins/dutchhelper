"""
Unit tests for custom exceptions.
"""

import pytest
from fastapi import HTTPException
from app.exceptions import ValidationError, ProcessingError


class TestCustomExceptions:
    """Test suite for custom exception classes"""

    def test_validation_error_creation(self):
        """Test that ValidationError can be created and raised"""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Test validation error")
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Test validation error"

    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from HTTPException"""
        error = ValidationError("Test")
        assert isinstance(error, HTTPException)
        assert isinstance(error, Exception)

    def test_processing_error_creation(self):
        """Test that ProcessingError can be created and raised"""
        with pytest.raises(ProcessingError) as exc_info:
            raise ProcessingError("Test processing error")
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Test processing error"

    def test_processing_error_inheritance(self):
        """Test that ProcessingError inherits from HTTPException"""
        error = ProcessingError("Test")
        assert isinstance(error, HTTPException)
        assert isinstance(error, Exception)

    def test_validation_error_with_empty_message(self):
        """Test ValidationError with empty message"""
        error = ValidationError("")
        assert error.status_code == 400
        assert error.detail == ""

    def test_processing_error_with_special_characters(self):
        """Test ProcessingError with special characters in message"""
        message = "Error: special chars!@#$%^&*()"
        error = ProcessingError(message)
        assert error.status_code == 500
        assert error.detail == message

    def test_processing_error_default_message(self):
        """Test ProcessingError with default message"""
        error = ProcessingError()
        assert error.status_code == 500
        assert error.detail == "Error processing text"

    def test_validation_error_status_code(self):
        """Test that ValidationError uses 400 status code"""
        error = ValidationError("Bad input")
        assert error.status_code == 400

    def test_processing_error_status_code(self):
        """Test that ProcessingError uses 500 status code"""
        error = ProcessingError("Server error")
        assert error.status_code == 500
