# ML Inference Service - MLOps

A production-ready machine learning inference system designed for Kubernetes deployment.

## Project Overview

This project demonstrates a minimal yet production-grade ML inference service with:
- ✅ REST API for model predictions (FastAPI)
- ✅ Containerized deployment (Docker)
- ✅ Kubernetes manifests with autoscaling
- ✅ Health checks and observability
- ✅ Comprehensive design documentation

**Model:** Random Forest classifier trained on Iris dataset (simple example)  
**Focus:** Production engineering, not model accuracy

## Quick Start

### Prerequisites

- Python 3.11+
- Docker
- curl and jq (for testing)

### Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Train the model** (already done, but to retrain):
```bash
python train_model.py
```

3. **Run the service:**
```bash
python -m uvicorn app.main:app --reload
```

4. **Test the API:**
```bash
# In another terminal
./examples/test_requests.sh

# Or using Python
python examples/test_requests.py
```

### Docker Deployment

1. **Build the image:**
```bash
docker build -t ml-inference-service:1.0.0 .
```

2. **Run the container:**
```bash
docker run -p 8000:8000 ml-inference-service:1.0.0
```

3. **Test:**
```bash
curl http://localhost:8000/health
```

### Docker Compose

```bash
docker-compose up --build
```

## API Documentation

Once running, visit:
- **Interactive docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Example Request

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": [5.1, 3.5, 1.4, 0.2],
    "request_id": "test-001"
  }'
```

### Example Response

```json
{
  "prediction": 0,
  "confidence": 0.98,
  "model_version": "1.0.0",
  "request_id": "test-001"
}
```

## Kubernetes Deployment

See [k8s/README.md](k8s/README.md) for detailed instructions.

**Quick deploy:**
```bash
# Apply all manifests
kubectl apply -f k8s/

# Check status
kubectl get pods -l app=ml-inference
kubectl get svc ml-inference-service

# Port forward for local testing
kubectl port-forward svc/ml-inference-service 8000:80
```

## Project Structure

```
.
├── app/
│   ├── main.py              # FastAPI application
│   └── model.joblib         # Trained model
├── k8s/
│   ├── deployment.yaml      # Kubernetes deployment
│   ├── deployment-gpu.yaml  # GPU-enabled deployment
│   ├── service.yaml         # Service definition
│   ├── hpa.yaml            # Horizontal Pod Autoscaler
│   ├── configmap.yaml      # Configuration
│   ├── pdb.yaml            # Pod Disruption Budget
│   └── README.md           # K8s deployment guide
├── docs/
│   └── DESIGN.md           # Design & decision document
├── examples/
│   ├── test_requests.sh    # Bash test script
│   └── test_requests.py    # Python test script
├── Dockerfile              # Container definition
├── docker-compose.yml      # Docker Compose config
├── requirements.txt        # Python dependencies
├── train_model.py         # Model training script
└── README.md              # This file
```

## Design Document

See [docs/DESIGN.md](docs/DESIGN.md) for comprehensive documentation covering:
1. Architecture overview
2. Key engineering decisions
3. Production considerations (monitoring, drift detection, rollback, secrets)
4. Scaling strategy (multiple models, teams, traffic)

## Key Features

### Production-Ready Design

- **Stateless service:** Horizontal scaling, no session affinity needed
- **Health checks:** Liveness and readiness probes for Kubernetes
- **Observability:** Prometheus metrics, structured logging
- **Security:** Non-root container, minimal dependencies
- **High availability:** 3+ replicas, pod disruption budget, anti-affinity

### Monitoring & Metrics

Available at `/metrics`:
- `inference_requests_total` - Request count by status/endpoint
- `inference_request_duration_seconds` - Latency distribution
- `prediction_value_distribution` - Confidence scores
- `model_version_info` - Current model version

### Auto-scaling

- **CPU-based:** Scales up when CPU >70%
- **Memory-based:** Scales up when memory >80%
- **Range:** 3-10 replicas
- **Behavior:** Fast scale-up, conservative scale-down

## Assumptions Made

1. **Single model:** System serves one model version at a time
2. **In-memory model:** Model fits in memory (<1GB)
3. **Stateless requests:** No session state or request batching
4. **Simple features:** Raw features provided (no feature store)
5. **Internal service:** No authentication/authorization implemented
6. **CPU inference:** GPU support documented but not default

## Trade-offs & Decisions

### Technology Choices

**FastAPI vs Flask**
- ✅ Better async support, automatic validation, OpenAPI docs
- ❌ Slightly more complex than Flask

**In-memory model vs Model Server**
- ✅ Lowest latency, simpler architecture
- ❌ Limited to small models, requires restart for updates

**Kubernetes vs Serverless**
- ✅ More control, predictable costs, better for high-throughput
- ❌ More operational complexity than Lambda/Cloud Run

### What Was NOT Implemented

- ❌ Model training pipeline (separate concern)
- ❌ Model registry (MLflow, etc.)
- ❌ Feature store (not needed for simple features)
- ❌ A/B testing framework (adds complexity)
- ❌ Request batching (not needed for fast models)
- ❌ Authentication (would use OAuth2/API keys in prod)

## Testing

### Unit Tests (if time permits)

```bash
pytest tests/ -v
```

### Load Testing

```bash
# Install k6
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [5.1, 3.5, 1.4, 0.2]}' \
  -s -o /dev/null -w "Time: %{time_total}s\n"
```

## Production Considerations

### Security
- Container runs as non-root user (UID 1000)
- Read-only root filesystem (configurable)
- No privileged escalation
- Secrets via Kubernetes Secrets or external secret manager

### Monitoring
- Prometheus metrics for service health
- Log aggregation for debugging
- Distributed tracing for complex flows (future)

### Disaster Recovery
- Rolling updates with zero downtime
- Automated rollback on health check failures
- Pod disruption budget ensures minimum availability
- Previous image versions retained for quick rollback

## Future Enhancements

1. **Model versioning:** Blue-green deployments, A/B testing
2. **Feature store:** Online feature serving for complex features
3. **Model registry:** MLflow integration for model lifecycle
4. **Batch inference:** Queue-based processing for high throughput
5. **Multi-model serving:** Single service for multiple models
6. **Advanced observability:** Distributed tracing, APM integration
7. **Authentication:** OAuth2, API keys, rate limiting

## Questions & Contact

For questions about this implementation, please contact the candidate or refer to:
- Design document: [docs/DESIGN.md](docs/DESIGN.md)
- Kubernetes guide: [k8s/README.md](k8s/README.md)

## License

This is a take-home exercise project. All code is provided as-is for evaluation purposes.
