#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "  Monte Carlo Simulator - Kubernetes Deployment Script    "
echo "=========================================================="

# 1. Build images
echo ""
echo "[1/3] Building Docker images..."
docker build -t options-backend:latest ./backend
docker build -t options-frontend:latest ./frontend

if command -v minikube &> /dev/null; then
    echo "Loading images into Minikube..."
    minikube image load options-backend:latest || true
    minikube image load options-frontend:latest || true
fi

# 2. Apply K8s manifests
echo ""
echo "[2/3] Applying Kubernetes manifests..."
kubectl apply -k k8s/

# 3. Wait for rollouts
echo ""
echo "[3/3] Waiting for pods to roll out..."
kubectl rollout status deployment/backend-deployment -n monte-carlo-sim --timeout=90s || true
kubectl rollout status deployment/frontend-deployment -n monte-carlo-sim --timeout=90s || true
kubectl rollout status deployment/prometheus-deployment -n monte-carlo-sim --timeout=90s || true
kubectl rollout status deployment/grafana-deployment -n monte-carlo-sim --timeout=90s || true

echo ""
echo "=========================================================="
echo "  DEPLOYMENT COMPLETE! ACCESS URLs:                       "
echo "=========================================================="
echo " Frontend Web App:     http://localhost:30080"
echo " Backend API Docs:     http://localhost:30800/docs"
echo " Backend Metrics:      http://localhost:30800/metrics"
echo " Prometheus Server:    http://localhost:30090"
echo " Grafana Dashboard:    http://localhost:30300 (admin / admin)"
echo ""
echo "Optional port-forward commands:"
echo " kubectl port-forward svc/frontend-service 3000:80 -n monte-carlo-sim"
echo " kubectl port-forward svc/backend-service 8000:8000 -n monte-carlo-sim"
echo " kubectl port-forward svc/prometheus-service 9090:9090 -n monte-carlo-sim"
echo " kubectl port-forward svc/grafana-service 3001:3000 -n monte-carlo-sim"
echo "=========================================================="
