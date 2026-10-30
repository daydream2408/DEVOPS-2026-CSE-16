#!/usr/bin/env bash
echo "Tearing down Kubernetes resources for Monte Carlo Simulator..."
kubectl delete -k k8s/ || true
echo "Cleanup complete!"
