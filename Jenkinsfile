pipeline {
    agent any

    environment {
        OWNER               = 'kellaritonttu'
        GIT_SHA             = "${GIT_COMMIT[0..7]}"
        DOCKERHUB_NAMESPACE = 'harhatilatonttu'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Login to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKERHUB_USER',
                    passwordVariable: 'DOCKERHUB_TOKEN'
                )]) {
                    sh 'echo $DOCKERHUB_TOKEN | docker login -u $DOCKERHUB_USER --password-stdin'
                }
            }
        }

        stage('Build and Push Images') {
            parallel {
                stage('gateway') {
                    steps {
                        sh """
                            docker build \
                                -t ${DOCKERHUB_NAMESPACE}/semantic-search-app-gateway:${GIT_SHA} \
                                -t ${DOCKERHUB_NAMESPACE}/semantic-search-app-gateway:latest \
                                -f services/gateway_service/Dockerfile .
                            docker push ${DOCKERHUB_NAMESPACE}/semantic-search-app-gateway:${GIT_SHA}
                            docker push ${DOCKERHUB_NAMESPACE}/semantic-search-app-gateway:latest
                        """
                    }
                }
                stage('user-service') {
                    steps {
                        sh """
                            docker build \
                                -t ${DOCKERHUB_NAMESPACE}/semantic-search-app-user:${GIT_SHA} \
                                -t ${DOCKERHUB_NAMESPACE}/semantic-search-app-user:latest \
                                -f services/user_service/Dockerfile .
                            docker push ${DOCKERHUB_NAMESPACE}/semantic-search-app-user:${GIT_SHA}
                            docker push ${DOCKERHUB_NAMESPACE}/semantic-search-app-user:latest
                        """
                    }
                }
                stage('document-service') {
                    steps {
                        sh """
                            docker build \
                                -t ${DOCKERHUB_NAMESPACE}/semantic-search-app-document:${GIT_SHA} \
                                -t ${DOCKERHUB_NAMESPACE}/semantic-search-app-document:latest \
                                -f services/document_service/Dockerfile .
                            docker push ${DOCKERHUB_NAMESPACE}/semantic-search-app-document:${GIT_SHA}
                            docker push ${DOCKERHUB_NAMESPACE}/semantic-search-app-document:latest
                        """
                    }
                }
                stage('search-service') {
                    steps {
                        sh """
                            docker build \
                                -t ${DOCKERHUB_NAMESPACE}/semantic-search-app-search:${GIT_SHA} \
                                -t ${DOCKERHUB_NAMESPACE}/semantic-search-app-search:latest \
                                -f services/search_service/Dockerfile .
                            docker push ${DOCKERHUB_NAMESPACE}/semantic-search-app-search:${GIT_SHA}
                            docker push ${DOCKERHUB_NAMESPACE}/semantic-search-app-search:latest
                        """
                    }
                }
                stage('model-service') {
                    steps {
                        sh """
                            docker build \
                                --build-arg TRANSFORMERS_OFFLINE=0 \
                                --build-arg HF_DATASETS_OFFLINE=0 \
                                -t ${DOCKERHUB_NAMESPACE}/semantic-search-app-model:${GIT_SHA} \
                                -t ${DOCKERHUB_NAMESPACE}/semantic-search-app-model:latest \
                                -f services/model_service/Dockerfile .
                            docker push ${DOCKERHUB_NAMESPACE}/semantic-search-app-model:${GIT_SHA}
                            docker push ${DOCKERHUB_NAMESPACE}/semantic-search-app-model:latest
                        """
                    }
                }
            }
        }

        stage('Update Helm values') {
            steps {
                sh """
                    yq eval '.gateway.image.repository = "${DOCKERHUB_NAMESPACE}/semantic-search-app-gateway"' -i helm/values.yaml
                    yq eval '.gateway.image.tag = "${GIT_SHA}"' -i helm/values.yaml

                    yq eval '.documentService.image.repository = "${DOCKERHUB_NAMESPACE}/semantic-search-app-document"' -i helm/values.yaml
                    yq eval '.documentService.image.tag = "${GIT_SHA}"' -i helm/values.yaml

                    yq eval '.userService.image.repository = "${DOCKERHUB_NAMESPACE}/semantic-search-app-user"' -i helm/values.yaml
                    yq eval '.userService.image.tag = "${GIT_SHA}"' -i helm/values.yaml

                    yq eval '.searchService.image.repository = "${DOCKERHUB_NAMESPACE}/semantic-search-app-search"' -i helm/values.yaml
                    yq eval '.searchService.image.tag = "${GIT_SHA}"' -i helm/values.yaml

                    yq eval '.modelService.image.repository = "${DOCKERHUB_NAMESPACE}/semantic-search-app-model"' -i helm/values.yaml
                    yq eval '.modelService.image.tag = "${GIT_SHA}"' -i helm/values.yaml
                """
            }
        }

        stage('Commit and Push') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'github-credentials',
                    usernameVariable: 'GITHUB_USER',
                    passwordVariable: 'GITHUB_TOKEN'
                )]) {
                    sh """
                        git config user.email "jenkins@ci"
                        git config user.name "Jenkins"
                        git add helm/values.yaml
                        git diff --staged --quiet || git commit -m "ci: update image tags to ${GIT_SHA}"
                        git push https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${OWNER}/semantic-search-app.git HEAD:main
                    """
                }
            }
        }
    }

    post {
        always {
            sh 'docker logout || true'
            cleanWs()
        }
    }
}