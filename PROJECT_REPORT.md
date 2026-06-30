# UrbanBank — Project Report

**Summary**
- **Project:** UrbanBank (full-stack monitoring/demo banking app)
- **Location:** monorepo with `Backend/`, `Frontend/`, `k8s/`, `grafana/`, and CI config at repository root.

**Quick Links**
- **Backend:** [Backend](Backend)
- **Frontend:** [Frontend](Frontend)
- **Kubernetes manifests:** [k8s](k8s)
- **Grafana provisioning:** [grafana](grafana)
- **Prometheus config:** [prometheus/prometheus.yml](prometheus/prometheus.yml)
- **CI / Jenkinsfile:** [Jenkinsfile](Jenkinsfile)
- **Docker Compose:** [docker-compose.yml](docker-compose.yml) and [docker-compose.jenkins.yml](docker-compose.jenkins.yml)

**Architecture & Components**
- **Backend:** Python FastAPI app. Key files: [Backend/main.py](Backend/main.py), [Backend/routers](Backend/routers).
- **Frontend:** React + Vite TypeScript app. Key files: [Frontend/src/main.tsx](Frontend/src/main.tsx), [Frontend/package.json](Frontend/package.json).
- **Data & Metrics:** Postgres manifests in [k8s/postgres-deployment.yaml](k8s/postgres-deployment.yaml). Metrics exported via [Backend/prometheus_metrics.py](Backend/prometheus_metrics.py).
- **Observability:** Prometheus config in [prometheus/prometheus.yml](prometheus/prometheus.yml); Grafana dashboards in [grafana/](grafana).
- **CI/CD:** Jenkins-driven pipeline in [Jenkinsfile](Jenkinsfile) and Jenkins init scripts in [jenkins/init.groovy.d/01-security.groovy](jenkins/init.groovy.d/01-security.groovy).
- **Architecture diagram:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — source: [docs/architecture.mmd](docs/architecture.mmd). To render PNG locally run `scripts/render_diagrams.sh`.

**How to Run (developer & full)**
- Development (local):

```bash
./start-dev.sh
```

- Full stack (compose):

```bash
./start-full.sh
# or
docker-compose up --build
```

- Kubernetes deployment (cluster):

```bash
kubectl apply -k k8s/
```

**Dependencies**
- Backend Python deps: [Backend/requirements.txt](Backend/requirements.txt)
- Frontend npm deps: [Frontend/package.json](Frontend/package.json)

**Testing**
- Frontend: Playwright config at [Frontend/playwright.config.ts](Frontend/playwright.config.ts) and unit tests via `vitest` ([Frontend/vitest.config.ts](Frontend/vitest.config.ts)).
- Backend: unit/integration tests should be added; current repo contains API routers under [Backend/routers](Backend/routers).

**CI/CD & Release Flow**
- Pipeline defined in [Jenkinsfile](Jenkinsfile) — builds images, runs tests, and deploys to target environment using `k8s` manifests or `docker-compose.jenkins.yml` for CI runners.
- Dockerfiles: [Backend/Dockerfile](Backend/Dockerfile) and [Frontend/Dockerfile](Frontend/Dockerfile).

**Monitoring & Alerting**
- Prometheus config: [prometheus/prometheus.yml](prometheus/prometheus.yml)
- Grafana dashboards and provisioning: [grafana/](grafana)
- Alerts and rules are provisioned under [grafana/provisioning/alerting](grafana/provisioning/alerting)

**Security & Secrets**
- Kubernetes secrets: [k8s/secret.yaml](k8s/secret.yaml)
- Jenkins security bootstrap: [jenkins/init.groovy.d/01-security.groovy](jenkins/init.groovy.d/01-security.groovy)

**Known Issues & Recommendations**
- Add backend integration tests and CI test steps if missing.
- Ensure secrets and credentials are stored in a secure store (Vault/Secrets Manager) rather than plaintext in manifests.
- Add schema for production-ready resource limits and HPA tuning: see [k8s/backend-hpa.yaml](k8s/backend-hpa.yaml).
- Avoid frontend N+1 API fanout — prefer server-side aggregated endpoints for lists (see repo memory note on performance).

**Next Steps / Roadmap**
- Implement automated backend tests and enable them in the Jenkins pipeline.
- Harden k8s manifests (resource requests, liveness/readiness probes, network policies).
- Add infrastructure as code provenance for Grafana alerts (remove API-created rules before switching to file provisioning).
- Add onboarding README for new developers with quick-start troubleshooting.

**Maintainers / Contacts**
- Repo owner / primary maintainer: check repository settings and `README.md` in the `Frontend/` for developer contacts.

---
Generated on: 2026-05-17
