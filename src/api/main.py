"""
FastAPI Application - Air Quality Predictor API

Main API application with endpoints for:
- Health check
- Single prediction
- Batch predictions
- Model information

Run with:
    uvicorn src.api.main:app --reload --port 8000

Access docs:
    http://localhost:8000/docs

Learning Notes:
- FastAPI provides automatic OpenAPI docs
- Async endpoints for better performance
- Pydantic models for validation
- CORS enabled for web access
"""

import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.models import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
    ModelInfoResponse,
    ErrorResponse,
    get_aqi_category,
    get_health_message
)
from src.api.predictor import ModelPredictor
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Air Quality Predictor API",
    description="Predict air quality index 24 hours in advance using machine learning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware (allows web apps to access API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize predictor (loads models)
predictor = ModelPredictor()

logger.info("FastAPI application initialized")


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on API startup."""
    logger.info("=" * 80)
    logger.info("AIR QUALITY PREDICTOR API STARTING")
    logger.info("=" * 80)
    logger.info(f"Available models: {predictor.list_models()}")
    logger.info("API documentation: http://localhost:8000/docs")
    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on API shutdown."""
    logger.info("API shutting down...")


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", 
         tags=["General"],
         summary="Root endpoint")
async def root():
    """
    Root endpoint - API information.
    
    Returns basic API info and links to documentation.
    """
    return {
        "message": "Air Quality Predictor API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health_check": "/health",
        "endpoints": {
            "predict": "/predict",
            "batch_predict": "/predict/batch",
            "models": "/models"
        }
    }


@app.get("/health",
         response_model=HealthResponse,
         tags=["General"],
         summary="Health check")
async def health_check():
    """
    Check API health and status.
    
    Returns:
        API status, version, available models
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        models_loaded=predictor.list_models(),
        timestamp=datetime.now()
    )


@app.post("/predict",
          response_model=PredictionResponse,
          tags=["Predictions"],
          summary="Predict AQI",
          responses={
              200: {"description": "Successful prediction"},
              400: {"model": ErrorResponse, "description": "Invalid input"},
              500: {"model": ErrorResponse, "description": "Server error"}
          })
async def predict_aqi(request: PredictionRequest):
    """
    Predict AQI 24 hours in advance.
    
    Provide current pollutant levels and get a prediction for tomorrow's AQI.
    
    Args:
        request: Prediction request with city and pollutant values
    
    Returns:
        Prediction with confidence interval and health message
    
    Example:
        ```
        POST /predict
        {
            "city": "bangkok",
            "aqi": 2.5,
            "pm2_5": 25.0,
            "pm10": 45.0,
            "no2": 15.0,
            "o3": 85.0,
            "model": "xgboost"
        }
        ```
    """
    try:
        logger.info(f"Prediction request for {request.city} using {request.model}")
        
        # Prepare pollutant dictionary
        pollutants = {
            'aqi': request.aqi,
            'pm2_5': request.pm2_5,
            'pm10': request.pm10,
            'no2': request.no2,
            'o3': request.o3,
            'co': request.co,
            'so2': request.so2,
            'nh3': request.nh3
        }
        
        # Make prediction
        prediction, confidence = predictor.predict(
            city=request.city.value,
            pollutants=pollutants,
            model_name=request.model.value
        )
        
        # Prepare response
        response = PredictionResponse(
            city=request.city.value.replace('_', ' ').title(),
            current_aqi=request.aqi,
            predicted_aqi=round(prediction, 2),
            predicted_category=get_aqi_category(prediction),
            confidence_interval=confidence,
            health_message=get_health_message(prediction),
            model_used=request.model.value,
            timestamp=datetime.now()
        )
        
        logger.info(f"✓ Prediction successful: {prediction:.2f}")
        
        return response
        
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post("/predict/batch",
          response_model=BatchPredictionResponse,
          tags=["Predictions"],
          summary="Batch predictions")
async def batch_predict(request: BatchPredictionRequest):
    """
    Predict AQI for multiple cities at once.
    
    Args:
        request: List of prediction requests (max 10)
    
    Returns:
        List of predictions
    """
    try:
        logger.info(f"Batch prediction request: {len(request.requests)} cities")
        
        predictions = []
        
        for req in request.requests:
            # Prepare pollutants
            pollutants = {
                'aqi': req.aqi,
                'pm2_5': req.pm2_5,
                'pm10': req.pm10,
                'no2': req.no2,
                'o3': req.o3,
                'co': req.co,
                'so2': req.so2,
                'nh3': req.nh3
            }
            
            # Make prediction
            prediction, confidence = predictor.predict(
                city=req.city.value,
                pollutants=pollutants,
                model_name=req.model.value
            )
            
            # Add to results
            predictions.append(
                PredictionResponse(
                    city=req.city.value.replace('_', ' ').title(),
                    current_aqi=req.aqi,
                    predicted_aqi=round(prediction, 2),
                    predicted_category=get_aqi_category(prediction),
                    confidence_interval=confidence,
                    health_message=get_health_message(prediction),
                    model_used=req.model.value,
                    timestamp=datetime.now()
                )
            )
        
        logger.info(f"✓ Batch prediction successful: {len(predictions)} predictions")
        
        return BatchPredictionResponse(
            predictions=predictions,
            total_predictions=len(predictions),
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Batch prediction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}"
        )


@app.get("/models",
         tags=["Models"],
         summary="List models")
async def list_models():
    """
    List all available prediction models.
    
    Returns:
        List of model names with descriptions
    """
    models_info = {
        "xgboost": "XGBoost - Best accuracy, industry standard",
        "lightgbm": "LightGBM - Fast and efficient, similar accuracy to XGBoost",
        "randomforest": "Random Forest - Robust ensemble method",
        "linearregression": "Linear Regression - Simple baseline model"
    }
    
    available = predictor.list_models()
    
    return {
        "total_models": len(available),
        "models": [
            {
                "name": model,
                "description": models_info.get(model, "No description available")
            }
            for model in available
        ]
    }


@app.get("/models/{model_name}",
         response_model=ModelInfoResponse,
         tags=["Models"],
         summary="Model details")
async def get_model_info(model_name: str):
    """
    Get detailed information about a specific model.
    
    Args:
        model_name: Name of the model
    
    Returns:
        Model metadata including performance metrics
    """
    try:
        info = predictor.get_model_info(model_name)
        
        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{model_name}' not found"
            )
        
        return ModelInfoResponse(
            model_name=info.get('model_name', model_name),
            model_type=model_name,
            training_date=info.get('timestamp'),
            performance_metrics=info.get('metrics', {}).get('validation', {}),
            features_used=info.get('data_info', {}).get('n_features', 0),
            description=f"Trained ML model for AQI prediction"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": exc.__class__.__name__,
            "message": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("STARTING AIR QUALITY PREDICTOR API")
    print("=" * 80)
    print("\nAPI Documentation: http://localhost:8000/docs")
    print("Alternative docs: http://localhost:8000/redoc")
    print("\nPress CTRL+C to stop")
    print("=" * 80)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)