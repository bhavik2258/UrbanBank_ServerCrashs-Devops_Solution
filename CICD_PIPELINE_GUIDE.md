# UrbanBank CI/CD Pipeline - Complete Guide

## Overview
The Jenkins CI/CD pipeline automates the entire build, test, and deployment process for UrbanBank. It's a full-stack DevOps solution that connects development code to production-ready Kubernetes deployments.

## Pipeline Stages (In Order)

### 1. **Checkout** 📥
- **Purpose**: Fetch latest code from GitHub repository
- **Action**: `git clone` the project at the current commit
- **Duration**: ~5-10 seconds

### 2. **Install Dependencies** 📦
- **Backend**: 
  - Upgrade pip
  - Install Python packages from `requirements.txt` (FastAPI, SQLAlchemy, asyncpg, Prometheus, etc.)
  - Install dev tools: `ruff`, `pytest`
- **Frontend**: 
  - Install npm packages from `package.json`
- **Duration**: ~1-2 minutes (first time slower, cached on subsequent runs)

### 3. **Lint Code** 🔍
- **Backend**: Run `ruff check .` for Python code quality
- **Frontend**: Run `npm run lint` for TypeScript/ESLint checks
- **Purpose**: Catch syntax errors and style violations early
- **Failure**: Pipeline stops here if linting fails
- **Duration**: ~10-20 seconds

### 4. **Run Tests** ✅
- **Backend**: Run `pytest` for unit and integration tests
- **Frontend**: Run `npm test` for component/unit tests
- **Purpose**: Ensure code functionality is correct
- **Failure**: Pipeline stops if critical tests fail
- **Duration**: ~30-60 seconds

### 5. **Build Docker Images** 🐳
- **Builds two container images**:
  1. `urbanbank-backend:${BUILD_NUMBER}` (e.g., `:342`)
  2. `urbanbank-frontend:${BUILD_NUMBER}`
- **Using**: Dockerfiles in [Backend/Dockerfile](Backend/Dockerfile) and [Frontend/Dockerfile](Frontend/Dockerfile)
- **Purpose**: Package application with dependencies
- **Duration**: ~2-5 minutes (depends on cached layers)

### 6. **Tag Latest** 🏷️
- **Action**: Tag built images as `:latest` for easy reference
  - `urbanbank-backend:latest`
  - `urbanbank-frontend:latest`
- **Purpose**: Enable quick deployments without specifying version numbers
- **Duration**: ~1 second

### 7. **Load to Minikube** 📤
- **Action**: `minikube image load` - imports Docker images into Minikube's local registry
- **Why needed**: Minikube is isolated; images must be explicitly loaded
- **Duration**: ~30-60 seconds
- **Prerequisite**: Minikube must be running

### 8. **Deploy to Kubernetes** ⚙️
- **Action**: 
  - Apply kustomize manifests: `kubectl apply -k k8s/`
  - Creates all K8s resources (Deployments, Services, ConfigMaps, PVCs, etc.)
  - Updates backend and frontend deployments with new image versions
- **Resources deployed**:
  - Backend (3 replicas)
  - Frontend (2 replicas)
  - PostgreSQL database
  - Prometheus monitoring
  - Grafana dashboards
  - Postgres exporter
  - Pod Disruption Budgets
  - Horizontal Pod Autoscaler
  - Ingress rules
- **Duration**: ~20-30 seconds

### 9. **Wait for Rollout** ⏳
- **Action**: `kubectl rollout status` - waits for all pods to become Ready
- **Monitors**: 
  - backend deployment (max 180s)
  - frontend deployment (max 180s)
  - prometheus deployment (max 180s)
  - grafana deployment (max 180s)
- **Purpose**: Ensure new versions are running before health checks
- **Failure**: Pipeline stops if any deployment doesn't become ready
- **Duration**: ~1-3 minutes

### 10. **Health Check** 🏥
- **Checks**:
  - `GET /health` on backend (verifies API is responding)
  - `GET /metrics` on backend (verifies Prometheus endpoint works)
  - `GET /` on frontend (verifies web UI loads)
- **Purpose**: Smoke test that application is functional
- **Failure**: Pipeline stops if any check fails
- **Duration**: ~10-20 seconds

### 11. **Verify Metrics** 📊
- **Action**:
  - Port-forward Prometheus service
  - Query Prometheus API for active targets
  - Verify `urbanbank-backend` target is registered and scraping
- **Purpose**: Ensure monitoring is working end-to-end
- **Failure**: Pipeline stops if backend is not being monitored
- **Duration**: ~20-30 seconds (with retries)

## Post-Build Actions

### Success ✅
- Logs: `SUCCESS: UrbanBank pipeline #{BUILD_NUMBER}`

### Failure ❌
- Logs: `FAILURE: UrbanBank pipeline #{BUILD_NUMBER}`

### Always (Regardless of Result)
1. **Archive Artifacts** 📦
   - K8s manifests: `k8s/**/*.yaml`
   - Grafana dashboards: `grafana/**/*.json`
   - Frontend build: `Frontend/dist/**`
   - Enables rollback and audit trail

2. **Docker Image Cleanup** 🧹
   - Run `docker image prune` to remove dangling images
   - Remove old urbanbank images (keep only current and latest)
   - Prevents disk space issues

3. **Workspace Cleanup** 🗑️
   - Remove build workspace to save disk

## Key Features

### Fail-Fast Design
- Linting happens before testing
- Testing happens before building Docker images
- Prevents wasted time building images for broken code

### Fully Automated Deployment
- No manual kubectl commands needed
- One git push → complete deployment
- Repeatable and consistent

### End-to-End Validation
- Tests code quality (lint)
- Tests functionality (pytest, npm test)
- Tests containerization (builds)
- Tests orchestration (Kubernetes deployment)
- Tests observability (Prometheus metrics)

### Monitoring Integration
- Verifies Prometheus is scraping backend
- Ensures Grafana dashboards are provisioned
- Creates audit trail of deployments

## Environment Variables

Set in pipeline:
```
K8S_NAMESPACE = 'urbanbank'
BACKEND_DIR = 'Backend'
FRONTEND_DIR = 'Frontend'
```

Available during build:
- `${BUILD_NUMBER}` - Jenkins build number (e.g., 342)
- `${BUILD_ID}` - Build timestamp
- `${WORKSPACE}` - Build directory path

## Pipeline Options

```groovy
options {
    timeout(time: 1, unit: 'HOURS')      // Max 1 hour per build
    disableConcurrentBuilds()             // Only one build at a time
}
```

## Triggering Builds

### Manual Trigger
1. Click "Build Now" in Jenkins UI
2. or: `curl -X POST http://jenkins:8080/job/UrbanBank-Pipeline/build?delay=0sec`

### Automatic Trigger (via Webhook)
- GitHub webhook → triggers on every push
- Jenkins polls GitHub periodically (if configured)
- Pull requests can trigger builds (if configured)

## Current Status

### Infrastructure Requirements
To run complete pipeline successfully, you need:

✅ **Available Now:**
- Jenkins server (running)
- Docker (for building images)
- Git repository access

❌ **Missing for Full Pipeline Execution:**
- Minikube cluster (not running)
- kubectl configured to access Minikube
- Sufficient disk space for Docker images

### Build Failures (#1, #2)
Reason: Jenkins fetches Jenkinsfile from GitHub. Local fixes require:
1. Push changes to GitHub
2. Jenkins automatically re-fetches updated Jenkinsfile
3. Retry build

### Next Steps to Make It Work
1. Start Minikube: `minikube start`
2. Enable required addons:
   ```bash
   minikube addons enable ingress
   minikube addons enable metrics-server
   ```
3. Configure kubectl context to point to Minikube
4. Trigger new build

## Jenkins URL
- **Local**: http://localhost:8080
- **Job**: http://localhost:8080/job/UrbanBank-Pipeline/
- **Build Console**: http://localhost:8080/job/UrbanBank-Pipeline/1/console

## Docker-in-Docker (DinD)
- Jenkins runs in Docker container
- Docker daemon (DinD) inside separate container
- Allows building Docker images from Jenkins
- Network: `urbanbank_jenkins_network`

## Related Documentation
- [Jenkinsfile](Jenkinsfile) - Pipeline definition
- [PROJECT_IMPLEMENTATION_AND_DEVOPS.md](PROJECT_IMPLEMENTATION_AND_DEVOPS.md) - DevOps concepts
- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Project status
