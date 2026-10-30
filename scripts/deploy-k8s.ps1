# PowerShell script to build and deploy Monte Carlo Options Simulator to Kubernetes
param(
    [switch]$BuildImages = $true,
    [string]$ClusterType = "auto" # "auto", "docker-desktop", "minikube", "kind"
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Monte Carlo Simulator - Kubernetes Deployment Script    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check kubectl
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Error "kubectl is not installed or not in PATH."
    exit 1
}

# 2. Build Docker images if requested
if ($BuildImages) {
    Write-Host "`n[1/3] Building Docker images..." -ForegroundColor Yellow
    docker build -t options-backend:latest ./backend
    docker build -t options-frontend:latest ./frontend

    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Docker build encountered an issue. Ensure Docker Daemon is running if rebuilding."
    }

    # Load into kind/minikube if detected
    if ($ClusterType -eq "minikube" -or (Get-Command minikube -ErrorAction SilentlyContinue)) {
        Write-Host "Loading images into Minikube..." -ForegroundColor Cyan
        minikube image load options-backend:latest
        minikube image load options-frontend:latest
    }
}

# 3. Apply Kubernetes manifests
Write-Host "`n[2/3] Applying Kubernetes manifests via Kustomize..." -ForegroundColor Yellow
kubectl apply -k k8s/

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to apply Kubernetes manifests. Check cluster connectivity."
    exit 1
}

# 4. Wait for rollouts
Write-Host "`n[3/3] Waiting for deployments to become ready..." -ForegroundColor Yellow
kubectl rollout status deployment/backend-deployment -n monte-carlo-sim --timeout=90s
kubectl rollout status deployment/frontend-deployment -n monte-carlo-sim --timeout=90s
kubectl rollout status deployment/prometheus-deployment -n monte-carlo-sim --timeout=90s
kubectl rollout status deployment/grafana-deployment -n monte-carlo-sim --timeout=90s

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  DEVICES & SERVICES READY! ACCESS URLs:                 " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " Frontend Web App:     http://localhost:30080" -ForegroundColor White
Write-Host " Backend API Docs:     http://localhost:30800/docs" -ForegroundColor White
Write-Host " Backend Metrics:      http://localhost:30800/metrics" -ForegroundColor White
Write-Host " Prometheus Server:    http://localhost:30090" -ForegroundColor White
Write-Host " Grafana Dashboard:    http://localhost:30300 (admin / admin)" -ForegroundColor White
Write-Host "`nIf NodePort is not accessible on your cluster, use port-forwarding:" -ForegroundColor Cyan
Write-Host " kubectl port-forward svc/frontend-service 3000:80 -n monte-carlo-sim" -ForegroundColor Gray
Write-Host " kubectl port-forward svc/backend-service 8000:8000 -n monte-carlo-sim" -ForegroundColor Gray
Write-Host " kubectl port-forward svc/prometheus-service 9090:9090 -n monte-carlo-sim" -ForegroundColor Gray
Write-Host " kubectl port-forward svc/grafana-service 3001:3000 -n monte-carlo-sim" -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Green
