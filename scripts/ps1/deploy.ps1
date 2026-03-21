Write-Host "Applying Minikube manifests..."
kubectl apply -f minikube/configmaps/
kubectl apply -f minikube/volumes/
kubectl apply -f minikube/deployments/
kubectl apply -f minikube/services/
Write-Host "Waiting for pods..."
kubectl wait --for=condition=ready pod --all --timeout=120s
Write-Host "Done."
kubectl get pods