# ML Inference System - Design & Decision Document

**Author:** MLOps Engineer Candidate  
**Date:** February 2026  
**Version:** 1.0

---

## 1. Architecture Overview

### System Design

The system is a stateless, containerized ML inference service designed for production deployment on Kubernetes. The architecture follows cloud-native principles with clear separation of concerns.

```
┌─────────────┐
│   Ingress   │ (Load Balancer / API Gateway)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Kubernetes Service (ClusterIP)     │
└──────┬──────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│   ML Inference Pods (3+ replicas)    │
│  ┌────────────────────────────────┐  │
│  │  FastAPI Application           │  │
│  │  - REST API endpoints          │  │
│  │  - Pydantic validation         │  │
│  │  - Health/Ready probes         │  │
│  │  - Prometheus metrics          │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │  ML Model (in-memory)          │  │
│  │  - Loaded at startup           │  │
│  │  - scikit-learn Random Forest  │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│   Monitoring & Observability         │
│  - Prometheus (metrics scraping)     │
│  - Grafana (dashboards)              │
│  - ELK/Loki (log aggregation)        │
└──────────────────────────────────────┘
```

### Key Components

1. **Inference API:** FastAPI-based REST service with validation, error handling, and observability
2. **Container:** Multi-stage Docker build running as non-root user
3. **Orchestration:** Kubernetes with HPA, PDB, and rolling updates
4. **Observability:** Prometheus metrics, structured logging, health checks

---

## 2. Key Engineering Decisions

### 2.1 Technology Choices

**FastAPI over Flask/Django**
- **Rationale:** Native async support, automatic OpenAPI docs, Pydantic validation, better performance
- **Trade-off:** Slightly steeper learning curve, but production benefits outweigh this

**In-Memory Model Loading**
- **Rationale:** Lowest latency (~1-5ms), simple architecture, no external dependencies
- **Trade-off:** Limited to models that fit in memory, requires container restart for updates
- **Alternative considered:** Model server (e.g., MLflow, Seldon) - adds complexity for this use case

**Stateless Design**
- **Rationale:** Horizontal scaling, fault tolerance, no sticky sessions needed
- **Trade-off:** Cannot maintain request context across calls (acceptable for inference)

### 2.2 What I Intentionally Did NOT Build

**Model Training Pipeline**
- **Why:** Inference and training have different scaling characteristics and lifecycles
- **Production approach:** Separate training jobs (e.g., Kubeflow, SageMaker) with model registry

**Model Registry**
- **Why:** Single model scenario doesn't justify the complexity
- **Production approach:** Use MLflow, Weights & Biases, or cloud-native solutions

**Advanced Batching**
- **Why:** Simple REST API pattern, current model is fast enough
- **Production approach:** Implement dynamic batching if latency budget allows (trade latency for throughput)

**Feature Store**
- **Why:** Raw features provided in request (no complex feature engineering)
- **Production approach:** Feast, Tecton, or custom Redis-based store for feature serving

**A/B Testing Framework**
- **Why:** Single model deployment, adds significant complexity
- **Production approach:** Traffic splitting at ingress level with canary deployments

---

## 3. Production Considerations

### 3.1 Service Health Monitoring

**Kubernetes Health Checks**
- **Liveness probe** (`/health`): Checks process health, restarts pod if failing
- **Readiness probe** (`/ready`): Checks model loaded, removes from load balancer if not ready
- **Startup probe:** Not implemented (fast startup), but would add for slow-loading models

**Metrics Collection (Prometheus)**
```python
inference_requests_total{status="success|error", endpoint="predict"}
inference_request_duration_seconds (histogram)
prediction_value_distribution (histogram)
model_version_info (gauge)
```

**Alerting Strategy**
- **High error rate:** >5% over 5 minutes → page on-call
- **High latency:** p99 >500ms → warning, investigate
- **Pod crashes:** >2 restarts in 10 minutes → alert
- **Low replica count:** <2 healthy pods → critical alert

### 3.2 Model Performance Monitoring & Drift Detection

**Prediction Monitoring**
```python
# Track distribution shifts
PREDICTION_DISTRIBUTION.observe(confidence)

# Log predictions for analysis
logger.info(f"Prediction: {prediction}, Confidence: {confidence}")
```

**Drift Detection Strategy**
1. **Statistical monitoring:** Track prediction distribution over time (KL divergence, PSI)
2. **Confidence monitoring:** Alert if average confidence drops significantly
3. **Feature monitoring:** Log feature statistics, compare to training distribution
4. **Ground truth collection:** Sample predictions for manual labeling, compare to model output

**Implementation Approach**
- **Real-time:** Prometheus metrics + Grafana dashboards for distribution shifts
- **Batch:** Daily jobs analyze logs, compute drift metrics (stored in time-series DB)
- **Alerting:** Significant drift (>0.1 PSI) triggers retraining evaluation

### 3.3 Model Rollback Strategy

**Deployment Approach: Blue-Green with Canary**

```bash
# Step 1: Deploy new model version (v2) alongside existing (v1)
kubectl apply -f deployment-v2.yaml --replicas=1

# Step 2: Route 10% traffic to v2 (Istio/Linkerd)
kubectl apply -f virtual-service-canary.yaml

# Step 3: Monitor for 30 minutes
# - Error rate, latency, prediction distribution

# Step 4a: Success → Gradual rollout (50%, 100%)
# Step 4b: Failure → Instant rollback
kubectl apply -f deployment-v1.yaml --replicas=3
kubectl delete deployment ml-inference-v2
```

**Rollback Implementation**
- **Fast rollback:** Keep previous image tag, single `kubectl rollout undo`
- **Model versioning:** Tag images with Git SHA and model version
- **Automated rollback:** If error rate >10% for 5 mins, auto-rollback via CI/CD

**State Management**
- Models stored in S3/GCS with version tags
- Deployment manifests reference specific model versions
- No in-place updates (immutable infrastructure)

### 3.4 Secrets Management

**Current Approach (Development)**
- Environment variables for non-sensitive config (ConfigMap)
- No secrets in current simple implementation

**Production Approach**

**Kubernetes Secrets (basic)**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ml-secrets
type: Opaque
data:
  model-registry-token: <base64-encoded>
  api-key: <base64-encoded>
```

**External Secrets Operator (recommended)**
- Integrates with HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager
- Automatic rotation, audit logging, fine-grained access control

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: ml-secrets
spec:
  secretStoreRef:
    name: aws-secretsmanager
  target:
    name: ml-secrets
  data:
  - secretKey: model-key
    remoteRef:
      key: prod/ml-inference/model-encryption-key
```

**Best Practices**
- Never commit secrets to Git
- Rotate credentials every 90 days
- Use IAM roles for AWS/GCP (no long-lived credentials)
- Encrypt secrets at rest (enabled by default in managed k8s)

---

## 4. Scaling the System

### 4.1 Multiple Models

**Approach 1: Model Router Pattern** (recommended for <10 models)
```
┌──────────────┐
│ API Gateway  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────┐
│  Model Router Service        │
│  - Routes by model_id        │
│  - Load balances replicas    │
└──┬────────────┬──────────────┘
   │            │
   ▼            ▼
┌────────┐  ┌────────┐
│Model A │  │Model B │
│Pods    │  │Pods    │
└────────┘  └────────┘
```

**Approach 2: Multi-Model Service** (if models share resources)
- Load multiple models in single container
- Select model based on request parameter
- Trade-off: Larger memory footprint, but simpler architecture

**Approach 3: Model Server (Seldon, KServe)** (for >10 models)
- Dedicated model serving infrastructure
- Built-in A/B testing, canary deployments, explainability
- Higher operational complexity

### 4.2 Multiple Teams

**Namespace Isolation**
```
team-a-namespace/
  ├── ml-inference-deployment
  ├── ml-inference-service
  └── resource-quota

team-b-namespace/
  ├── ml-inference-deployment
  └── ...
```

**Shared Infrastructure**
- **API Gateway:** Kong, Ambassador for rate limiting, auth, routing
- **Observability:** Centralized Prometheus, shared Grafana dashboards
- **CI/CD:** Shared pipelines with team-specific triggers
- **Model Registry:** MLflow with role-based access control

**Resource Governance**
- **ResourceQuota:** Limit CPU/memory per namespace
- **LimitRange:** Set default/max resource requests
- **PriorityClass:** Ensure critical models get resources first

### 4.3 Higher Traffic

**Horizontal Scaling (primary approach)**
- HPA scales 3→10 replicas based on CPU/memory
- Further scaling: Increase maxReplicas, add node pool auto-scaling

**Vertical Scaling (model-dependent)**
- Increase CPU/memory limits for larger models
- Use GPU nodes for deep learning workloads

**Caching Layer** (if applicable)
```
┌──────────────┐
│  Redis Cache │  (TTL=5min for common requests)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Inference API│
└──────────────┘
```

**Performance Optimizations**
1. **Batch inference:** Accumulate requests, predict in batches (trade latency for throughput)
2. **Model optimization:** ONNX Runtime, TensorRT for faster inference
3. **Connection pooling:** Reuse HTTP connections (handled by Kubernetes)
4. **Request queuing:** Use KEDA for queue-based scaling (e.g., SQS, Kafka)

---

## 5. Optional Bonus: CI/CD Pipeline Sketch

```
┌─────────────┐
│  Git Push   │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────┐
│  GitHub Actions / GitLab CI  │
└──────┬───────────────────────┘
       │
       ├─► Lint & Format (black, flake8)
       ├─► Unit Tests (pytest)
       ├─► Build Docker Image
       ├─► Scan Image (Trivy, Snyk)
       ├─► Push to Registry (ECR, GCR)
       │
       ▼
┌──────────────────────────────┐
│  ArgoCD / Flux (GitOps)      │
└──────┬───────────────────────┘
       │
       ├─► Deploy to Staging
       ├─► Integration Tests
       ├─► Canary Deploy to Prod (10%)
       ├─► Monitor (30 min)
       └─► Full Rollout or Rollback
```

**Key Principles**
- **Immutable artifacts:** Docker images tagged with Git SHA
- **GitOps:** All config in Git, ArgoCD syncs cluster state
- **Automated testing:** Fast feedback loop (<10 min)
- **Progressive delivery:** Canary → blue-green → full rollout

---

## Conclusion

This design prioritizes **simplicity, observability, and operational safety** over premature optimization. The architecture is production-ready for medium-scale deployments and provides clear paths for scaling to multiple models, teams, and higher traffic volumes.

**Trade-offs made:**
- In-memory models (simplicity) vs. model server (flexibility)
- Stateless service (scalability) vs. stateful (request context)
- Rolling updates (zero downtime) vs. blue-green (instant rollback)

**Next steps for production:**
- Add authentication/authorization (OAuth2, API keys)
- Implement comprehensive integration tests
- Set up end-to-end monitoring dashboards
- Document runbooks for common failure scenarios