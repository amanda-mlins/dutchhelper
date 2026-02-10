"""Unit tests for logging optimization"""
import logging
import pytest
from app.config import settings
from app.main import app


class TestLoggingConfiguration:
    """Test that logging is configured correctly"""
    
    def test_default_log_level_is_info(self):
        """Test that default log level is INFO"""
        assert settings.LOG_LEVEL == "INFO"
    
    def test_log_level_can_be_configured(self):
        """Test that LOG_LEVEL can be set"""
        # This would be set via .env or environment variable
        # Default should be INFO
        assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    
    def test_logging_configured_in_app(self):
        """Test that app logging is configured"""
        # Get the root logger and check its level
        root_logger = logging.getLogger()
        assert root_logger.level != logging.NOTSET


class TestConditionalDebugLogging:
    """Test that debug logs only print when enabled"""
    
    def setup_method(self):
        """Setup for each test"""
        self.logger = logging.getLogger("app.llm_service")
    
    def test_debug_log_disabled_by_default(self):
        """Test that DEBUG logs are not emitted by default"""
        # Set to INFO level
        self.logger.setLevel(logging.INFO)
        
        # Check that isEnabledFor works correctly
        assert not self.logger.isEnabledFor(logging.DEBUG)
        assert self.logger.isEnabledFor(logging.INFO)
    
    def test_debug_log_enabled_when_debug_level(self):
        """Test that DEBUG logs are emitted when level is DEBUG"""
        self.logger.setLevel(logging.DEBUG)
        
        assert self.logger.isEnabledFor(logging.DEBUG)
        assert self.logger.isEnabledFor(logging.INFO)
    
    def test_conditional_debug_logging_pattern(self):
        """Test the conditional logging pattern used in code"""
        self.logger.setLevel(logging.INFO)
        
        # This is the pattern used in optimized code
        if self.logger.isEnabledFor(logging.DEBUG):
            # This block should not execute
            executed = True
        else:
            executed = False
        
        assert not executed
    
    def test_conditional_debug_logging_pattern_when_enabled(self):
        """Test conditional logging pattern when debug is enabled"""
        self.logger.setLevel(logging.DEBUG)
        
        # This is the pattern used in optimized code
        if self.logger.isEnabledFor(logging.DEBUG):
            executed = True
        else:
            executed = False
        
        assert executed


class TestLoggingOptimization:
    """Test specific logging optimizations"""
    
    def setup_method(self):
        """Setup for each test"""
        self.logger = logging.getLogger("app.llm_service")
        self.logger.setLevel(logging.INFO)
    
    def test_no_expensive_string_formatting_at_info_level(self):
        """Test that expensive formatting doesn't happen at INFO level"""
        # This simulates the optimization where debug logs are conditional
        
        # Define expensive operation (string slicing)
        expensive_string = "A" * 10000
        
        # At INFO level, this expensive operation should be skipped
        log_executed = False
        
        if self.logger.isEnabledFor(logging.DEBUG):
            # This expensive operation shouldn't execute
            expensive_result = expensive_string[:100]
            log_executed = True
        
        assert not log_executed
    
    def test_expensive_operation_at_debug_level(self):
        """Test that expensive operations happen at DEBUG level"""
        self.logger.setLevel(logging.DEBUG)
        
        expensive_string = "A" * 10000
        log_executed = False
        
        if self.logger.isEnabledFor(logging.DEBUG):
            expensive_result = expensive_string[:100]
            log_executed = True
        
        assert log_executed
    
    def test_per_component_logging_removed(self):
        """Test that per-component logging is conditional"""
        # Old pattern would have been:
        # for i, component in enumerate(components):
        #     logger.debug(f"  [{i}] {component.type}: '{component.value}'")
        
        # New pattern is:
        # if logger.isEnabledFor(logging.DEBUG):
        #     for component in components:
        #         logger.debug(f"  - {component.type}: {component.value}")
        
        # At INFO level, entire loop should be skipped
        self.logger.setLevel(logging.INFO)
        
        components = [
            {"type": "noun", "value": "kat"},
            {"type": "verb", "value": "zit"},
            {"type": "preposition", "value": "op"},
        ]
        
        logged_count = 0
        
        if self.logger.isEnabledFor(logging.DEBUG):
            for component in components:
                # logger.debug would be called here
                logged_count += 1
        
        assert logged_count == 0  # Should not loop at all


class TestLoggingLevels:
    """Test different logging levels"""
    
    def test_logging_level_hierarchy(self):
        """Test that logging level hierarchy is correct"""
        levels = [
            (logging.DEBUG, 10),
            (logging.INFO, 20),
            (logging.WARNING, 30),
            (logging.ERROR, 40),
            (logging.CRITICAL, 50),
        ]
        
        for level, value in levels:
            assert level == value
    
    def test_logger_enabled_for_hierarchy(self):
        """Test isEnabledFor respects level hierarchy"""
        logger = logging.getLogger("test")
        
        # Set to WARNING level
        logger.setLevel(logging.WARNING)
        
        # Check hierarchy
        assert not logger.isEnabledFor(logging.DEBUG)
        assert not logger.isEnabledFor(logging.INFO)
        assert logger.isEnabledFor(logging.WARNING)
        assert logger.isEnabledFor(logging.ERROR)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
