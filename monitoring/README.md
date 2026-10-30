# Monitoring Stack — Prometheus + Grafana

This project uses **Prometheus** for metrics collection and **Grafana** for dashboards and visualization. The stack is fully configured for both **Docker Compose** (local dev) and **Kubernetes** (production).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      monte-carlo-sim namespace                  │
│                                                                 │
│  ┌──────────────┐   /metrics    ┌────────────────┐             │
│  │   Backend    │◄─────────────►│   Prometheus   │             │
│  │  (FastAPI)   │               │  :9090         │             │
│  │  port 8000   │               └───────┬────────┘             │
│  └──────────────┘                       │ data source          │
│                                         ▼                       │
│  ┌──────────────┐               ┌────────────────┐             │
│  │   Frontend   │               │    Grafana     │             │
│  │  (Nginx)     │               │  :3000         │             │
│  │  port 80     │               │  Dashboard     │             │
│  └──────────────┘               └────────────────┘             │
│                                                                 │
│  ┌──────────────┐                                               │
│  │     HPA      │ 2–8 replicas at 70% CPU                      │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Running Locally (Docker Compose)

```bash
# Start all services including Prometheus + Grafana
docker compose up --build -d

# Check all containers are healthy
docker compose ps
```

| Service     | URL                              | Credentials  |
|-------------|----------------------------------|--------------|
| Frontend    | http://localhost:3000            | —            |
| Backend API | http://localhost:8000/docs       | —            |
| Metrics     | http://localhost:8000/metrics    | —            |
| Prometheus  | http://localhost:9090            | —            |
| Grafana     | http://localhost:3001            | admin / DevOps@2026! |

---

## Running on Kubernetes

### Prerequisites
- `kubectl` installed and pointing to your cluster
- Docker Desktop (with K8s enabled) **or** Minikube **or** Kind

### Deploy

```powershell
# Build Docker images and apply all manifests via Kustomize
.\scripts\deploy-k8s.ps1

# Or manually:
docker build -t options-backend:latest ./backend
docker build -t options-frontend:latest ./frontend
kubectl apply -k k8s/
```

### Access via NodePort

| Service     | NodePort URL                          | Notes               |
|-------------|---------------------------------------|---------------------|
| Frontend    | http://localhost:30080                |                     |
| Backend API | http://localhost:30800/docs           |                     |
| Metrics     | http://localhost:30800/metrics        |                     |
| Prometheus  | http://localhost:30090                |                     |
| Grafana     | http://localhost:30300                | admin / DevOps@2026!|

### Access via Ingress (NGINX Ingress Controller required)

| Service     | Ingress Path                          |
|-------------|---------------------------------------|
| Frontend    | http://localhost/                     |
| Backend API | http://localhost/api/                 |
| Grafana     | http://localhost/grafana/             |
| Prometheus  | http://localhost/prometheus/          |

> **Note**: Install NGINX Ingress Controller with:
> ```bash
> kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.1/deploy/static/provider/cloud/deploy.yaml
> ```

### Access via Port-Forwarding (any cluster)

```bash
kubectl port-forward svc/frontend-service    3000:80   -n monte-carlo-sim
kubectl port-forward svc/backend-service     8000:8000 -n monte-carlo-sim
kubectl port-forward svc/prometheus-service  9090:9090 -n monte-carlo-sim
kubectl port-forward svc/grafana-service     3001:3000 -n monte-carlo-sim
```

---

## Prometheus Metrics

The backend (`main.py`) exposes these custom metrics at `/metrics`:

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | HTTP requests by method, endpoint, status |
| `http_request_duration_seconds` | Histogram | Request latency with percentile buckets |
| `monte_carlo_simulations_total` | Counter | Simulations by option_type, style, status |
| `monte_carlo_simulation_duration_seconds` | Histogram | Simulation compute time |
| `monte_carlo_simulated_paths_total` | Counter | Total GBM paths computed |
| `monte_carlo_active_websockets` | Gauge | Live WebSocket connections |
| `monte_carlo_last_simulated_price` | Gauge | Most recent option price per type |

### Useful PromQL Queries

```promql
# Simulation throughput (ops/sec)
sum by (option_type, style) (rate(monte_carlo_simulations_total[1m]))

# p99 simulation latency
histogram_quantile(0.99, sum by (le) (rate(monte_carlo_simulation_duration_seconds_bucket[1m])))

# HTTP error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# Active WebSocket connections
monte_carlo_active_websockets

# Backend memory usage
process_resident_memory_bytes
```

---

## Grafana Dashboard

The pre-provisioned dashboard **"Monte Carlo Options Simulator & DevOps Metrics"** (UID: `options-simulator-main`) includes:

### 📊 Quant Engine Overview
- Total Simulations Run
- Total Simulated Paths
- Active WebSocket Streams
- Latest Option Price (\$)

### ⚡ Performance & Latency
- Simulation Throughput (ops/sec)
- Monte Carlo Latency (p50 / p90 / p99)

### 🌐 API Traffic & Reliability
- HTTP Request Rate by Endpoint
- HTTP Status Codes (2xx, 4xx, 5xx)

### 🖥️ System & Runtime Telemetry
- Process Resident Memory (RSS)
- Process CPU Usage Rate

---

## Alerting Rules

Alerting rules are defined in:
- **Docker Compose**: `monitoring/prometheus/alerts.yml`
- **Kubernetes**: `k8s/monitoring/prometheus-alerts.yaml`

| Alert | Severity | Condition |
|-------|----------|-----------|
| `BackendDown` | 🔴 Critical | Backend unreachable for 1 min |
| `HighErrorRate` | 🔴 Critical | 5xx rate > 5% for 2 min |
| `SimulationErrorSpike` | 🔴 Critical | Simulation error rate > 10% |
| `HighSimulationLatencyP99` | 🟡 Warning | p99 latency > 2s for 3 min |
| `HighHTTPLatencyP95` | 🟡 Warning | Endpoint p95 > 1s for 5 min |
| `TooManyActiveWebSockets` | 🟡 Warning | Active WS > 50 for 2 min |
| `HPAAtMaxReplicas` | 🟡 Warning | HPA at max replicas for 5 min |
| `HighMemoryUsage` | 🟡 Warning | Memory > 400MB for 5 min |
| `PodNotReady` | 🔴 Critical | Pod not ready for 3 min |
| `PodCrashLooping` | 🔴 Critical | Pod restarting frequently |
| `NoIncomingTraffic` | 🟡 Warning | Zero requests for 5 min |

> To add Alertmanager (email/Slack notifications), add an `alertmanager-deployment.yaml` and configure `alerting:` in `prometheus.yml`.

---

## File Structure

```
monitoring/
├── prometheus/
│   ├── prometheus.yml          ← Main scrape config (Docker Compose)
│   └── alerts.yml              ← Alerting rules (Docker Compose)
└── grafana/
    ├── provisioning/
    │   ├── datasources/
    │   │   └── datasources.yaml    ← Auto-connects Grafana → Prometheus
    │   └── dashboards/
    │       └── dashboards.yaml     ← Tells Grafana where to find dashboard JSONs
    └── dashboards/
        └── options-simulator.json  ← Pre-built dashboard definition

k8s/monitoring/
├── prometheus-rbac.yaml            ← ServiceAccount + ClusterRole for pod discovery
├── prometheus-pvc.yaml             ← 5Gi persistent storage for Prometheus
├── prometheus-configmap.yaml       ← Prometheus config (K8s service discovery)
├── prometheus-alerts.yaml          ← Alerting rules ConfigMap
├── prometheus-deployment.yaml      ← Prometheus pod spec
├── prometheus-service.yaml         ← NodePort :30090
├── grafana-secret.yaml             ← Admin credentials (base64)
├── grafana-pvc.yaml                ← 2Gi persistent storage for Grafana
├── grafana-datasources-configmap.yaml
├── grafana-dashboards-configmap.yaml
├── grafana-deployment.yaml         ← Grafana pod spec
└── grafana-service.yaml            ← NodePort :30300
```
