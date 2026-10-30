# Monte Carlo Options Pricing & Risk Simulator

Full-stack quant project: FastAPI backend runs Monte Carlo simulations for
European/Asian/Barrier options, React frontend visualizes convergence, price
paths, payoff distribution, and Greeks.

## Structure

```
backend/       FastAPI app, MC pricing engine, pytest suite, Prometheus metrics (/metrics, /health)
frontend/      React (Vite) app, charts via recharts, vitest tests, Nginx reverse proxy
k8s/           Kubernetes manifests (Deployments, Services, HPA, Ingress, Kustomize)
monitoring/    Prometheus scrape config & Grafana dashboards/datasources provisioning
dashboard/     Static page showing commit activity per contributor (GitHub API)
scripts/       Automated deployment and cleanup scripts for Kubernetes
Jenkinsfile    CI pipeline — auto-triggered on every push (tests + build + k8s validation)
docs/          Setup guides, K8s & Monitoring architecture, team plan, git workflow
```

## Running with Docker Compose (Instant Full-Stack + Monitoring)

Run the full application alongside Prometheus and Grafana with a single command:

```bash
docker compose up -d --build
```

- **Frontend App**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend Prometheus Metrics**: [http://localhost:8000/metrics](http://localhost:8000/metrics)
- **Prometheus Server**: [http://localhost:9090](http://localhost:9090)
- **Grafana Dashboard**: [http://localhost:3001](http://localhost:3001) *(login: `admin` / `admin`)*

## Running on Kubernetes

Complete production-grade Kubernetes manifests are in `k8s/` and include HPA (Horizontal Pod Autoscaling), Ingress, Liveness/Readiness health probes, Prometheus auto-discovery, and pre-provisioned Grafana dashboards.

### Quick Deploy:
- **Windows (PowerShell)**:
  ```powershell
  .\scripts\deploy-k8s.ps1
  ```
- **Linux / macOS**:
  ```bash
  ./scripts/deploy-k8s.sh
  ```
- **Or via kubectl**:
  ```bash
  kubectl apply -k k8s/
  ```

### Accessing Endpoints:
- **Frontend App**: `http://localhost:30080` (or `kubectl port-forward svc/frontend-service 3000:80 -n monte-carlo-sim`)
- **Backend API Docs**: `http://localhost:30800/docs`
- **Prometheus Server**: `http://localhost:30090`
- **Grafana Dashboard**: `http://localhost:30300` *(login: `admin` / `admin`)*

For complete architectural details and metric catalogs, see [`docs/KUBERNETES_PROMETHEUS_GRAFANA.md`](docs/KUBERNETES_PROMETHEUS_GRAFANA.md).

## Running locally without containers

**Backend**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Runs on `http://127.0.0.1:8000`. Swagger docs at `/docs`. Metrics at `/metrics`.

**Frontend**
```bash
cd frontend
npm install
npm run dev
```
Runs on `http://127.0.0.1:5173`, calls backend at `http://127.0.0.1:8000`
(override with `VITE_API_BASE` env var).

**Tests**
```bash
cd backend && python -m pytest tests/ -v
cd frontend && npm test
```

**Dashboard**
Open `dashboard/index.html` directly in a browser, or serve it with any
static server. Edit `OWNER`/`REPO` at the top of `dashboard/dashboard.js`
first.

## CI/CD

See `docs/JENKINS_SETUP.md` for full setup. Jenkins pipeline (`Jenkinsfile`) runs backend pytest + frontend vitest + frontend build + Kubernetes manifest validation on every commit.

