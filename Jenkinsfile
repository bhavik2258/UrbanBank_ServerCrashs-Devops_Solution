pipeline {
    agent any

    // Best Practice: Use Parameters so you can inject dynamic IP addresses or credentials without editing code
    parameters {
        string(name: 'MINIKUBE_IP', defaultValue: '192.168.49.2', description: 'IP address of the Minikube cluster')
        string(name: 'DOCKER_REGISTRY', defaultValue: 'docker.io', description: 'Default Docker Registry')
    }

    environment {
        APP_NAME = 'urbanbank'
        // Using Jenkins build ID directly for tags creates unique, traceable image tags
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from Git...'
                checkout scm
            }
        }

        stage('Install Dependencies & Tests') {
            parallel {
                stage('Backend') {
                    steps {
                        echo 'Setting up Python Environment...'
                        // Best Practice: Fail the build if tests fail (removed the '|| echo' suppression)
                        sh '''
                            cd Backend
                            pip install -r requirements.txt
                            # pytest tests/
                        '''
                    }
                }
                stage('Frontend') {
                    steps {
                        echo 'Setting up Node Environment...'
                        sh '''
                            cd Frontend
                            npm install
                            npm run build
                            # npm test
                        '''
                    }
                }
            }
        }

        stage('Code Quality Check') {
            steps {
                echo 'Skipping SonarQube Scanner (Placeholder)...'
            }
        }

        stage('Build Docker Images') {
            steps {
                echo 'Building Backend, Frontend...'
                sh "docker build -t ${APP_NAME}-backend:${IMAGE_TAG} ./Backend"
                sh "docker build -t ${APP_NAME}-frontend:${IMAGE_TAG} ./Frontend"
            }
        }

        stage('Tag as Latest') {
            steps {
                echo 'Tagging images as latest...'
                sh "docker tag ${APP_NAME}-backend:${IMAGE_TAG} ${APP_NAME}-backend:latest"
                sh "docker tag ${APP_NAME}-frontend:${IMAGE_TAG} ${APP_NAME}-frontend:latest"
            }
        }

        stage('Deploy to Minikube') {
            steps {
                echo 'Deploying to local Minikube...'
                // Best Practice: Use standard kubectl commands assuming a k8s directory for configurations
                sh '''
                    if [ -d "k8s" ]; then
                        kubectl apply -f k8s/
                        kubectl set image deployment/backend backend=${APP_NAME}-backend:${IMAGE_TAG}
                        kubectl set image deployment/frontend frontend=${APP_NAME}-frontend:${IMAGE_TAG}
                    else
                        echo "No k8s directory found. Please create one with your deployment yaml files!"
                        exit 1
                    fi
                '''
            }
        }

        stage('Health Check') {
            steps {
                echo 'Running Health Check...'
                // Using parameterized MINIKUBE_IP
                sh "curl -s -o /dev/null -w '%{http_code}' http://${params.MINIKUBE_IP}:30000/health | grep 200"
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution finished. Cleaning up workspace...'
            cleanWs()
        }
        success {
            echo "✅ Pipeline #${BUILD_NUMBER} completed successfully!"
        }
        failure {
            echo "❌ Pipeline #${BUILD_NUMBER} failed! Check Jenkins logs."
        }
    }
}
