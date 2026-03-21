Write-Host "Loading images into Minikube..."
minikube image load 703-document-service:latest
minikube image load 703-search-service:latest
minikube image load 703-gateway:latest
minikube image load 703-model-service:latest
minikube image load qdrant/qdrant:v1.17.0
minikube image load nginx:alpine
Write-Host "Done."