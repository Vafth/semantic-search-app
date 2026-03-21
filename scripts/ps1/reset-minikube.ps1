Write-Host "Deleting all resources..."
kubectl delete -f minikube/services/
kubectl delete -f minikube/deployments/
kubectl delete -f minikube/volumes/
kubectl delete -f minikube/configmaps/
Write-Host "Done."