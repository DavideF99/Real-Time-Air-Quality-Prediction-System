"""
API Data Models (Pydantic Schemas)

Defines request/response structures for the API.

Learning Notes:
- Pydantic provides automatic validation
- Type hints ensure data correctness
- Generates OpenAPI documentation automatically
- Easy serialization to JSON
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class CityEnum(str, Enum):
    """Available cities for prediction."""
    BANGKOK = "bangkok"
    DURBAN = "durban"
    SAO_PAULO = "sao_paulo"
    SYDNEY = "sydney"
    LONDON = "london"
    NEW_YORK = "new_york"


class AQICategoryEnum(str, Enum):
    """AQI health categories."""
    GOOD = "Good"
    MODERATE = "Moderate"
    UNHEALTHY_SENSITIVE = "Unhealthy for Sensitive Groups"
    UNHEALTHY = "Unhealthy"
    VERY_UNHEALTHY = "Very Unhealthy"
    HAZARDOUS = "Hazardous"


class ModelEnum(str, Enum):
    """Available prediction models."""
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    RANDOM_FOREST = "random_forest"
    LINEAR = "linear_regression"


# ============================================================================
# REQUEST MODELS
# ============================================================================

class PredictionRequest(BaseModel):
    """
    Request for AQI prediction.
    
    Example:
        {
            "city": "bangkok",
            "aqi": 2.5,
            "pm2_5": 25.0,
            "pm10": 45.0,
            "no2": 15.0,
            "o3": 85.0,
            "co": 250.0,
            "so2": 5.0,
            "nh3": 2.0,
            "model": "xgboost"
        }
    """
    
    # Required fields
    city: CityEnum = Field(..., description="City for prediction")
    
    # Current pollutant values
    aqi: float = Field(..., ge=1.0, le=5.0, description="Current AQI (1-5)")
    pm2_5: float = Field(..., ge=0.0, le=500.0, description="PM2.5 (μg/m³)")
    pm10: float = Field(..., ge=0.0, le=600.0, description="PM10 (μg/m³)")
    no2: float = Field(..., ge=0.0, le=400.0, description="NO2 (μg/m³)")
    o3: float = Field(..., ge=0.0, le=500.0, description="O3 (μg/m³)")
    co: Optional[float] = Field(250.0, ge=0.0, le=30000.0, description="CO (μg/m³)")
    so2: Optional[float] = Field(5.0, ge=0.0, le=1000.0, description="SO2 (μg/m³)")
    nh3: Optional[float] = Field(2.0, ge=0.0, le=200.0, description="NH3 (μg/m³)")
    
    # Optional model selection
    model: Optional[ModelEnum] = Field(
        ModelEnum.XGBOOST, 
        description="Model to use for prediction"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "city": "bangkok",
                "aqi": 2.5,
                "pm2_5": 25.0,
                "pm10": 45.0,
                "no2": 15.0,
                "o3": 85.0,
                "co": 250.0,
                "so2": 5.0,
                "nh3": 2.0,
                "model": "xgboost"
            }
        }


class BatchPredictionRequest(BaseModel):
    """
    Request for multiple predictions.
    
    Example:
        {
            "requests": [
                {"city": "bangkok", "aqi": 2.5, ...},
                {"city": "london", "aqi": 1.8, ...}
            ]
        }
    """
    requests: List[PredictionRequest] = Field(
        ..., 
        min_length=1, 
        max_length=10,
        description="List of prediction requests (max 10)"
    )


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class PredictionResponse(BaseModel):
    """
    Response with AQI prediction.
    
    Example:
        {
            "city": "bangkok",
            "current_aqi": 2.5,
            "predicted_aqi": 2.8,
            "predicted_category": "Moderate",
            "confidence_interval": {
                "lower": 2.3,
                "upper": 3.3
            },
            "health_message": "Air quality is acceptable...",
            "model_used": "xgboost",
            "timestamp": "2025-11-05T10:30:00"
        }
    """
    
    city: str = Field(..., description="City name")
    current_aqi: float = Field(..., description="Current AQI")
    predicted_aqi: float = Field(..., description="Predicted AQI (24h ahead)")
    predicted_category: AQICategoryEnum = Field(..., description="AQI category")
    
    confidence_interval: Dict[str, float] = Field(
        ..., 
        description="Prediction confidence interval"
    )
    
    health_message: str = Field(..., description="Health recommendation")
    model_used: str = Field(..., description="Model used for prediction")
    timestamp: datetime = Field(..., description="Prediction timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "city": "Bangkok",
                "current_aqi": 2.5,
                "predicted_aqi": 2.8,
                "predicted_category": "Moderate",
                "confidence_interval": {
                    "lower": 2.3,
                    "upper": 3.3
                },
                "health_message": "Air quality is acceptable for most people.",
                "model_used": "xgboost",
                "timestamp": "2025-11-05T10:30:00"
            }
        }


class BatchPredictionResponse(BaseModel):
    """Response with multiple predictions."""
    predictions: List[PredictionResponse]
    total_predictions: int
    timestamp: datetime


class HealthResponse(BaseModel):
    """API health check response."""
    status: str = Field(..., description="API status")
    version: str = Field(..., description="API version")
    models_loaded: List[str] = Field(..., description="Available models")
    timestamp: datetime = Field(..., description="Current server time")


class ModelInfoResponse(BaseModel):
    """Information about a specific model."""
    model_name: str
    model_type: str
    training_date: Optional[str]
    performance_metrics: Dict[str, float]
    features_used: int
    description: str


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error description")
    detail: Optional[str] = Field(None, description="Additional details")
    timestamp: datetime = Field(..., description="Error timestamp")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_aqi_category(aqi: float) -> AQICategoryEnum:
    """
    Convert AQI value to health category.
    
    Args:
        aqi: AQI value (1-5 scale)
    
    Returns:
        AQI category enum
    """
    if aqi <= 1.5:
        return AQICategoryEnum.GOOD
    elif aqi <= 2.5:
        return AQICategoryEnum.MODERATE
    elif aqi <= 3.5:
        return AQICategoryEnum.UNHEALTHY_SENSITIVE
    elif aqi <= 4.5:
        return AQICategoryEnum.UNHEALTHY
    elif aqi <= 5.0:
        return AQICategoryEnum.VERY_UNHEALTHY
    else:
        return AQICategoryEnum.HAZARDOUS


def get_health_message(aqi: float) -> str:
    """
    Get health recommendation based on AQI.
    
    Args:
        aqi: AQI value (1-5 scale)
    
    Returns:
        Health message string
    """
    if aqi <= 1.5:
        return "Air quality is good. Perfect for outdoor activities!"
    elif aqi <= 2.5:
        return "Air quality is acceptable for most people. Sensitive individuals should consider limiting prolonged outdoor exertion."
    elif aqi <= 3.5:
        return "Members of sensitive groups may experience health effects. The general public is less likely to be affected."
    elif aqi <= 4.5:
        return "Everyone may begin to experience health effects. Sensitive groups may experience more serious effects. Reduce prolonged outdoor activities."
    elif aqi <= 5.0:
        return "Health alert: everyone may experience more serious health effects. Avoid outdoor activities."
    else:
        return "Health warning: emergency conditions. Everyone should avoid all outdoor exertion."


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test Pydantic models."""
    
    print("=" * 80)
    print("PYDANTIC MODELS TEST")
    print("=" * 80)
    
    # Test PredictionRequest
    print("\n1. Testing PredictionRequest:")
    request = PredictionRequest(
        city=CityEnum.BANGKOK,
        aqi=2.5,
        pm2_5=25.0,
        pm10=45.0,
        no2=15.0,
        o3=85.0
    )
    print(f"✓ Created request for {request.city}")
    print(f"  AQI: {request.aqi}")
    print(f"  Model: {request.model}")
    
    # Test validation
    print("\n2. Testing Validation:")
    try:
        bad_request = PredictionRequest(
            city=CityEnum.BANGKOK,
            aqi=10.0,  # Invalid (> 5)
            pm2_5=25.0,
            pm10=45.0,
            no2=15.0,
            o3=85.0
        )
    except Exception as e:
        print(f"✓ Validation caught error: {type(e).__name__}")
    
    # Test PredictionResponse
    print("\n3. Testing PredictionResponse:")
    response = PredictionResponse(
        city="Bangkok",
        current_aqi=2.5,
        predicted_aqi=2.8,
        predicted_category=get_aqi_category(2.8),
        confidence_interval={"lower": 2.3, "upper": 3.3},
        health_message=get_health_message(2.8),
        model_used="xgboost",
        timestamp=datetime.now()
    )
    print(f"✓ Created response")
    print(f"  Prediction: {response.predicted_aqi:.2f}")
    print(f"  Category: {response.predicted_category}")
    print(f"  Message: {response.health_message}")
    
    # Test JSON serialization
    print("\n4. Testing JSON Serialization:")
    json_data = response.model_dump_json(indent=2)
    print("✓ JSON output:")
    print(json_data[:200] + "...")
    
    print("\n" + "=" * 80)
    print("✓ All Pydantic models working correctly!")
    print("=" * 80)