# Kubernetes, Prometheus & Grafana Architecture & Setup Guide

This guide describes how to run and monitor the **Monte Carlo Options Pricing & Risk Simulator** using **Kubernetes**, **Prometheus**, and **Grafana**.

---

## 1. Architecture Overview

```mermaid
flowchart TD
    subgraph Browser ["Client Web Browser"]
        User["User / Trader"]
    end

    subgraph Kubernetes ["Kubernetes Cluster (Namespace: monte-carlo-sim)"]
        Ingress["Ingress Controller\n(Port 80)"]
        
        subgraph Frontend_Pods ["Frontend Tier"]
            F_Svc["frontend-service\nNodePort: 30080"]
            F_Pod1["options-frontend-1\n(Nginx + React SPA)"]
            F_Pod2["options-frontend-2\n(Nginx + React SPA)"]
        end

        subgraph Backend_Pods ["Backend Quant Tier"]
            B_Svc["backend-service\nNodePort: 30800"]
            B_Pod1["options-backend-1\n(FastAPI Engine)"]
            B_Pod2["options-backend-2\n(FastAPI Engine)"]
            HPA["Horizontal Pod Autoscaler\n(Min: 2, Max: 8 @ 70% CPU)"]
        end

        subgraph Monitoring_Tier ["Observability Tier"]
            Prom_Svc["prometheus-service\nNodePort: 30090"]
            Prom_Pod["Prometheus Server\nv2.51.0"]
            
            Graf_Svc["grafana-service\nNodePort: 30300"]
            Graf_Pod["Grafana Server\nv10.4.0\n(Pre-provisioned Dashboards)"]
        end
    end

    User -->|HTTP 30080| F_Svc
    User -->|Grafana 30300| Graf_Svc
    User -->|Prometheus 30090| Prom_Svc

    F_Svc --> F_Pod1 & F_Pod2
    F_Pod1 & F_Pod2 -->|REST & WebSockets| B_Svc
    B_Svc --> B_Pod1 & B_Pod2
    HPA -.->|Autoscales| Backend_Pods

    Prom_Pod -->|Scrapes /metrics (5s)| B_Pod1 & B_Pod2
    Prom_Pod -->|Self-scrape| Prom_Pod
    Graf_Pod -->|PromQL Queries| Prom_Svc
```

---

## 2. Telemetry & Metrics Catalog

The FastAPI backend exposes Prometheus metrics on `/metrics`:

### Quant & Domain Metrics
| Metric Name | Type | Labels | Description |
|---|---|---|---|
| `monte_carlo_simulations_total` | Counter | `option_type`, `style`, `status` | Cumulative Monte Carlo simulation requests |
| `monte_carlo_simulation_duration_seconds` | Histogram | `option_type`, `style` | Latency distribution of simulation calculations |
| `monte_carlo_simulated_paths_total` | Counter | - | Total price paths simulated across all runs |
| `monte_carlo_active_websockets` | Gauge | - | Real-time active WebSocket client connections |
| `monte_carlo_last_simulated_price` | Gauge | `option_type`, `style` | Last computed option price |

### HTTP & Infrastructure Metrics
| Metric Name | Type | Labels | Description |
|---|---|---|---|
| `http_requests_total` | Counter | `method`, `endpoint`, `status` | Throughput of HTTP calls |
| `http_request_duration_seconds` | Histogram | `method`, `endpoint` | Request duration in seconds |
| `process_resident_memory_bytes` | Gauge | - | Physical memory (RSS) consumed by backend |
| `process_cpu_seconds_total` | Counter | - | Cumulative CPU time used by the Python process |

---

## 3. Quickstart: Local Docker Compose (1 Command)

To run the complete stack locally with Prometheus and Grafana pre-wired:

```bash
docker compose up -d --build
```

### Access URLs:
- **Frontend App**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend Metrics**: [http://localhost:8000/metrics](http://localhost:8000/metrics)
- **Prometheus UI**: [http://localhost:9090](http://localhost:9090)
- **Grafana UI**: [http://localhost:3001](http://localhost:3001)
  - **Username**: `admin`
  - **Password**: `admin`
  - *(Dashboard is automatically provisioned under "Options Simulator")*

To stop:
```bash
docker compose down
```

---

## 4. Kubernetes Deployment

The Kubernetes manifests are located in `k8s/` and managed with **Kustomize**.

### Step 1: Build Docker Images
```bash
docker build -t options-backend:latest ./backend
docker build -t options-frontend:latest ./frontend
```

*(If using Minikube or Kind, load the images into the local cluster)*:
```bash
# For Minikube:
minikube image load options-backend:latest
minikube image load options-frontend:latest

# For Kind:
kind load docker-image options-backend:latest options-frontend:latest
```

### Step 2: Deploy to Kubernetes
Using the deployment scripts:
- **Windows (PowerShell)**:
  ```powershell
  .\scripts\deploy-k8s.ps1
  ```
- **Linux / macOS**:
  ```bash
  chmod +x ./scripts/deploy-k8s.sh
  ./scripts/deploy-k8s.sh
  ```
- **Or directly via kubectl**:
  ```bash
  kubectl apply -k k8s/
  ```

### Step 3: Verify Pods & Services
```bash
kubectl get pods -n monte-carlo-sim
kubectl get svc -n monte-carlo-sim
kubectl get hpa -n monte-carlo-sim
```

### Step 4: Access Endpoints
| Component | NodePort URL | Port-Forward Command |
|---|---|---|
| **Frontend Web App** | `http://localhost:30080` | `kubectl port-forward svc/frontend-service 3000:80 -n monte-carlo-sim` |
| **Backend API Docs** | `http://localhost:30800/docs` | `kubectl port-forward svc/backend-service 8000:8000 -n monte-carlo-sim` |
| **Prometheus Server** | `http://localhost:30090` | `kubectl port-forward svc/prometheus-service 9090:9090 -n monte-carlo-sim` |
| **Grafana Dashboard** | `http://localhost:30300` | `kubectl port-forward svc/grafana-service 3001:3000 -n monte-carlo-sim` |

---

## 5. Grafana Dashboard Panels

When opening Grafana (`http://localhost:30300` or `http://localhost:3001`, user: `admin`, pass: `admin`), navigate to **Dashboards > Options Simulator > Monte Carlo Options Simulator & DevOps Metrics**:

1. **Total Simulations Run**: Counter of total simulation calculations.
2. **Total Simulated Paths**: Total paths computed across European, Asian, and Barrier options.
3. **Active WebSocket Streams**: Real-time gauge of open WebSocket simulation connections.
4. **Latest Option Price**: Current simulated price with currency formatting.
5. **Simulation Throughput (Ops/sec)**: Rate of simulations segmented by option type & style.
6. **Simulation Latency (p50 / p90 / p99)**: Quant latency percentiles.
7. **HTTP Traffic by Endpoint**: Rate of calls to `/simulate`, `/ticker-info`, and `/health`.
8. **HTTP Status Codes**: Bar chart showing 2xx, 4xx, and 5xx response rates.
9. **Process Memory (RSS)**: Backend memory footprint.
10. **CPU Utilization**: CPU second rate under Monte Carlo workload.

---

## 6. Teardown
To remove all Kubernetes resources:
```bash
kubectl delete -k k8s/
```
Or via script:
```powershell
.\scripts\cleanup-k8s.ps1
```
