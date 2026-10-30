# PowerShell script to clean up Monte Carlo Simulator Kubernetes resources
Write-Host "Tearing down Kubernetes resources for Monte Carlo Simulator..." -ForegroundColor Yellow
kubectl delete -k k8s/
Write-Host "Cleanup complete!" -ForegroundColor Green
