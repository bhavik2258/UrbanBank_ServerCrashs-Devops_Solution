pipeline {
    agent any

    options {
        timeout(time: 1, unit: 'HOURS')
        disableConcurrentBuilds()
    }

    environment {
        K8S_NAMESPACE = 'urbanbank'
        BACKEND_DIR = 'Backend'
        FRONTEND_DIR = 'Frontend'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    set -e
                    cd "$BACKEND_DIR"
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt ruff pytest
                    cd ../"$FRONTEND_DIR"
                    npm install
                '''
            }
        }

        stage('Lint Code') {
            steps {
                sh '''
                    set -e
                    cd "$BACKEND_DIR"
                    ruff check .
                    cd ../"$FRONTEND_DIR"
                    npm run lint
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    set -e
                    cd "$BACKEND_DIR"
                    pytest -q || test $? -eq 5
                    cd ../"$FRONTEND_DIR"
                    npm test
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                    set -e
                    docker build -t urbanbank-backend:${BUILD_NUMBER} ./$BACKEND_DIR
                    docker build -t urbanbank-frontend:${BUILD_NUMBER} ./$FRONTEND_DIR
                '''
            }
        }

        stage('Tag Latest') {
            steps {
                sh '''
                    docker tag urbanbank-backend:${BUILD_NUMBER} urbanbank-backend:latest
                    docker tag urbanbank-frontend:${BUILD_NUMBER} urbanbank-frontend:latest
                '''
            }
        }

        stage('Load to Minikube') {
            steps {
                sh '''
                    minikube image load urbanbank-backend:${BUILD_NUMBER}
                    minikube image load urbanbank-frontend:${BUILD_NUMBER}
                '''
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh '''
                    set -e
                    kubectl apply -f k8s/ || {
                      find k8s -name '*.yaml' ! -name 'kustomization.yaml' -print0 | xargs -0 -n1 kubectl apply -f
                    }
                    kubectl set image deployment/backend backend=urbanbank-backend:${BUILD_NUMBER} -n $K8S_NAMESPACE
                    kubectl set image deployment/frontend frontend=urbanbank-frontend:${BUILD_NUMBER} -n $K8S_NAMESPACE
                '''
            }
        }

        stage('Wait for Rollout') {
            steps {
                sh '''
                    kubectl rollout status deployment/backend -n $K8S_NAMESPACE --timeout=180s
                    kubectl rollout status deployment/frontend -n $K8S_NAMESPACE --timeout=180s
                    kubectl rollout status deployment/prometheus -n $K8S_NAMESPACE --timeout=180s
                    kubectl rollout status deployment/grafana -n $K8S_NAMESPACE --timeout=180s
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    set -e
                    BACKEND_URL=$(minikube service backend --url -n $K8S_NAMESPACE | head -n 1)
                    FRONTEND_URL=$(minikube service frontend --url -n $K8S_NAMESPACE | head -n 1)
                    curl -fsS "$BACKEND_URL/health"
                    curl -fsS "$BACKEND_URL/metrics" >/dev/null
                    curl -fsS "$FRONTEND_URL" >/dev/null
                '''
            }
        }

        stage('Verify Metrics') {
            steps {
                sh '''
                    set -e
                    kubectl -n $K8S_NAMESPACE port-forward svc/prometheus 19090:9090 >/tmp/prometheus-pf.log 2>&1 &
                    PF_PID=$!
                    trap 'kill $PF_PID 2>/dev/null || true' EXIT
                    python - <<'PY'
import json
import sys
import time
from urllib.request import urlopen

url = "http://127.0.0.1:19090/api/v1/targets"
for _ in range(20):
    try:
        payload = json.loads(urlopen(url, timeout=2).read().decode())
        active = payload.get("data", {}).get("activeTargets", [])
        if any("urbanbank-backend" in t.get("labels", {}).get("job", "") for t in active):
            print("Prometheus target urbanbank-backend is active")
            sys.exit(0)
    except Exception:
        pass
    time.sleep(1)
sys.exit("Prometheus target urbanbank-backend not found")
PY
                '''
            }
        }
    }

    post {
        success {
            echo "SUCCESS: UrbanBank pipeline #${BUILD_NUMBER}"
        }
        failure {
            echo "FAILURE: UrbanBank pipeline #${BUILD_NUMBER}"
        }
        always {
            archiveArtifacts artifacts: 'k8s/**/*.yaml,grafana/**/*.json,Frontend/dist/**', allowEmptyArchive: true, fingerprint: true
            sh '''
                docker image prune -f || true
                docker images --format '{{.Repository}}:{{.Tag}}' | grep '^urbanbank-' | grep -v ':latest$' | grep -v ":${BUILD_NUMBER}$" | xargs -r docker rmi || true
            '''
            cleanWs()
        }
    }
}
 
