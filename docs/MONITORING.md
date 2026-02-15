# Grafana Dashboard Configuration for ML Inference Service

## Prometheus Queries

### Service Health Metrics

**Request Rate (requests/sec)**
```promql
rate(inference_requests_total[5m])
```

**Error Rate (%)**
```promql
100 * (
  rate(inference_requests_total{status="error"}[5m])
  /
  rate(inference_requests_total[5m])
)
```

**Request Latency (p50, p95, p99)**
```promql
histogram_quantile(0.50, rate(inference_request_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(inference_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(inference_request_duration_seconds_bucket[5m]))
```

**Active Pods**
```promql
count(up{job="ml-inference-service"})
```

### Model Performance Metrics

**Prediction Confidence Distribution**
```promql
histogram_quantile(0.50, rate(prediction_value_distribution_bucket[5m]))
histogram_quantile(0.95, rate(prediction_value_distribution_bucket[5m]))
```

**Average Prediction Confidence**
```promql
rate(prediction_value_distribution_sum[5m]) / rate(prediction_value_distribution_count[5m])
```

**Model Version**
```promql
model_version_info
```

### Resource Utilization

**CPU Usage**
```promql
rate(container_cpu_usage_seconds_total{pod=~"ml-inference.*"}[5m])
```

**Memory Usage**
```promql
container_memory_working_set_bytes{pod=~"ml-inference.*"} / 1024 / 1024
```

**Pod Restarts**
```promql
increase(kube_pod_container_status_restarts_total{pod=~"ml-inference.*"}[1h])
```

## Alerting Rules

### Critical Alerts

**High Error Rate**
```yaml
- alert: HighErrorRate
  expr: |
    100 * (
      rate(inference_requests_total{status="error"}[5m])
      /
      rate(inference_requests_total[5m])
    ) > 5
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value }}% (threshold: 5%)"
```

**Service Down**
```yaml
- alert: ServiceDown
  expr: up{job="ml-inference-service"} == 0
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "ML Inference Service is down"
    description: "Service has been down for 2 minutes"
```

**Low Replica Count**
```yaml
- alert: LowReplicaCount
  expr: count(up{job="ml-inference-service"}) < 2
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Low replica count"
    description: "Only {{ $value }} replicas available (minimum: 2)"
```

### Warning Alerts

**High Latency**
```yaml
- alert: HighLatency
  expr: |
    histogram_quantile(0.99, 
      rate(inference_request_duration_seconds_bucket[5m])
    ) > 0.5
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "High p99 latency detected"
    description: "P99 latency is {{ $value }}s (threshold: 0.5s)"
```

**Low Prediction Confidence**
```yaml
- alert: LowPredictionConfidence
  expr: |
    (
      rate(prediction_value_distribution_sum[1h])
      /
      rate(prediction_value_distribution_count[1h])
    ) < 0.8
  for: 1h
  labels:
    severity: warning
  annotations:
    summary: "Low average prediction confidence"
    description: "Average confidence is {{ $value }} (threshold: 0.8)"
```

**High Memory Usage**
```yaml
- alert: HighMemoryUsage
  expr: |
    (
      container_memory_working_set_bytes{pod=~"ml-inference.*"}
      /
      container_spec_memory_limit_bytes{pod=~"ml-inference.*"}
    ) > 0.9
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High memory usage"
    description: "Memory usage is {{ $value }}% of limit"
```

## Dashboard Layout

### Row 1: Overview
- Request Rate (graph)
- Error Rate (graph)
- Active Pods (stat)
- Model Version (stat)

### Row 2: Performance
- P50/P95/P99 Latency (graph)
- Request Duration Heatmap
- Requests by Endpoint (pie chart)
- Success vs Error Rate (graph)

### Row 3: Model Metrics
- Prediction Confidence Distribution (histogram)
- Average Confidence Over Time (graph)
- Prediction Count by Class (bar chart)

### Row 4: Resources
- CPU Usage (graph)
- Memory Usage (graph)
- Pod Restarts (table)
- Network I/O (graph)

## Grafana Dashboard JSON

A complete dashboard JSON can be imported with these panels pre-configured.
Contact the team for the full dashboard export.

## Log Queries (Loki)

**Error Logs**
```logql
{app="ml-inference"} |= "ERROR"
```

**Slow Requests (>1s)**
```logql
{app="ml-inference"} | json | duration > 1s
```

**Prediction Logs by Request ID**
```logql
{app="ml-inference"} | json | request_id="example-001"
```