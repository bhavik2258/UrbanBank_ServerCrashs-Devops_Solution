# UrbanBank Implementation Status

Last updated: 2026-04-27

## 1. Scope of this document
This file captures what is currently implemented in the UrbanBank codebase across:
- Application features (backend + frontend)
- Platform and DevOps tooling (Docker, Kubernetes, CI/CD, Ansible, monitoring)

## 2. Current architecture
- Frontend: React + TypeScript + Vite, served by Nginx in containerized environments.
- Backend: FastAPI + SQLAlchemy (async) + PostgreSQL.
- Observability: Prometheus + Grafana + Prometheus exporter for PostgreSQL.
- Deploy targets: Docker Compose (local stack) and Kubernetes (Minikube-oriented manifests).
- Automation: Jenkins pipeline and Ansible playbooks.

## 3. Application implementation (Backend)

### 3.1 API runtime and lifecycle
Implemented:
- FastAPI app with startup/lifespan initialization.
- Automatic DB table creation.
- Performance indexes on frequently queried fields.
- Initial data seeding for cooperative bank branches and baseline metrics.
- APScheduler background jobs for:
  - Periodic metric generation per branch.
  - Periodic auto-heal for critical branches.
- CORS configuration for local frontend origins.
- Prometheus instrumentation endpoint exposure.
- SSE stream endpoint for near-real-time dashboard updates.

Key endpoints implemented:
- GET /
- GET /health
- GET /dashboard/stream

### 3.2 Branch and simulation flows
Implemented:
- Branch listing endpoint with latest metric snapshot and computed uptime.
- Branch detail endpoint with latest state.
- Incident simulation endpoint to force a critical service-down scenario.
- Heal simulation endpoint to recover a branch and resolve open issues.

Key endpoints implemented:
- GET /branches
- GET /branches/{branch_id}
- POST /simulate/incident/{branch_id}
- POST /simulate/heal/{branch_id}

### 3.3 Metrics and dashboard APIs
Implemented:
- Latest metric for branch.
- Time-series metric history (latest 60 readings) for charting.
- Dashboard summary API (total branches, active alerts, incidents today, average uptime).
- Bank-ops KPI API with computed operational indicators:
  - Transaction success rate
  - Authentication failures (last hour)
  - Transfer p95 latency
  - Transfer error rate
  - ATM/POS/network uptime
  - DB replication lag estimate
  - Alert volume by branch and severity

Key endpoints implemented:
- GET /metrics/{branch_id}
- GET /metrics/{branch_id}/history
- GET /dashboard/summary
- GET /dashboard/bank-ops-kpis

### 3.4 Alerts and incidents APIs
Implemented:
- Alerts list with optional branch filter and limit.
- Active alerts endpoint.
- Alert resolve endpoint.
- Grafana webhook receiver endpoint.
- Paginated incidents endpoint.
- Branch-specific incidents endpoint.

Key endpoints implemented:
- GET /alerts
- GET /alerts/active
- PATCH /alerts/{alert_id}/resolve
- POST /alerts/webhooks/grafana
- GET /incidents
- GET /incidents/{branch_id}

### 3.5 Data model and domain behavior
Implemented entities:
- Branch
- Metric
- Alert
- Incident

Implemented domain behavior:
- Branch status transitions between healthy/warning/critical.
- Auto-generated warning alerts for high CPU/RAM/disk thresholds.
- Auto-resolution for recovered metric-based warning alerts.
- Incident creation on simulated failures.
- Incident resolution with downtime calculation on heal.
- Auto-heal processing of all critical branches in background cycle.

### 3.6 Backend observability instrumentation
Implemented custom metrics:
- branch_status_total (counter)
- branch_status_current (gauge)
- incident_created_total (counter)
- active_incidents (gauge)

Additional implementation:
- Startup refresh of active incident gauge.
- Startup refresh of branch status gauges.

## 4. Application implementation (Frontend)

### 4.1 App shell and routing
Implemented:
- Protected routing with login gate.
- Public login route.
- Lazy-loaded pages and suspense fallback.
- Shared navbar + theme toggle.

Implemented pages:
- Login
- Dashboard
- Branch Detail
- Alerts
- Incidents
- Not Found

### 4.2 Auth and role model
Implemented:
- Session-based authentication stored in sessionStorage.
- In-app directory users with predefined credentials.
- Role labels and permission checks.
- Roles:
  - platform_admin
  - operations_analyst
  - auditor (read-only)
- Permission-gated actions for simulation/heal/export/manage-account paths.

### 4.3 Dashboard UX and data behavior
Implemented:
- Dashboard summary cards.
- Bank selector and tenant-oriented branch filtering.
- Branch card operations for simulate failure and trigger heal.
- Bank operations KPI cards.
- Alert volume table by branch/severity.
- Incremental branch rendering with Show More pagination behavior.
- Real-time refresh using SSE with polling fallback.

### 4.4 Branch detail UX
Implemented:
- Branch metadata and live metric gauges.
- Services status pills.
- Historical metrics chart.
- Branch-scoped recent alerts table.
- Branch-scoped incident timeline.

### 4.5 Alerts and incidents UX
Implemented:
- Alerts page with filters:
  - Branch
  - Severity
  - Status (active/resolved)
- Incidents page with:
  - Search/filter
  - Auto-heal status badges
  - Ansible action visibility
  - CSV export interaction (permission-gated UI path)

### 4.6 Account settings UX
Implemented:
- Account settings dialog in navbar profile menu.
- User profile display (name/email/role).
- Notification preference toggles.
- Preference persistence in localStorage keyed by user email.

## 5. DevOps and platform tooling

### 5.1 Docker and local stack
Implemented:
- Multi-service Docker Compose stack for:
  - PostgreSQL
  - Backend
  - Frontend
  - Prometheus
  - Grafana
  - PostgreSQL exporter
- Health checks and startup dependencies.
- Persistent volumes for DB, Prometheus, and Grafana.

### 5.2 Local developer startup script
Implemented:
- start-dev.sh to boot local services:
  - Docker services: DB, Prometheus, Grafana
  - Backend via uvicorn (local venv)
  - Frontend via npm run dev
- Graceful cleanup on SIGINT/SIGTERM.

### 5.3 Container build definitions
Implemented:
- Backend Dockerfile (Python 3.11 slim, uvicorn runtime).
- Frontend multi-stage Dockerfile (Node build -> Nginx runtime).
- Nginx config with SPA fallback and /api proxy to backend.

### 5.4 Kubernetes deployment stack
Implemented with kustomize:
- Namespace, configmap, secret.
- Deployments/services for backend, frontend, postgres, prometheus, grafana, postgres-exporter.
- PersistentVolumeClaims for postgres/prometheus/grafana.
- PodDisruptionBudgets for backend/frontend/postgres.
- HorizontalPodAutoscaler for backend (CPU+memory based).
- Ingress resources for frontend and /api routing with rewrite.

### 5.5 CI/CD pipeline (Jenkins)
Implemented Jenkinsfile stages:
- Checkout
- Install Dependencies
- Lint Code (ruff + frontend lint)
- Run Tests (pytest + npm test)
- Build Docker Images
- Tag Latest
- Load to Minikube
- Deploy to Kubernetes
- Wait for Rollout
- Health Check
- Verify Metrics target in Prometheus

Post actions implemented:
- Artifact archive
- Docker image cleanup
- Workspace cleanup

Also present:
- Dedicated Jenkins + DinD docker compose setup for local Jenkins environment.

### 5.6 Ansible automation
Implemented playbooks:
- setup_infrastructure.yml
  - Installs required packages
  - Starts Docker
  - Installs/starts Minikube
  - Enables ingress + metrics-server
- deploy_app.yml
  - Builds backend/frontend images
  - Loads images into Minikube
  - Applies k8s kustomize manifests
  - Waits for rollout and prints frontend URL
- setup_monitoring.yml
  - Installs Helm-based monitoring stack
  - Creates Grafana admin secret
  - Adds FastAPI scrape target and dashboard
- rollback.yml
  - Rolls back backend/frontend deployments
  - Waits for rollback status and validates backend health
- teardown.yml
  - Deletes namespace/resources
  - Optionally removes images and stops Minikube

## 6. Monitoring and alerting implementation

### 6.1 Prometheus
Implemented:
- Scrape jobs for backend and postgres exporter in Docker setup.
- Kubernetes Prometheus config with backend and postgres targets.

### 6.2 Grafana dashboards
Implemented:
- Provisioned datasource and dashboard provider.
- UrbanBank dashboard JSON provisioned in both Docker and k8s flow.
- Panels for:
  - Branch health counts
  - Incident rates/active incidents
  - API traffic/latency/errors
  - Infra resource trends
  - PostgreSQL activity metrics

### 6.3 Grafana alerting
Implemented:
- Provisioned contact point: UrbanBank Webhook.
- Notification policy routing to webhook.
- Alert rule group for critical conditions, including:
  - Backend down
  - Postgres exporter down
  - High HTTP 5xx rate
  - Active incidents spike
  - Request rate drop
- Webhook target wired to backend endpoint:
  - POST /alerts/webhooks/grafana

## 7. Testing and quality status
Implemented:
- Frontend linting and test scripts in package.json.
- Example Vitest test scaffold.
- Playwright config/fixture scaffold for E2E extension.
- Backend test command integrated in Jenkins pipeline.

Current status note:
- Frontend automated tests are scaffolded but minimal.

## 8. Notable current limitations
- Settings preferences are frontend-local only (no backend settings API).
- Login and role directory are static/in-app (no external IAM integration).
- Alert webhook endpoint currently logs payload and acknowledges receipt.

## 9. Primary implementation files (quick reference)
- Backend app and APIs:
  - Backend/main.py
  - Backend/routers/branches.py
  - Backend/routers/metrics.py
  - Backend/routers/alerts.py
  - Backend/routers/incidents.py
  - Backend/crud.py
  - Backend/models.py
  - Backend/schemas.py
  - Backend/prometheus_metrics.py
- Frontend app and pages:
  - Frontend/src/App.tsx
  - Frontend/src/api/api.ts
  - Frontend/src/pages/Login.tsx
  - Frontend/src/pages/Dashboard.tsx
  - Frontend/src/pages/BranchDetail.tsx
  - Frontend/src/pages/Alerts.tsx
  - Frontend/src/pages/Incidents.tsx
  - Frontend/src/lib/auth.ts
  - Frontend/src/components/SettingsDialog.tsx
- DevOps and infra:
  - docker-compose.yml
  - docker-compose.jenkins.yml
  - Jenkinsfile
  - start-dev.sh
  - ansible/*.yml
  - k8s/*.yaml
  - prometheus/prometheus.yml
  - grafana/urbanbank-dashboard.json
  - grafana/provisioning/**/*
