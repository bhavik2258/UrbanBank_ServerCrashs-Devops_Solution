# UrbanBank CI/CD Pipeline - Live Setup Summary

## 🎯 Current Status

### ✅ Running Services
- **Jenkins Server** - http://localhost:8080 (LTS)
- **Jenkins Docker-in-Docker (DinD)** - Enables building Docker images
- **UrbanBank Backend** - http://localhost:8000 (FastAPI)
- **Prometheus** - http://localhost:9090 (Metrics collection)
- **Grafana** - http://localhost:3001 (Dashboards, credentials: admin/admin)
- **PostgreSQL Exporter** - http://localhost:9187 (DB metrics)

### ❌ Not Running (Needed for Full Pipeline)
- **Minikube** - Local Kubernetes cluster
- **kubectl** - Kubernetes CLI access

---

## 📊 Complete CI/CD Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────────┐
│                     UrbanBank CI/CD Pipeline                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. CHECKOUT          - Pull code from GitHub                     │
│     ↓                                                               │
│  2. INSTALL DEPS      - pip install, npm install                  │
│     ↓                                                               │
│  3. LINT CODE         - ruff (Python), eslint (TypeScript)         │
│     ↓                                                               │
│  4. RUN TESTS         - pytest (backend), npm test (frontend)      │
│     ↓                                                               │
│  5. BUILD IMAGES      - docker build backend, frontend images      │
│     ↓                                                               │
│  6. TAG LATEST        - tag as :latest for easy access             │
│     ↓                                                               │
│  7. LOAD TO MINIKUBE  - minikube image load                        │
│     ↓                                                               │
│  8. DEPLOY TO K8S     - kubectl apply kustomize manifests          │
│     ↓                                                               │
│  9. WAIT FOR ROLLOUT  - kubectl rollout status (timeout: 180s)     │
│     ↓                                                               │
│ 10. HEALTH CHECK      - /health, /metrics, frontend curl           │
│     ↓                                                               │
│ 11. VERIFY METRICS    - Check Prometheus is scraping backend       │
│     ↓                                                               │
│ 12. SUCCESS/FAILURE   - Build result logged                        │
│     ↓                                                               │
│ 13. ARCHIVE           - Save K8s yamls, Grafana dashboards         │
│     ↓                                                               │
│ 14. CLEANUP           - Docker prune, workspace cleanup            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔗 Quick Access Links

| Service | URL | Credentials |
|---------|-----|-------------|
| **Jenkins** | http://localhost:8080 | No auth by default |
| **Backend API** | http://localhost:8000 | None |
| **Backend Health** | http://localhost:8000/health | - |
| **Backend Metrics** | http://localhost:8000/metrics | - |
| **Prometheus** | http://localhost:9090 | None |
| **Grafana** | http://localhost:3001 | admin / admin |
| **UrbanBank Job** | http://localhost:8080/job/UrbanBank-Pipeline/ | - |

---

## 🏗️ Architecture

```
                              GitHub Repository
                                     ↓
                          ┌──────────────────┐
                          │  Webhook Trigger │
                          └──────────────────┘
                                     ↓
                          ┌──────────────────────────┐
                          │   Jenkins (Port 8080)    │
                          │  + Docker-in-Docker      │
                          └──────────────────────────┘
                                     ↓
                    ┌────────────────────────────────┐
                    │  Build Docker Images           │
                    │  - urbanbank-backend:latest    │
                    │  - urbanbank-frontend:latest   │
                    └────────────────────────────────┘
                                     ↓
                    ┌────────────────────────────────┐
                    │  Minikube Kubernetes Cluster   │
                    │  (When available)              │
                    └────────────────────────────────┘
                                     ↓
                    ┌────────────────────────────────┐
                    │  Running UrbanBank Application │
                    │  + Prometheus Monitoring       │
                    │  + Grafana Dashboards          │
                    └────────────────────────────────┘
```

---

## 🔄 How CI/CD Works

### When You Push Code to GitHub:
1. **Developer** → `git push origin main`
2. **GitHub** → Sends webhook to Jenkins
3. **Jenkins** → Detects the Jenkinsfile in repository
4. **Pipeline Starts** → Executes all 11 stages automatically
5. **Result** → Application deployed to Minikube (if successful)

### What Each Stage Does:

| Stage | Function | Success Criteria |
|-------|----------|------------------|
| Checkout | Gets latest code | Code cloned |
| Install Deps | Installs requirements | No errors |
| Lint | Checks code style | No violations |
| Tests | Runs unit tests | Tests pass |
| Build Images | Creates Docker containers | Images built |
| Tag Latest | Names images | Tags applied |
| Load Minikube | Imports to Minikube | Minikube can use images |
| Deploy K8s | Applies manifests | Resources created |
| Rollout Wait | Checks pod readiness | All pods Running |
| Health Check | Tests endpoints | Services respond |
| Verify Metrics | Checks monitoring | Prometheus scraping |

---

## 🚀 To Run a Successful Build:

### Step 1: Start Minikube
```bash
minikube start --driver=docker
```

### Step 2: Enable Required Addons
```bash
minikube addons enable ingress
minikube addons enable metrics-server
```

### Step 3: Configure kubectl
```bash
# Verify kubectl points to Minikube
kubectl config use-context minikube
kubectl get nodes  # Should show minikube node
```

### Step 4: Trigger Build
```bash
# Via Jenkins UI: Click "Build Now"
# OR via CLI:
curl -X POST http://localhost:8080/job/UrbanBank-Pipeline/build?delay=0sec
```

### Step 5: Watch Pipeline
```bash
# Option A: Web UI
open http://localhost:8080/job/UrbanBank-Pipeline/

# Option B: Check last build console
kubectl logs -f $(kubectl get pods -n urbanbank -o name | head -1)
```

---

## 📋 Pipeline Features

### ✅ Fail-Fast Architecture
- Code is linted **before** building Docker images
- Tests run **before** containerization
- Early failures prevent wasted time

### ✅ Fully Automated Deployment
- One command: `git push`
- Full deployment to Kubernetes
- No manual kubectl commands needed

### ✅ End-to-End Validation
- ✓ Code quality (lint)
- ✓ Functionality (tests)
- ✓ Containerization (Docker)
- ✓ Orchestration (Kubernetes)
- ✓ Observability (Prometheus)

### ✅ Monitoring Integration
- Verifies Prometheus scrapes backend
- Ensures metrics endpoint works
- Grafana dashboards automatically configured

### ✅ Rollback Support
- Artifacts archived automatically
- Previous builds remain accessible
- Easy to revert to prior version

---

## 🛠️ Pipeline Configuration

### Timeout
- Maximum 1 hour per build
- Fails if exceeds timeout

### Concurrency
- Only one build runs at a time
- Prevents resource conflicts

### Cleanup
- Docker images pruned after build
- Workspace deleted to save disk
- K8s artifacts archived before cleanup

---

## 📊 Kubernetes Resources Deployed

When pipeline reaches "Deploy to Kubernetes" stage, the following resources are created in the `urbanbank` namespace:

```
Deployments:
- backend         (3 replicas, auto-scales 2-10 based on CPU/Memory)
- frontend        (2 replicas)
- postgres        (1 replica)
- prometheus      (1 replica)
- grafana         (1 replica)
- postgres-exporter (1 replica)

Services:
- backend, frontend, postgres, prometheus, grafana, postgres-exporter

PersistentVolumeClaims:
- postgres-pvc, prometheus-storage, grafana-storage

ConfigMaps:
- urbanbank-config, prometheus-config, grafana configs

Pod Disruption Budgets:
- backend-pdb, frontend-pdb, postgres-pdb

HorizontalPodAutoscaler:
- backend-hpa (scales 2-10 based on metrics)

Ingress:
- Routes /api to backend
- Routes / to frontend
```

---

## 🔍 Monitoring the Pipeline

### Jenkins Web UI
- http://localhost:8080/job/UrbanBank-Pipeline/1/console
- Shows real-time console output
- Color-coded logs (errors in red)

### Docker Logs
```bash
docker compose -f docker-compose.jenkins.yml logs -f jenkins
```

### Backend Health
```bash
curl http://localhost:8000/health
```

### Metrics in Prometheus
```bash
# Visit Prometheus UI
open http://localhost:9090

# Query: up{job="urbanbank-backend"} should return 1 (healthy)
```

### Grafana Dashboard
```bash
# Visit Grafana
open http://localhost:3001
# Login: admin / admin
# Dashboard: UrbanBank (auto-provisioned)
```

---

## 🐛 Troubleshooting

### Build Fails at "Load to Minikube"
- **Issue**: Minikube not running
- **Fix**: `minikube start --driver=docker`

### Build Fails at "Deploy to Kubernetes"
- **Issue**: kubectl not configured
- **Fix**: `kubectl config use-context minikube`

### Build Fails at "Wait for Rollout"
- **Issue**: Pods not becoming Ready
- **Fix**: `kubectl logs -n urbanbank <pod-name>`

### Build Fails at "Health Check"
- **Issue**: Backend service not accessible
- **Fix**: `kubectl port-forward -n urbanbank svc/backend 8000:8000`

### Build Fails at "Verify Metrics"
- **Issue**: Prometheus not scraping
- **Fix**: Check Prometheus targets: http://localhost:9090/targets

---

## 📝 Files Reference

| File | Purpose |
|------|---------|
| [Jenkinsfile](Jenkinsfile) | Pipeline definition |
| [docker-compose.jenkins.yml](docker-compose.jenkins.yml) | Jenkins + DinD stack |
| [k8s/](k8s/) | Kubernetes manifests |
| [prometheus/](prometheus/) | Prometheus config |
| [grafana/](grafana/) | Grafana dashboards |

---

## 🎓 Learning Resources

- [Jenkins Pipeline Syntax](https://jenkins.io/doc/pipeline/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)

---

**Created**: 2026-04-28
**Pipeline Status**: Ready (waiting for Minikube)
**Last Updated**: When Jenkinsfile changes are pushed
