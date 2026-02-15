# Kubernetes Deployment Guide

## Overview

This directory contains Kubernetes manifests for deploying the ML inference service in a production-like environment.

## Files

- `deployment.yaml` - Main deployment configuration with CPU-based workloads
- `deployment-gpu.yaml` - GPU-enabled deployment (example)
- `service.yaml` - ClusterIP service for internal access
- `hpa.yaml` - Horizontal Pod Autoscaler for automatic scaling
- `configmap.yaml` - Configuration management
- `pdb.yaml` - Pod Disruption Budget for high availability

## Design Decisions

### Resource Allocation

**CPU-based deployment:**
- Requests: 250m CPU, 512Mi memory
- Limits: 1000m CPU, 1Gi memory
- Rationale: Provides 4:1 burst capacity while ensuring stable baseline performance

**GPU-based deployment:**
- 1 GPU per pod
- 2-4 CPU cores, 4-8Gi memory
- Rationale: GPUs are expensive; optimize for throughput with proper CPU/memory pairing

### Health Checks

**Liveness Probe:**
- Path: `/health`
- Checks if the process is alive
- Failure triggers pod restart

**Readiness Probe:**
- Path: `/ready`
- Checks if model is loaded and ready to serve
- Failure removes pod from service endpoints

### High Availability

- **3 replicas minimum** for fault tolerance
- **Pod Anti-Affinity** spreads pods across nodes
- **Pod Disruption Budget** ensures at least 2 pods during updates
- **Rolling Update Strategy** with zero downtime (maxUnavailable: 0)

## Deployment Instructions

### Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Verify deployment
kubectl get deployments
kubectl get pods
kubectl get svc

# Check pod logs
kubectl logs -l app=ml-inference --tail=50

# Test the service
kubectl port-forward svc/ml-inference-service 8000:80
curl http://localhost:8000/health
```

### Deploy with GPU Support

```bash
# Prerequisites:
# 1. Cluster must have GPU nodes (e.g., GKE with nvidia-tesla-t4)
# 2. NVIDIA device plugin must be installed

# Deploy GPU-enabled version
kubectl apply -f k8s/deployment-gpu.yaml

# Verify GPU allocation
kubectl describe pod <pod-name> | grep -A 5 "nvidia.com/gpu"
```

## Scaling

### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment ml-inference-service --replicas=5

# Verify
kubectl get deployments
```

### Auto-scaling (HPA)

The HPA automatically scales based on:
- CPU utilization > 70%
- Memory utilization > 80%

```bash
# Check HPA status
kubectl get hpa ml-inference-hpa

# Describe HPA for detailed metrics
kubectl describe hpa ml-inference-hpa
```

**Scaling behavior:**
- Scales up aggressively (100% or +2 pods per 15s)
- Scales down conservatively (50% per 15s after 5min stabilization)
- Min: 3 replicas, Max: 10 replicas

## GPU Support Details

### Prerequisites

1. **GPU Node Pool:** Provision nodes with GPUs
   ```bash
   # GKE example
   gcloud container node-pools create gpu-pool \
     --cluster=my-cluster \
     --accelerator type=nvidia-tesla-t4,count=1 \
     --machine-type=n1-standard-4
   ```

2. **NVIDIA Device Plugin:**
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml
   ```

3. **Container Image:** Must include CUDA runtime
   ```dockerfile
   FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04
   # ... rest of Dockerfile
   ```

### GPU Resource Management

- **Node Selector:** Routes pods to GPU nodes only
- **Tolerations:** Allows scheduling on tainted GPU nodes
- **Resource Requests:** Ensures exclusive GPU access
- **Time-slicing:** Not used (dedicated GPU per pod for consistent latency)

### GPU vs CPU Deployment

Use GPU deployment when:
- Model requires GPU acceleration (deep learning)
- Batch inference with high throughput needs
- Cost-effective at scale (amortize GPU cost over many requests)

Use CPU deployment when:
- Simple models (scikit-learn, XGBoost)
- Low latency requirements (avoid GPU scheduling overhead)
- Cost-sensitive workloads

## Monitoring

Prometheus metrics available at `/metrics`:
- `inference_requests_total` - Request count by status
- `inference_request_duration_seconds` - Latency histogram
- `prediction_value_distribution` - Prediction confidence distribution
- `model_version_info` - Current model version

## Secrets Management

For production, store sensitive data in Kubernetes Secrets:

```bash
# Create secret for model registry credentials
kubectl create secret docker-registry model-registry \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass

# Reference in deployment
spec:
  imagePullSecrets:
  - name: model-registry
```

For model encryption keys, API keys, etc:

```bash
kubectl create secret generic ml-secrets \
  --from-literal=model-key=<encryption-key> \
  --from-literal=api-key=<api-key>
```

## Troubleshooting

```bash
# Pod not starting
kubectl describe pod <pod-name>
kubectl logs <pod-name>

# Service not accessible
kubectl get endpoints ml-inference-service

# HPA not scaling
kubectl describe hpa ml-inference-hpa
kubectl top pods  # requires metrics-server
```