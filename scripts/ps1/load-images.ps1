Write-Host "Loading images into Minikube..."
minikube image load semantic-search-model-service:latest
minikube image load qdrant/qdrant:v1.17.0
minikube image load semantic-search-document-service:latest
minikube image load semantic-search-search-service:latest
minikube image load semantic-search-gateway:latest
Write-Host "Done."