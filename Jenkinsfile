pipeline {
    // Force the pipeline to run ONLY on the Docker-in-Docker agent node
    agent { 
        label 'docker-agent' 
    }

    environment {
        APP_NAME = 'urbanbank'
        IMAGE_TAG = "${BUILD_NUMBER}"
        // Set paths assuming the repo is checked out
    }

    stages {
        stage('Clone Repository') {
            steps {
                echo 'Checking out code from GitHub...'
                checkout scm
            }
        }

        stage('Install & Test') {
            parallel {
                stage('Backend (Python)') {
                    steps {
                        echo 'Testing Python Backend...'
                        sh '''
                            cd Backend
                            pip install -r requirements.txt
                            # pytest tests/  # Uncomment when tests are written
                        '''
                    }
                }
                stage('Frontend (React)') {
                    steps {
                        echo 'Testing React Frontend...'
                        sh '''
                            cd Frontend
                            npm install
                            npm run build
                            # npm test      # Uncomment when tests are written
                        '''
                    }
                }
            }
        }

        stage('Build Docker Images') {
            steps {
                echo 'Building Docker Images...'
                sh "docker build -t ${APP_NAME}-backend:${IMAGE_TAG} ./Backend"
                sh "docker build -t ${APP_NAME}-frontend:${IMAGE_TAG} ./Frontend"
            }
        }

        stage('Deploy / Restart') {
            steps {
                echo 'Deploying application locally via Docker Compose...'
                // Since this runs on the agent with docker access, we can deploy it directly
                sh 'docker compose down || true'
                sh 'docker compose up -d --build'
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo "✅ UrbanBank Pipeline #${BUILD_NUMBER} completed successfully!"
        }
        failure {
            echo "❌ UrbanBank Pipeline #${BUILD_NUMBER} failed!"
        }
    }
}
