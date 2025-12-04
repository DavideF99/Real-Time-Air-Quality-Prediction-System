"""
Air Quality Data Collector Module

This module handles fetching air quality data from the OpenWeatherMap API.

Features:
- Fetches current air pollution data for configured cities
- Automatic retry on failures
- Rate limiting to stay within API quotas
- Response validation
- Data persistence to CSV files

Learning Notes:
- API calls can fail (network issues, API limits, etc.)
- Always implement retry logic and error handling
- Validate API responses before using the data
- Log all operations for debugging
"""

import time
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from src.utils.config import get_config
from src.utils.logger import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class APIError(Exception):
    """Custom exception for API-related errors."""
    pass


class AirQualityCollector:
    """
    Collector for air quality data from OpenWeatherMap API.
    
    This class handles:
    - API authentication
    - Data fetching with retry logic
    - Response parsing and validation
    - Data persistence
    
    Usage:
        collector = AirQualityCollector()
        data = collector.fetch_city_data('bangkok')
        collector.save_to_csv(data, 'bangkok')
    """
    
    def __init__(self):
        """Initialize the collector with configuration."""
        self.config = get_config()
        self.api_key = self.config.get_api_key()
        self.base_url = self.config.get_api_base_url()
        self.collection_settings = self.config.get_collection_settings()
        
        # API call tracking for rate limiting
        self.api_calls_today = 0
        self.max_calls_per_day = 1000  # Free tier limit
        
        logger.info("AirQualityCollector initialized")
    
    def fetch_city_data(self, city_key: str) -> Dict[str, Any]:
        """
        Fetch current air quality data for a specific city.
        
        Args:
            city_key: City identifier (e.g., 'bangkok', 'new_york')
            
        Returns:
            Dictionary with air quality data
            
        Raises:
            APIError: If API call fails after all retries
            
        Learning Note: This method implements the full fetch-retry-validate cycle
        """
        # Get city configuration
        city_config = self.config.get_city(city_key)
        if not city_config:
            raise ValueError(f"City '{city_key}' not found in configuration")
        
        logger.info(f"Fetching air quality data for {city_config['name']}")
        
        # Build API request URL
        url = f"{self.base_url}/air_pollution"
        params = {
            'lat': city_config['latitude'],
            'lon': city_config['longitude'],
            'appid': self.api_key
        }
        
        # Attempt to fetch data with retries
        max_retries = self.collection_settings.get('retry_attempts', 3)
        retry_delay = self.collection_settings.get('retry_delay_seconds', 5)
        timeout = self.collection_settings.get('timeout_seconds', 10)
        
        for attempt in range(max_retries):
            try:
                # Check rate limit
                if self.api_calls_today >= self.max_calls_per_day:
                    raise APIError(f"Daily API call limit ({self.max_calls_per_day}) reached")
                
                # Make API request
                logger.debug(f"API call attempt {attempt + 1}/{max_retries}")
                response = requests.get(url, params=params, timeout=timeout)
                
                # Increment call counter
                self.api_calls_today += 1
                
                # Check response status
                response.raise_for_status()
                
                # Parse JSON response
                data = response.json()
                
                # Validate response structure
                if not self._validate_response(data):
                    raise APIError("Invalid API response structure")
                
                # Add metadata
                data['city_key'] = city_key
                data['city_name'] = city_config['name']
                data['country'] = city_config['country']
                data['fetch_timestamp'] = datetime.now().isoformat()
                
                logger.info(f"Successfully fetched data for {city_config['name']}")
                return data
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise APIError(f"Failed to fetch data after {max_retries} attempts (timeout)")
            
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise APIError(f"Failed to fetch data after {max_retries} attempts: {e}")
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise APIError(f"Unexpected error during API call: {e}")
    
    def _validate_response(self, data: Dict[str, Any]) -> bool:
        """
        Validate API response structure.
        
        Args:
            data: API response dictionary
            
        Returns:
            True if response is valid, False otherwise
            
        Learning Note: Always validate external data before using it!
        """
        try:
            # Check required fields
            if 'list' not in data:
                logger.error("Response missing 'list' field")
                return False
            
            if not data['list']:
                logger.error("Response 'list' is empty")
                return False
            
            # Check first entry has required components
            first_entry = data['list'][0]
            if 'main' not in first_entry:
                logger.error("Response missing 'main' field")
                return False
            
            if 'components' not in first_entry:
                logger.error("Response missing 'components' field")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def parse_api_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse raw API response into structured format.
        
        Args:
            raw_data: Raw API response
            
        Returns:
            Parsed data dictionary with clean structure
            
        Learning Note: This transforms nested JSON into flat structure for easier analysis
        """
        try:
            # Extract the first (most recent) reading
            reading = raw_data['list'][0]
            
            # Build structured data
            parsed = {
                # Metadata
                'timestamp': datetime.fromtimestamp(reading['dt']).isoformat(),
                'city_key': raw_data.get('city_key', 'unknown'),
                'city_name': raw_data.get('city_name', 'Unknown'),
                'country': raw_data.get('country', 'Unknown'),
                'fetch_timestamp': raw_data.get('fetch_timestamp'),
                
                # Air Quality Index (1-5 scale)
                'aqi': reading['main']['aqi'],
                
                # Pollutant concentrations (μg/m³)
                'co': reading['components'].get('co', None),  # Carbon monoxide
                'no': reading['components'].get('no', None),  # Nitrogen monoxide
                'no2': reading['components'].get('no2', None),  # Nitrogen dioxide
                'o3': reading['components'].get('o3', None),  # Ozone
                'so2': reading['components'].get('so2', None),  # Sulfur dioxide
                'pm2_5': reading['components'].get('pm2_5', None),  # Fine particles
                'pm10': reading['components'].get('pm10', None),  # Coarse particles
                'nh3': reading['components'].get('nh3', None),  # Ammonia
            }
            
            return parsed
            
        except KeyError as e:
            logger.error(f"Missing key in API response: {e}")
            raise APIError(f"Failed to parse API response: missing key {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}")
            raise APIError(f"Failed to parse API response: {e}")
    
    def fetch_all_cities(self) -> List[Dict[str, Any]]:
        """
        Fetch air quality data for all configured cities.
        
        Returns:
            List of data dictionaries, one per city
            
        Learning Note: This is the main method you'll call regularly
        """
        cities = self.config.get_cities()
        all_data = []
        
        logger.info(f"Fetching data for {len(cities)} cities")
        
        for city_key in cities.keys():
            try:
                # Fetch raw data
                raw_data = self.fetch_city_data(city_key)
                
                # Parse into clean format
                parsed_data = self.parse_api_response(raw_data)
                
                all_data.append(parsed_data)
                
                # Small delay between requests to be respectful to API
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to fetch data for {city_key}: {e}")
                # Continue with other cities even if one fails
                continue
        
        logger.info(f"Successfully fetched data for {len(all_data)}/{len(cities)} cities")
        return all_data
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> Path:
        """
        Save collected data to CSV file.
        
        Args:
            data: List of data dictionaries
            filename: Custom filename (auto-generated if None)
            
        Returns:
            Path to saved file
            
        Learning Note: CSV is simple and widely compatible for storing structured data
        """
        if not data:
            logger.warning("No data to save")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"aqi_data_{timestamp}.csv"
        
        # Ensure .csv extension
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # Get save path
        raw_data_dir = self.config.get_raw_data_dir()
        filepath = raw_data_dir / filename
        
        # Save to CSV
        df.to_csv(filepath, index=False)
        
        logger.info(f"Saved {len(df)} records to {filepath}")
        logger.info(f"File size: {filepath.stat().st_size / 1024:.2f} KB")
        
        return filepath
    
    def get_api_call_stats(self) -> Dict[str, int]:
        """
        Get API usage statistics.
        
        Returns:
            Dictionary with usage info
        """
        remaining = self.max_calls_per_day - self.api_calls_today
        return {
            'calls_made_today': self.api_calls_today,
            'max_calls_per_day': self.max_calls_per_day,
            'remaining_calls': remaining,
            'usage_percentage': (self.api_calls_today / self.max_calls_per_day) * 100
        }


if __name__ == "__main__":
    """
    Test the data collector.
    
    This script:
    1. Fetches data for all configured cities
    2. Saves to CSV
    3. Displays summary statistics
    
    Run: python src/data/collectors.py
    """
    
    print("\n" + "=" * 70)
    print("AIR QUALITY DATA COLLECTOR TEST")
    print("=" * 70 + "\n")
    
    try:
        # Initialize collector
        collector = AirQualityCollector()
        print("✅ Collector initialized\n")
        
        # Fetch data for all cities
        print("📡 Fetching data from OpenWeatherMap API...\n")
        all_data = collector.fetch_all_cities()
        
        if not all_data:
            print("❌ No data collected!")
            exit(1)
        
        print(f"\n✅ Successfully collected data for {len(all_data)} cities\n")
        
        # Display summary
        print("-" * 70)
        print("DATA SUMMARY")
        print("-" * 70)
        
        for data in all_data:
            aqi_category = {
                1: "Good",
                2: "Fair", 
                3: "Moderate",
                4: "Poor",
                5: "Very Poor"
            }.get(data['aqi'], "Unknown")
            
            print(f"\n🌍 {data['city_name']}, {data['country']}")
            print(f"   AQI: {data['aqi']} ({aqi_category})")
            print(f"   PM2.5: {data['pm2_5']:.2f} μg/m³")
            print(f"   PM10: {data['pm10']:.2f} μg/m³")
            print(f"   NO2: {data['no2']:.2f} μg/m³")
            print(f"   O3: {data['o3']:.2f} μg/m³")
            print(f"   Timestamp: {data['timestamp']}")
        
        # Save to CSV
        print("\n" + "-" * 70)
        print("SAVING DATA")
        print("-" * 70 + "\n")
        
        filepath = collector.save_to_csv(all_data)
        print(f"✅ Data saved to: {filepath}")
        
        # Show API usage
        stats = collector.get_api_call_stats()
        print("\n" + "-" * 70)
        print("API USAGE STATISTICS")
        print("-" * 70)
        print(f"Calls made today: {stats['calls_made_today']}/{stats['max_calls_per_day']}")
        print(f"Remaining calls: {stats['remaining_calls']}")
        print(f"Usage: {stats['usage_percentage']:.1f}%")
        
        print("\n" + "=" * 70)
        print("DATA COLLECTION TEST PASSED! 🎉")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ DATA COLLECTION TEST FAILED")
        print("=" * 70)
        print(f"\nError: {e}\n")
        logger.exception("Test failed with exception")
        exit(1)