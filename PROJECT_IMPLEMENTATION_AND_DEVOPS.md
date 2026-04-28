# UrbanBank Project Implementation and DevOps Guide

Last updated: 2026-04-28

This document describes what is currently implemented across the UrbanBank repository and explains the DevOps concepts used in the project in practical terms.

## 1. What Is Implemented

### 1.1 Backend application

The backend is a FastAPI service with async SQLAlchemy and PostgreSQL. It implements:

- Application startup and shutdown via FastAPI lifespan hooks.
- Database initialization and table creation on startup.
- Background scheduling for metric collection and auto-healing jobs.
- Seed data generation for branches and baseline operational state.
- CORS for local frontend development.
- Prometheus instrumentation and metrics exposure.
- Server-Sent Events stream for dashboard updates.

Implemented backend API areas:

- Root and health endpoints.
- Branch listing and branch detail APIs.
- Metric snapshot and time-series history APIs.
- Alert listing, filtering, and resolution APIs.
- Incident listing and branch-specific incident APIs.
- Simulation endpoints for creating and healing failures.
- Grafana webhook endpoint for alert ingestion.

Relevant files:

- [Backend/main.py](Backend/main.py)
- [Backend/crud.py](Backend/crud.py)
- [Backend/models.py](Backend/models.py)
- [Backend/routers/branches.py](Backend/routers/branches.py)
- [Backend/routers/metrics.py](Backend/routers/metrics.py)
- [Backend/routers/alerts.py](Backend/routers/alerts.py)
- [Backend/routers/incidents.py](Backend/routers/incidents.py)
- [Backend/prometheus_metrics.py](Backend/prometheus_metrics.py)

### 1.2 Frontend application

The frontend is a React + TypeScript + Vite app. It implements:

- Login-gated navigation.
- Dashboard, branch detail, alerts, and incidents pages.
- KPI cards and operational summary widgets.
- Historical charts and live status indicators.
- User settings dialog with persisted preferences.
- Theme switching and responsive layout behavior.
- Data fetching through a centralized API layer.

Relevant files:

- [Frontend/src/App.tsx](Frontend/src/App.tsx)
- [Frontend/src/api/api.ts](Frontend/src/api/api.ts)
- [Frontend/src/pages/Dashboard.tsx](Frontend/src/pages/Dashboard.tsx)
- [Frontend/src/pages/BranchDetail.tsx](Frontend/src/pages/BranchDetail.tsx)
- [Frontend/src/pages/Alerts.tsx](Frontend/src/pages/Alerts.tsx)
- [Frontend/src/pages/Incidents.tsx](Frontend/src/pages/Incidents.tsx)
- [Frontend/src/components/SettingsDialog.tsx](Frontend/src/components/SettingsDialog.tsx)
- [Frontend/src/lib/auth.ts](Frontend/src/lib/auth.ts)

### 1.3 Monitoring and observability

The project includes monitoring and observability for application and database health:

- Prometheus scraping for backend and PostgreSQL exporter targets.
- Grafana dashboards provisioned from files.
- Grafana alerting configured with a webhook contact point.
- PostgreSQL exporter for database metrics.
- Custom backend metrics for branch and incident state.

Relevant files:

- [prometheus/prometheus.yml](prometheus/prometheus.yml)
- [grafana/urbanbank-dashboard.json](grafana/urbanbank-dashboard.json)
- [grafana/provisioning](grafana/provisioning)
- [Backend/prometheus_metrics.py](Backend/prometheus_metrics.py)

### 1.4 Docker and local development

The project supports a local multi-service stack using Docker Compose:

- PostgreSQL database.
- Backend API.
- Frontend web server.
- Prometheus.
- Grafana.
- PostgreSQL exporter.

It also includes a local startup script that launches the stack and handles cleanup.

Relevant files:

- [docker-compose.yml](docker-compose.yml)
- [start-dev.sh](start-dev.sh)
- [Backend/Dockerfile](Backend/Dockerfile)
- [Frontend/Dockerfile](Frontend/Dockerfile)
- [Frontend/nginx.conf](Frontend/nginx.conf)

### 1.5 Kubernetes deployment

The repository contains a Kubernetes deployment stack with kustomize-based manifests:

- Namespace and shared config.
- Backend, frontend, PostgreSQL, Prometheus, Grafana, and exporter workloads.
- Services and ingress routing.
- Persistent volume claims for stateful components.
- PodDisruptionBudgets for availability.
- HorizontalPodAutoscaler for backend scaling.

Relevant files:

- [k8s/kustomization.yaml](k8s/kustomization.yaml)
- [k8s/backend-deployment.yaml](k8s/backend-deployment.yaml)
- [k8s/frontend-deployment.yaml](k8s/frontend-deployment.yaml)
- [k8s/postgres-deployment.yaml](k8s/postgres-deployment.yaml)
- [k8s/prometheus-deployment.yaml](k8s/prometheus-deployment.yaml)
- [k8s/grafana-deployment.yaml](k8s/grafana-deployment.yaml)
- [k8s/ingress.yaml](k8s/ingress.yaml)

### 1.6 CI/CD and automation

The repo includes CI/CD and automation assets for building, testing, deploying, and rolling back the application:

- Jenkins pipeline with lint, test, build, deploy, health-check, and metrics-verification stages.
- Docker image build and tag flow.
- Kubernetes deployment and rollout validation.
- Ansible playbooks for setup, deployment, monitoring, rollback, and teardown.

Relevant files:

- [Jenkinsfile](Jenkinsfile)
- [ansible/setup_infrastructure.yml](ansible/setup_infrastructure.yml)
- [ansible/deploy_app.yml](ansible/deploy_app.yml)
- [ansible/setup_monitoring.yml](ansible/setup_monitoring.yml)
- [ansible/rollback.yml](ansible/rollback.yml)
- [ansible/teardown.yml](ansible/teardown.yml)

## 2. DevOps Concepts Explained Using This Project

### 2.1 DevOps in plain terms

DevOps is the practice of connecting software development and operations so that software can be built, tested, deployed, observed, and recovered in a repeatable way. In this repository, DevOps is not just a diagram or a slogan; it is implemented through Docker, Kubernetes, Jenkins, Ansible, Prometheus, and Grafana.

The main goal is to reduce the gap between code and production-like operations:

- Developers can run the app locally in a consistent environment.
- Automation can build and test the app the same way every time.
- Deployment can be repeated without manual hand-holding.
- Monitoring can show whether the system is healthy after deployment.

### 2.2 Infrastructure as Code

Infrastructure as Code means infrastructure is described in files instead of being configured manually through a console or ad hoc shell commands.

How it appears here:

- Docker Compose defines local services in [docker-compose.yml](docker-compose.yml).
- Kubernetes resources are declared in [k8s/](k8s).
- Ansible playbooks describe setup and deployment workflows in [ansible/](ansible).
- Prometheus and Grafana are configured from versioned files in [prometheus/](prometheus) and [grafana/](grafana).

Why it matters:

- The environment becomes reproducible.
- Changes are reviewable in Git.
- Deployment behavior can be traced back to code.
- New team members can understand the stack faster.

### 2.3 Containerization

Containerization packages an application and its runtime dependencies into an isolated unit. That reduces the classic problem of "it works on my machine".

How it appears here:

- The backend is built into a container using [Backend/Dockerfile](Backend/Dockerfile).
- The frontend is built into a container using [Frontend/Dockerfile](Frontend/Dockerfile).
- Nginx serves the frontend and proxies API calls in [Frontend/nginx.conf](Frontend/nginx.conf).
- Docker Compose launches the whole local stack with one command.

Why it matters:

- The backend runtime, dependencies, and entrypoint are fixed.
- The frontend build output is separated from the development environment.
- Local development becomes closer to deployment behavior.
- Teams can run the same service image in Docker Compose, Kubernetes, or CI.

### 2.4 Service orchestration

Service orchestration means managing multiple cooperating services so they start in the right order and can talk to each other reliably.

How it appears here:

- PostgreSQL starts before the backend.
- Prometheus depends on backend and exporter targets.
- Grafana depends on Prometheus.
- The backend connects to PostgreSQL through Docker network DNS instead of localhost.

Relevant implementation:

- [docker-compose.yml](docker-compose.yml)
- [k8s/kustomization.yaml](k8s/kustomization.yaml)

Why it matters:

- The app is not a single process; it is a system of services.
- Orchestration coordinates dependencies.
- Health checks reduce startup race conditions.
- A failed service can be restarted or rescheduled by the platform.

### 2.5 Configuration management

Configuration management means separating code from environment-specific values.

How it appears here:

- Backend connection and secret values are injected through environment variables in Docker Compose and Kubernetes.
- Frontend API base URL is read from environment in [Frontend/src/api/api.ts](Frontend/src/api/api.ts).
- Prometheus and Grafana use file-based provisioning.

Why it matters:

- The same code can run in different environments.
- Sensitive values do not need to be hardcoded.
- Development, test, and production settings can differ safely.

### 2.6 Secret management

Secret management is the discipline of storing credentials outside source code.

How it appears here:

- PostgreSQL credentials are provided via environment variables.
- Grafana admin credentials are defined through container environment variables.
- Kubernetes uses a [k8s/secret.yaml](k8s/secret.yaml) resource.

Why it matters:

- Secrets should not be committed directly into app code.
- Different environments can use different credentials.
- Secret rotation becomes possible without code changes.

### 2.7 Continuous Integration

Continuous Integration means code changes are automatically validated after they are committed.

How it appears here in [Jenkinsfile](Jenkinsfile):

- Backend dependencies are installed.
- Frontend dependencies are installed.
- Backend linting runs with Ruff.
- Frontend linting runs with ESLint.
- Tests run for both layers.

Why it matters:

- Problems are caught earlier.
- Regressions are detected before deployment.
- Quality gates are consistent across contributors.

### 2.8 Continuous Delivery and deployment

Continuous Delivery means the application can be packaged and prepared for release repeatedly. Continuous Deployment goes further and ships changes automatically when checks pass.

How it appears here:

- Jenkins builds Docker images.
- Jenkins tags the images.
- Jenkins loads images into Minikube.
- Jenkins applies Kubernetes manifests.
- Jenkins waits for rollout completion.
- Jenkins verifies backend and frontend health.

Relevant file:

- [Jenkinsfile](Jenkinsfile)

Why it matters:

- Deployment is no longer a manual sequence of commands.
- The release process is repeatable.
- The pipeline can fail fast when something is broken.

### 2.9 Health checks and readiness

Health checks are how platforms and automation verify that a service is alive and ready to serve traffic.

How it appears here:

- PostgreSQL has a container healthcheck.
- The backend exposes a `/health` endpoint.
- Jenkins waits for backend and frontend endpoints.
- Docker Compose uses `depends_on` with health conditions.

Why it matters:

- Startup order becomes safer.
- Deployments can be validated automatically.
- Orchestrators can restart or delay traffic when a service is not ready.

### 2.10 Observability

Observability means being able to understand what the system is doing from the outside using logs, metrics, and traces. This repo focuses on metrics and alerts.

How it appears here:

- Backend exposes Prometheus metrics.
- Prometheus scrapes the backend and postgres exporter.
- Grafana visualizes branch health and infrastructure status.
- Alerting routes critical conditions to the backend webhook.

Why it matters:

- You can detect failures before users report them.
- Metrics help explain whether an issue is application-level or infrastructure-level.
- Dashboards support faster operational decisions.

### 2.11 Logging and metrics

Logging captures discrete events. Metrics capture time-based numeric state.

How it appears here:

- The backend logs startup, metric generation, and auto-heal activity.
- The backend publishes custom counters and gauges.
- Prometheus records operational measurements over time.

Why it matters:

- Logs help answer "what happened?"
- Metrics help answer "how often?" and "how bad?"
- Together they reduce guesswork during incidents.

### 2.12 Monitoring

Monitoring means continuously watching the health of the system.

How it appears here:

- Prometheus collects backend and database exporter metrics.
- Grafana dashboards are provisioned automatically.
- Dashboard panels show branch health, incidents, and resource trends.

Why it matters:

- Operators can see trends instead of reacting only after failure.
- Dashboards standardize what the team considers important.
- A deployed system is only useful if you can see whether it is working.

### 2.13 Alerting

Alerting means turning important monitoring signals into notifications.

How it appears here:

- Grafana alert rules are provisioned from files.
- A webhook contact point posts alerts to the backend.
- The backend receives Grafana alerts through `/alerts/webhooks/grafana`.

Why it matters:

- Human attention is reserved for high-priority events.
- Alerts are declarative and version controlled.
- The team can define what counts as critical.

### 2.14 Self-healing

Self-healing means the system automatically recovers from some failures without waiting for a manual fix.

How it appears here:

- The backend has a background job that auto-heals critical branches.
- Simulated incidents can be resolved through a heal endpoint.
- Alert and incident state is updated when recovery happens.

Why it matters:

- Short-lived failures can be resolved quickly.
- Operational load is reduced.
- Recovery is more consistent than manual intervention.

### 2.15 Scalability and autoscaling

Scalability means the system can handle more load. Autoscaling means the platform adjusts resource count based on demand.

How it appears here:

- Kubernetes includes a backend HorizontalPodAutoscaler.
- The backend deployment is designed to be replicated.

Why it matters:

- Load spikes do not always require a manual response.
- Resource use can expand and contract with demand.
- Scaling policy becomes part of the deployment definition.

### 2.16 High availability and resilience

High availability is about reducing downtime. Resilience is about continuing to function when some parts fail.

How it appears here:

- PodDisruptionBudgets protect backend, frontend, and PostgreSQL.
- Services are split so one failure does not necessarily take down the whole stack.
- Persistent volumes preserve state across restarts.
- The pipeline validates rollout status before considering deployment successful.

Why it matters:

- Maintenance events are less disruptive.
- Failed pods can be replaced without losing data.
- The system becomes more tolerant of infrastructure churn.

### 2.17 Rollback and recovery

Rollback is the ability to return to a previous working state after a bad deployment.

How it appears here:

- The repository includes [ansible/rollback.yml](ansible/rollback.yml).
- The Jenkins pipeline verifies rollouts and health after deployment.
- The deployment files are versioned, so changes can be reverted in Git.

Why it matters:

- Mistakes do not have to become outages.
- Recovery can be scripted.
- Teams can act quickly when a release breaks production.

### 2.18 Environment parity

Environment parity means development, test, and production are as similar as possible.

How it appears here:

- The same Docker images can be used locally and in orchestration.
- Local Compose and Kubernetes use the same backend port conventions.
- The frontend talks to the backend through a clearly defined API base.

Why it matters:

- Bugs caused by environment differences are reduced.
- Local debugging is more trustworthy.
- Deployment surprises are fewer.

### 2.19 State management

Stateful services need careful handling because not everything can be recreated from code alone.

How it appears here:

- PostgreSQL has a persistent volume.
- Prometheus has a persistent TSDB volume.
- Grafana stores data in a persistent volume.

Why it matters:

- Operational data survives restarts.
- Monitoring history is retained.
- Dashboards and settings are not lost on redeploy.

### 2.20 Security posture

Security in DevOps is about building protections into delivery and operations.

How it appears here:

- Secrets are parameterized instead of hardcoded.
- The frontend is served through Nginx in deployment mode.
- Kubernetes resources separate workloads into a namespace.
- Monitoring and alerting provide visibility into unexpected behavior.

Why it matters:

- Security is part of the delivery process, not an afterthought.
- Operational controls are codified.
- The system is easier to audit.

## 3. Exact DevOps Tooling Present In This Repository

### 3.1 Docker Compose

Used for local integration of all major services.

- [docker-compose.yml](docker-compose.yml)

### 3.2 Dockerfiles

Used to build repeatable images for backend and frontend.

- [Backend/Dockerfile](Backend/Dockerfile)
- [Frontend/Dockerfile](Frontend/Dockerfile)

### 3.3 Kubernetes manifests

Used to describe runtime deployment in a cluster.

- [k8s/](k8s)

### 3.4 Jenkins pipeline

Used to automate build, test, deploy, and verify steps.

- [Jenkinsfile](Jenkinsfile)

### 3.5 Ansible automation

Used to automate infrastructure setup, app deployment, monitoring setup, rollback, and teardown.

- [ansible/](ansible)

### 3.6 Monitoring stack

Used to expose and visualize system health.

- [prometheus/](prometheus)
- [grafana/](grafana)

## 4. Project Notes And Current Limits

The repository is feature-complete in several important areas, but a few things are intentionally limited or still local-only:

- User accounts and roles are defined in-app rather than through an external IAM system.
- Some settings are persisted only in frontend storage.
- The Grafana webhook endpoint accepts alerts and acknowledges them, but it is not a full incident management platform.
- Frontend tests exist, but the test surface is still relatively small compared with the application size.

## 5. Quick Summary

UrbanBank already implements a real DevOps workflow:

- Code is containerized.
- Services are orchestrated.
- Infrastructure is declared as code.
- Builds and tests are automated.
- Deployments are validated.
- Metrics and dashboards provide visibility.
- Alerts and self-healing reduce operational friction.

If you want, the next step is to turn this into a shorter README-style version or into a presentation-ready project report.