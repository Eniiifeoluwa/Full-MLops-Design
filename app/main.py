"""
ML Inference Service
A production-ready REST API for serving machine learning predictions.
"""
import logging
import time
from typing import List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import numpy as np
import joblib
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import Response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'inference_requests_total',
    'Total inference requests',
    ['status', 'endpoint']
)
REQUEST_LATENCY = Histogram(
    'inference_request_duration_seconds',
    'Inference request latency',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)
PREDICTION_DISTRIBUTION = Histogram(
    'prediction_value_distribution',
    'Distribution of prediction values',
    buckets=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)
MODEL_VERSION = Gauge('model_version_info', 'Model version information')

# Global model holder
model_holder = {"model": None, "version": "1.0.0"}


class PredictionRequest(BaseModel):
    """Request schema for predictions."""
    features: List[float] = Field(
        ...,
        description="Feature vector for prediction",
        min_items=4,
        max_items=4
    )
    request_id: str = Field(
        default=None,
        description="Optional request ID for tracking"
    )

    @validator('features')
    def validate_features(cls, v):
        """Ensure features are valid numbers."""
        if any(np.isnan(x) or np.isinf(x) for x in v):
            raise ValueError("Features cannot contain NaN or Inf values")
        return v


class PredictionResponse(BaseModel):
    """Response schema for predictions."""
    prediction: int = Field(..., description="Predicted class")
    confidence: float = Field(..., description="Prediction confidence")
    model_version: str = Field(..., description="Model version used")
    request_id: str = Field(default=None, description="Request tracking ID")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    model_version: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the application."""
    # Startup: Load model
    logger.info("Loading ML model...")
    try:
        model = joblib.load('app/model.joblib')
        model_holder["model"] = model
        MODEL_VERSION.set(1)
        logger.info(f"Model loaded successfully. Version: {model_holder['version']}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down inference service...")


# Initialize FastAPI app
app = FastAPI(
    title="ML Inference Service",
    description="Production-ready machine learning inference API",
    version="1.0.0",
    lifespan=lifespan
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and track latency."""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    logger.info(
        f"Method={request.method} Path={request.url.path} "
        f"Status={response.status_code} Duration={duration:.3f}s"
    )
    
    return response


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for liveness probe.
    Returns 200 if service is alive.
    """
    REQUEST_COUNT.labels(status='success', endpoint='health').inc()
    return HealthResponse(
        status="healthy",
        model_loaded=model_holder["model"] is not None,
        model_version=model_holder["version"]
    )


@app.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """
    Readiness check endpoint for readiness probe.
    Returns 200 only if model is loaded and ready to serve.
    """
    if model_holder["model"] is None:
        REQUEST_COUNT.labels(status='error', endpoint='ready').inc()
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    REQUEST_COUNT.labels(status='success', endpoint='ready').inc()
    return HealthResponse(
        status="ready",
        model_loaded=True,
        model_version=model_holder["version"]
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Main prediction endpoint.
    
    Args:
        request: PredictionRequest with features
        
    Returns:
        PredictionResponse with prediction and confidence
    """
    with REQUEST_LATENCY.time():
        try:
            # Check model availability
            if model_holder["model"] is None:
                REQUEST_COUNT.labels(status='error', endpoint='predict').inc()
                raise HTTPException(status_code=503, detail="Model not loaded")
            
            # Prepare features
            features = np.array(request.features).reshape(1, -1)
            
            # Make prediction
            prediction = int(model_holder["model"].predict(features)[0])
            
            # Get prediction probabilities for confidence
            try:
                probabilities = model_holder["model"].predict_proba(features)[0]
                confidence = float(max(probabilities))
                PREDICTION_DISTRIBUTION.observe(confidence)
            except AttributeError:
                # Model doesn't support predict_proba
                confidence = 1.0
            
            REQUEST_COUNT.labels(status='success', endpoint='predict').inc()
            
            logger.info(
                f"Prediction successful - Request: {request.request_id}, "
                f"Prediction: {prediction}, Confidence: {confidence:.3f}"
            )
            
            return PredictionResponse(
                prediction=prediction,
                confidence=confidence,
                model_version=model_holder["version"],
                request_id=request.request_id
            )
            
        except ValueError as e:
            REQUEST_COUNT.labels(status='error', endpoint='predict').inc()
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            REQUEST_COUNT.labels(status='error', endpoint='predict').inc()
            logger.error(f"Prediction error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "ML Inference Service",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/predict",
            "health": "/health",
            "ready": "/ready",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)