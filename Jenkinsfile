pipeline {
    agent any

    environment {
        POSTGRES_USER = 'admin'
        POSTGRES_PASSWORD = 'password123'
        POSTGRES_DB = 'project_db_test'
        POSTGRES_HOST = 'postgres-test'
        POSTGRES_PORT = '5432'
        DATABASE_URL = "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
    }

    stages {

        stage('Debug Docker env') {
            steps {
                sh '''
                    echo "DOCKER_HOST=$DOCKER_HOST"
                    echo "DOCKER_CERT_PATH=$DOCKER_CERT_PATH"
                    echo "DOCKER_TLS_VERIFY=$DOCKER_TLS_VERIFY"
                    which docker
                    docker version
                    ls -la /certs/client/ 2>/dev/null || echo "No certs dir"
                '''
            }
        }

        stage("Checkout") {
            steps {
                script {
                    // Start Postgres container for tests
                    sh '''
                        docker run -d \
                            --name postgres-test \
                            --network host \
                            -e POSTGRES_USER=${POSTGRES_USER} \
                            -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
                            -e POSTGRES_DB=${POSTGRES_DB} \
                            -p 5432:5432 \
                            postgres:15
                        
                        # Wait for Postgres to be ready
                        until docker exec postgres-test pg_isready -U ${POSTGRES_USER}; do
                            echo "Waiting for postgres..."
                            sleep 2
                        done
                    '''
                }
            }
        }

        stage("Install uv") {
            steps {
                sh '''
                    curl -LsSf https://astral.sh/uv/install.sh | sh
                    export PATH="$HOME/.local/bin:$PATH"
                    uv --version
                '''
            }
        }

        stage("Set up Python") {
            steps {
                sh '''
                    export PATH="$HOME/.local/bin:$PATH"
                    uv python install 3.11
                '''
            }
        }

        stage('Install dependencies') {
            steps {
                sh '''
                    export PATH="$HOME/.local/bin:$PATH"
                    uv sync --package search_service --package semantic_search_app --group dev
                '''
            }
        }

        stage('Run tests') {
            steps {
                sh '''
                    export PATH="$HOME/.local/bin:$PATH"
                    export DATABASE_URL=${DATABASE_URL}
                    uv run pytest services/search_service/tests -v
                '''
            }
        }
    }

    post {
        always {
            // Cleanup: stop and remove Postgres container
            sh '''
                docker stop postgres-test || true
                docker rm postgres-test || true
            '''
            cleanWs()
        }
    }
}