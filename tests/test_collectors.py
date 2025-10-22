"""
Unit Tests for Data Collectors Module

Learning Notes:
- Tests ensure your code works correctly
- Run tests before committing code
- Tests serve as documentation of expected behavior
"""

import pytest
import pandas as pd
from pathlib import Path

from src.data.collectors import AirQualityCollector
from src.utils.config import get_config


class TestAirQualityCollector:
    """Test suite for AirQualityCollector class."""
    
    @pytest.fixture
    def collector(self):
        """Fixture to create collector instance for each test."""
        return AirQualityCollector()
    
    def test_initialization(self, collector):
        """Test that collector initializes correctly."""
        assert collector is not None
        assert collector.api_key is not None
        assert len(collector.api_key) > 0
        assert collector.base_url is not None
    
    def test_fetch_city_data_bangkok(self, collector):
        """Test fetching data for Bangkok."""
        # This makes a real API call
        data = collector.fetch_city_data('bangkok')
        
        assert data is not None
        assert 'city_key' in data
        assert data['city_key'] == 'bangkok'
        assert 'list' in data
        assert len(data['list']) > 0
    
    def test_parse_api_response(self, collector):
        """Test parsing API response."""
        # First fetch real data
        raw_data = collector.fetch_city_data('bangkok')
        
        # Parse it
        parsed = collector.parse_api_response(raw_data)
        
        # Check required fields
        assert 'timestamp' in parsed
        assert 'city_name' in parsed
        assert 'aqi' in parsed
        assert 'pm2_5' in parsed
        
        # Check data types
        assert isinstance(parsed['aqi'], int)
        assert 1 <= parsed['aqi'] <= 5
    
    def test_fetch_all_cities(self, collector):
        """Test fetching data for all cities."""
        all_data = collector.fetch_all_cities()
        
        assert len(all_data) > 0
        assert len(all_data) <= 6  # We configured 6 cities
        
        # Check each record has required fields
        for data in all_data:
            assert 'city_name' in data
            assert 'aqi' in data
            assert 'pm2_5' in data
    
    def test_save_to_csv(self, collector, tmp_path):
        """Test saving data to CSV."""
        # Fetch some data
        all_data = collector.fetch_all_cities()
        
        # Save to temporary directory
        config = get_config()
        original_dir = config.get_raw_data_dir()
        
        # Use pytest's tmp_path for testing
        test_file = tmp_path / "test_data.csv"
        
        # Convert to DataFrame and save
        df = pd.DataFrame(all_data)
        df.to_csv(test_file, index=False)
        
        # Verify file was created
        assert test_file.exists()
        
        # Verify content
        df_loaded = pd.read_csv(test_file)
        assert len(df_loaded) == len(all_data)
    
    def test_api_call_stats(self, collector):
        """Test API usage statistics."""
        # Make some API calls
        collector.fetch_city_data('bangkok')
        
        stats = collector.get_api_call_stats()
        
        assert 'calls_made_today' in stats
        assert 'remaining_calls' in stats
        assert stats['calls_made_today'] > 0
        assert stats['remaining_calls'] < 1000


if __name__ == "__main__":
    """Run tests from command line."""
    pytest.main([__file__, "-v"])