"""
Configuration Management Module

This module handles loading and accessing configuration from:
- YAML configuration files (cities.yaml, data_config.yaml)
- Environment variables (.env file)

Learning Notes:
- Singleton pattern: Only one Config instance exists
- Environment variables override YAML settings
- Provides type-safe access to configuration values
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass


class Config:
    """
    Configuration manager using Singleton pattern.
    
    This ensures all parts of the application use the same configuration.
    
    Usage:
        config = Config()
        api_key = config.get_api_key()
        cities = config.get_cities()
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """
        Singleton implementation: Only create one instance.
        
        Learning Note: __new__ is called before __init__
        This pattern ensures we only load config files once.
        """
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration (only runs once due to Singleton)."""
        if not Config._initialized:
            # Load environment variables from .env file
            load_dotenv()
            
            # Set up paths
            self.project_root = Path(__file__).parent.parent.parent
            self.config_dir = self.project_root / "configs"
            self.data_dir = self.project_root / "data"
            
            # Load configuration files
            self._load_configs()
            
            Config._initialized = True
    
    def _load_configs(self):
        """
        Load all YAML configuration files.
        
        Learning Note: We use try-except to handle missing files gracefully.
        """
        try:
            # Load cities configuration
            cities_file = self.config_dir / "cities.yaml"
            with open(cities_file, 'r') as f:
                self.cities_config = yaml.safe_load(f)
            
            # Load data pipeline configuration
            data_config_file = self.config_dir / "data_config.yaml"
            with open(data_config_file, 'r') as f:
                self.data_config = yaml.safe_load(f)
                
        except FileNotFoundError as e:
            raise ConfigurationError(
                f"Configuration file not found: {e.filename}\n"
                f"Please ensure all config files exist in {self.config_dir}"
            )
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing YAML file: {e}")
    
    def get_api_key(self) -> str:
        """
        Get OpenWeatherMap API key from environment variables.
        
        Returns:
            API key string
            
        Raises:
            ConfigurationError: If API key is not set
            
        Learning Note: Never hardcode API keys in your code!
        """
        api_key = os.getenv('OPENWEATHER_API_KEY')
        
        if not api_key:
            raise ConfigurationError(
                "OPENWEATHER_API_KEY not found in environment variables.\n"
                "Please check your .env file."
            )
        
        return api_key
    
    def get_cities(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all configured cities.
        
        Returns:
            Dictionary with city data:
            {
                'bangkok': {
                    'name': 'Bangkok',
                    'latitude': 13.7563,
                    'longitude': 100.5018,
                    ...
                },
                ...
            }
        """
        return self.cities_config.get('cities', {})
    
    def get_city(self, city_key: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific city.
        
        Args:
            city_key: City identifier (e.g., 'bangkok', 'new_york')
            
        Returns:
            City configuration dictionary or None if not found
            
        Example:
            >>> config = Config()
            >>> bangkok = config.get_city('bangkok')
            >>> print(bangkok['latitude'])
            13.7563
        """
        cities = self.get_cities()
        return cities.get(city_key)
    
    def get_api_base_url(self) -> str:
        """Get API base URL."""
        return self.cities_config.get('api', {}).get('base_url', 
                                                      'http://api.openweathermap.org/data/2.5')
    
    def get_collection_settings(self) -> Dict[str, Any]:
        """
        Get data collection settings.
        
        Returns:
            Dictionary with collection parameters:
            {
                'frequency_hours': 1,
                'retry_attempts': 3,
                'retry_delay_seconds': 5,
                'timeout_seconds': 10
            }
        """
        return self.cities_config.get('collection', {})
    
    def get_data_quality_settings(self) -> Dict[str, Any]:
        """Get data quality validation rules."""
        return self.data_config.get('data_quality', {})
    
    def get_raw_data_dir(self) -> Path:
        """Get path to raw data directory."""
        raw_dir = Path(os.getenv('RAW_DATA_DIR', 'data/raw'))
        full_path = self.project_root / raw_dir
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path
    
    def get_processed_data_dir(self) -> Path:
        """Get path to processed data directory."""
        processed_dir = Path(os.getenv('PROCESSED_DATA_DIR', 'data/processed'))
        full_path = self.project_root / processed_dir
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path
    
    def get_log_dir(self) -> Path:
        """Get path to logs directory."""
        log_dir = Path(os.getenv('LOG_DIR', 'data/logs'))
        full_path = self.project_root / log_dir
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path
    
    def get_log_level(self) -> str:
        """Get logging level from environment (default: INFO)."""
        return os.getenv('LOG_LEVEL', 'INFO').upper()
    
    def validate_config(self) -> bool:
        """
        Validate that all required configuration is present.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If configuration is invalid
            
        Learning Note: Always validate configuration at startup!
        """
        errors = []
        
        # Check API key
        try:
            self.get_api_key()
        except ConfigurationError as e:
            errors.append(str(e))
        
        # Check cities
        cities = self.get_cities()
        if not cities:
            errors.append("No cities configured in cities.yaml")
        
        # Validate each city has required fields
        required_fields = ['name', 'latitude', 'longitude', 'country']
        for city_key, city_data in cities.items():
            for field in required_fields:
                if field not in city_data:
                    errors.append(f"City '{city_key}' missing required field: {field}")
        
        if errors:
            raise ConfigurationError(
                "Configuration validation failed:\n" + "\n".join(f"- {e}" for e in errors)
            )
        
        return True


# Convenience function for quick access
def get_config() -> Config:
    """
    Get the global configuration instance.
    
    This is the recommended way to access configuration throughout the app.
    
    Usage:
        from src.utils.config import get_config
        
        config = get_config()
        api_key = config.get_api_key()
    """
    return Config()


if __name__ == "__main__":
    """
    Test the configuration loader.
    
    Run this file directly to verify your configuration:
    python src/utils/config.py
    """
    try:
        config = get_config()
        
        print("=" * 60)
        print("CONFIGURATION VALIDATION")
        print("=" * 60)
        
        # Validate configuration
        config.validate_config()
        print("✅ Configuration is valid!\n")
        
        # Display API key status (masked for security)
        api_key = config.get_api_key()
        print(f"✅ API Key: {api_key[:8]}...{api_key[-4:]} (length: {len(api_key)})\n")
        
        # Display cities
        cities = config.get_cities()
        print(f"✅ Configured Cities: {len(cities)}")
        for city_key, city_data in cities.items():
            print(f"   - {city_data['name']}, {city_data['country']} "
                  f"({city_data['latitude']}, {city_data['longitude']})")
        
        print("\n" + "=" * 60)
        print("CONFIGURATION TEST PASSED! 🎉")
        print("=" * 60)
        
    except ConfigurationError as e:
        print("\n" + "=" * 60)
        print("❌ CONFIGURATION ERROR")
        print("=" * 60)
        print(f"\n{e}\n")
        print("Please fix the issues above and try again.")
        exit(1)