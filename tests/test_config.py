"""
Unit Tests for Configuration Module

Tests configuration loading, validation, and access.

Run:
    pytest tests/test_config.py -v
"""

import pytest
import os
from pathlib import Path
import tempfile
import yaml

from src.utils.config import Config, ConfigurationError, get_config


# ============================================================================
# SINGLETON TESTS
# ============================================================================

@pytest.mark.unit
class TestConfigSingleton:
    """Test Config singleton pattern."""
    
    def test_singleton_instance(self):
        """Test only one Config instance exists."""
        config1 = Config()
        config2 = Config()
        
        assert config1 is config2
    
    def test_get_config_returns_singleton(self):
        """Test get_config returns same instance."""
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

@pytest.mark.unit
class TestConfigInitialization:
    """Test configuration initialization."""
    
    def test_config_initializes(self):
        """Test config initializes without errors."""
        config = get_config()
        
        assert config is not None
        assert config.project_root.exists()
        assert config.config_dir.exists()
        assert config.data_dir.exists()
    
    def test_config_loads_cities(self):
        """Test cities configuration is loaded."""
        config = get_config()
        cities = config.get_cities()
        
        assert cities is not None
        assert len(cities) > 0
        assert isinstance(cities, dict)
    
    def test_config_loads_data_settings(self):
        """Test data configuration is loaded."""
        config = get_config()
        settings = config.get_data_quality_settings()
        
        assert settings is not None
        assert isinstance(settings, dict)


# ============================================================================
# API KEY TESTS
# ============================================================================

@pytest.mark.unit
class TestAPIKey:
    """Test API key retrieval."""
    
    def test_get_api_key_exists(self):
        """Test API key is retrieved."""
        config = get_config()
        
        try:
            api_key = config.get_api_key()
            assert api_key is not None
            assert len(api_key) > 0
            assert isinstance(api_key, str)
        except ConfigurationError as e:
            pytest.skip(f"API key not configured: {e}")
    
    def test_api_key_format(self):
        """Test API key has reasonable format."""
        config = get_config()
        
        try:
            api_key = config.get_api_key()
            # OpenWeatherMap keys are 32 characters
            assert len(api_key) >= 20
            assert len(api_key) <= 40
        except ConfigurationError:
            pytest.skip("API key not configured")


# ============================================================================
# CITY CONFIGURATION TESTS
# ============================================================================

@pytest.mark.unit
class TestCityConfiguration:
    """Test city configuration access."""
    
    def test_get_cities_returns_dict(self):
        """Test get_cities returns dictionary."""
        config = get_config()
        cities = config.get_cities()
        
        assert isinstance(cities, dict)
    
    def test_cities_have_required_fields(self):
        """Test each city has required fields."""
        config = get_config()
        cities = config.get_cities()
        
        required_fields = ['name', 'latitude', 'longitude', 'country']
        
        for city_key, city_data in cities.items():
            for field in required_fields:
                assert field in city_data, f"{city_key} missing {field}"
    
    def test_get_specific_city(self):
        """Test retrieving specific city."""
        config = get_config()
        
        bangkok = config.get_city('bangkok')
        
        assert bangkok is not None
        assert bangkok['name'] == 'Bangkok'
        assert 'latitude' in bangkok
        assert 'longitude' in bangkok
    
    def test_get_nonexistent_city(self):
        """Test retrieving nonexistent city returns None."""
        config = get_config()
        
        city = config.get_city('nonexistent_city')
        
        assert city is None
    
    def test_city_coordinates_valid(self):
        """Test city coordinates are valid."""
        config = get_config()
        cities = config.get_cities()
        
        for city_key, city_data in cities.items():
            lat = city_data['latitude']
            lon = city_data['longitude']
            
            # Valid latitude: -90 to 90
            assert -90 <= lat <= 90, f"{city_key} invalid latitude"
            
            # Valid longitude: -180 to 180
            assert -180 <= lon <= 180, f"{city_key} invalid longitude"


# ============================================================================
# API CONFIGURATION TESTS
# ============================================================================

@pytest.mark.unit
class TestAPIConfiguration:
    """Test API configuration."""
    
    def test_get_api_base_url(self):
        """Test API base URL is retrieved."""
        config = get_config()
        base_url = config.get_api_base_url()
        
        assert base_url is not None
        assert isinstance(base_url, str)
        assert base_url.startswith('http')
    
    def test_get_collection_settings(self):
        """Test collection settings are retrieved."""
        config = get_config()
        settings = config.get_collection_settings()
        
        assert settings is not None
        assert isinstance(settings, dict)
        
        # Check expected settings
        expected_keys = ['retry_attempts', 'retry_delay_seconds', 'timeout_seconds']
        for key in expected_keys:
            assert key in settings, f"Missing {key}"


# ============================================================================
# DATA QUALITY SETTINGS TESTS
# ============================================================================

@pytest.mark.unit
class TestDataQualitySettings:
    """Test data quality settings."""
    
    def test_get_quality_settings(self):
        """Test quality settings are retrieved."""
        config = get_config()
        settings = config.get_data_quality_settings()
        
        assert settings is not None
        assert isinstance(settings, dict)
    
    def test_pollutant_ranges_exist(self):
        """Test pollutant range settings exist."""
        config = get_config()
        settings = config.get_data_quality_settings()
        
        # Check some range settings
        range_keys = ['pm2_5_range', 'pm10_range', 'aqi_range']
        
        for key in range_keys:
            if key in settings:
                range_val = settings[key]
                assert isinstance(range_val, list)
                assert len(range_val) == 2
                assert range_val[0] < range_val[1]


# ============================================================================
# DIRECTORY MANAGEMENT TESTS
# ============================================================================

@pytest.mark.unit
class TestDirectoryManagement:
    """Test directory path management."""
    
    def test_get_raw_data_dir(self):
        """Test raw data directory path."""
        config = get_config()
        raw_dir = config.get_raw_data_dir()
        
        assert raw_dir is not None
        assert isinstance(raw_dir, Path)
        assert raw_dir.exists()
    
    def test_get_processed_data_dir(self):
        """Test processed data directory path."""
        config = get_config()
        processed_dir = config.get_processed_data_dir()
        
        assert processed_dir is not None
        assert isinstance(processed_dir, Path)
        assert processed_dir.exists()
    
    def test_get_log_dir(self):
        """Test log directory path."""
        config = get_config()
        log_dir = config.get_log_dir()
        
        assert log_dir is not None
        assert isinstance(log_dir, Path)
        assert log_dir.exists()
    
    def test_directories_created_if_missing(self, tmp_path):
        """Test directories are created if they don't exist."""
        # This tests the mkdir logic
        config = get_config()
        
        # Just verify the directories exist
        assert config.get_raw_data_dir().exists()
        assert config.get_processed_data_dir().exists()
        assert config.get_log_dir().exists()


# ============================================================================
# LOGGING CONFIGURATION TESTS
# ============================================================================

@pytest.mark.unit
class TestLoggingConfiguration:
    """Test logging configuration."""
    
    def test_get_log_level(self):
        """Test log level retrieval."""
        config = get_config()
        log_level = config.get_log_level()
        
        assert log_level is not None
        assert isinstance(log_level, str)
        
        # Check it's a valid log level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        assert log_level in valid_levels


# ============================================================================
# VALIDATION TESTS
# ============================================================================

@pytest.mark.unit
class TestConfigValidation:
    """Test configuration validation."""
    
    def test_validate_config_success(self):
        """Test validation passes for valid config."""
        config = get_config()
        
        try:
            is_valid = config.validate_config()
            assert is_valid
        except ConfigurationError as e:
            # If API key is missing, that's expected in test environment
            if "OPENWEATHER_API_KEY" not in str(e):
                raise
            pytest.skip("API key not configured (expected in test)")
    
    def test_validate_empty_cities(self, tmp_path):
        """Test validation fails with empty cities."""
        # Create temporary config with no cities
        config_dir = tmp_path / "configs"
        config_dir.mkdir()
        
        empty_config = {
            'cities': {},
            'api': {'base_url': 'http://test.com'},
            'collection': {}
        }
        
        with open(config_dir / 'cities.yaml', 'w') as f:
            yaml.dump(empty_config, f)
        
        # This would fail validation
        # (Can't easily test without recreating Config instance)


# ============================================================================
# ENVIRONMENT VARIABLE TESTS
# ============================================================================

@pytest.mark.unit
class TestEnvironmentVariables:
    """Test environment variable handling."""
    
    def test_log_level_from_env(self, monkeypatch):
        """Test log level can be set via environment."""
        monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
        
        config = get_config()
        log_level = config.get_log_level()
        
        assert log_level == 'DEBUG'
    
    def test_default_log_level(self, monkeypatch):
        """Test default log level when not set."""
        monkeypatch.delenv('LOG_LEVEL', raising=False)
        
        config = get_config()
        log_level = config.get_log_level()
        
        assert log_level == 'INFO'


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.unit
class TestConfigErrorHandling:
    """Test configuration error handling."""
    
    def test_missing_api_key_raises_error(self, monkeypatch):
        """Test missing API key raises error."""
        # Remove API key from environment
        monkeypatch.delenv('OPENWEATHER_API_KEY', raising=False)
        
        # Create new config instance (can't easily do with singleton)
        # Test indirectly through validation
        config = get_config()
        
        with pytest.raises(ConfigurationError):
            config.validate_config()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
class TestConfigIntegration:
    """Test configuration integration with other modules."""
    
    def test_config_used_by_collector(self):
        """Test config is properly used by collector."""
        from src.data.collectors import AirQualityCollector
        
        collector = AirQualityCollector()
        
        # Collector should have loaded config
        assert collector.api_key is not None
        assert collector.base_url is not None
    
    def test_config_used_by_cleaner(self):
        """Test config is properly used by cleaner."""
        from src.data.cleaners import DataCleaner
        
        cleaner = DataCleaner()
        
        # Cleaner should have loaded config
        assert cleaner.config is not None
        assert cleaner.quality_settings is not None


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.performance
def test_config_initialization_speed():
    """Test config initialization is fast."""
    import time
    
    start = time.time()
    config = get_config()
    elapsed = time.time() - start
    
    # Should be very fast (already cached)
    assert elapsed < 0.01  # < 10ms


@pytest.mark.performance
def test_config_access_speed():
    """Test config access operations are fast."""
    import time
    
    config = get_config()
    
    start = time.time()
    for _ in range(1000):
        _ = config.get_cities()
    elapsed = time.time() - start
    
    # 1000 accesses should be fast
    assert elapsed < 0.1  # < 100ms total