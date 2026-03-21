#!/bin/bash
echo "Applying Minikube manifests..."
kubectl apply -f minikube/configmaps/
kubectl apply -f minikube/volumes/
kubectl apply -f minikube/deployments/
kubectl apply -f minikube/services/
echo "Waiting for pods..."
kubectl wait --for=condition=ready pod --all --timeout=120s
echo "Done."
kubectl get pods