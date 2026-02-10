"""
Pytest configuration and fixtures for backend tests.
"""

import sys
import os

# Add the backend directory to the path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

import pytest


@pytest.fixture(scope="session")
def setup_test_env():
    """Setup test environment"""
    # This could load test environment variables, etc.
    yield
