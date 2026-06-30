#!/bin/bash

BACKEND_PORT=8000
FRONTEND_PORT=5173
JENKINS_PORT=8080
SONARQUBE_PORT=9000
export JENKINS_ADMIN_USERNAME=${JENKINS_ADMIN_USERNAME:-urbanbank-admin}
export JENKINS_ADMIN_PASSWORD=${JENKINS_ADMIN_PASSWORD:-UrbanBankJenkins2026!}
JENKINS_COMPOSE_FILE=docker-compose.jenkins.yml
JENKINS_STARTED_BY_SCRIPT=false
SONARQUBE_STARTED_BY_SCRIPT=false
START_MONITORING=${START_MONITORING:-false}
START_JENKINS=${START_JENKINS:-false}
START_SONARQUBE=${START_SONARQUBE:-false}
START_MINIKUBE_FOR_JENKINS=${START_MINIKUBE_FOR_JENKINS:-false}

port_is_listening() {
    local port="$1"
    ss -ltn "sport = :${port}" 2>/dev/null | tail -n +2 | grep -q .
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

http_is_responding() {
    local url="$1"
    curl -fsS --max-time 3 "${url}" >/dev/null 2>&1
}

jenkins_container_is_running() {
    docker compose -f "${JENKINS_COMPOSE_FILE}" ps --status running --services 2>/dev/null | grep -qx jenkins
}

sonarqube_container_is_running() {
    docker compose -f "${JENKINS_COMPOSE_FILE}" ps --status running --services 2>/dev/null | grep -qx sonarqube
}

minikube_is_running() {
    minikube status --format='{{.Host}} {{.Kubelet}} {{.APIServer}}' 2>/dev/null | grep -q "Running Running Running"
}

ensure_kubernetes_for_jenkins() {
    if [[ "${START_MINIKUBE_FOR_JENKINS}" != "true" ]]; then
        echo "ℹ️ Skipping Minikube startup because START_MINIKUBE_FOR_JENKINS is not true."
        return
    fi

    echo "☸️ Checking Kubernetes tools for Jenkins CI/CD..."
    if ! command_exists kubectl; then
        echo "⚠️ kubectl is missing. Install kubectl before running the Jenkins deploy pipeline."
        exit 1
    fi

    if ! command_exists minikube; then
        echo "⚠️ minikube is missing. Install Minikube before running the Jenkins deploy pipeline."
        exit 1
    fi

    if minikube_is_running; then
        echo "ℹ️ Minikube is already running; Jenkins can use kubectl/minikube deploy stages."
    else
        echo "☸️ Starting Minikube for Jenkins CI/CD deploy stages..."
        minikube start
    fi
}

echo "🚀 Starting database via Docker..."
docker compose up db -d

if [[ "${START_MONITORING}" == "true" ]]; then
    echo "📈 Starting Prometheus/Grafana via Docker..."
    docker compose --profile monitoring up -d postgres-exporter prometheus grafana
else
    echo "ℹ️ Skipping Prometheus/Grafana. Set START_MONITORING=true to start them."
fi

if [[ "${START_SONARQUBE}" == "true" ]]; then
    echo "🔎 Starting SonarQube via Docker..."
    if sonarqube_container_is_running; then
        echo "ℹ️ SonarQube is already running; reusing it."
    elif port_is_listening "${SONARQUBE_PORT}"; then
        echo "⚠️ Port ${SONARQUBE_PORT} is already in use, so SonarQube cannot start there."
        echo "   Stop the process using that port before rerunning."
        exit 1
    else
        docker compose -f "${JENKINS_COMPOSE_FILE}" up -d sonarqube
        SONARQUBE_STARTED_BY_SCRIPT=true
    fi
else
    echo "ℹ️ Skipping SonarQube. Set START_SONARQUBE=true to start it."
fi

if [[ "${START_JENKINS}" == "true" ]]; then
    ensure_kubernetes_for_jenkins

    echo "🏗️ Starting Jenkins CI/CD via Docker..."
    if jenkins_container_is_running; then
        echo "ℹ️ Jenkins container is already running; reusing it."
    elif port_is_listening "${JENKINS_PORT}"; then
        echo "⚠️ Port ${JENKINS_PORT} is already in use, so Jenkins cannot start there."
        echo "   Stop the process using that port before rerunning."
        exit 1
    else
        docker compose -f "${JENKINS_COMPOSE_FILE}" up -d jenkins
        JENKINS_STARTED_BY_SCRIPT=true
    fi
else
    echo "ℹ️ Skipping Jenkins CI/CD. Set START_JENKINS=true to start it."
fi

echo "🐍 Starting Python Backend (FastAPI)..."
if http_is_responding "http://localhost:${BACKEND_PORT}/health"; then
    echo "ℹ️ Backend already responding on port ${BACKEND_PORT}; reusing the existing process."
elif port_is_listening "${BACKEND_PORT}"; then
    echo "⚠️ Port ${BACKEND_PORT} is already in use, but the UrbanBank health check did not respond quickly."
    echo "   Stop the process using that port or wait for it to become healthy before rerunning."
    exit 1
else
    (cd Backend && source ../.venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port "${BACKEND_PORT}" < /dev/null) &
    BACKEND_PID=$!
fi

echo "⚛️ Starting React/Vite Frontend..."
if http_is_responding "http://localhost:${FRONTEND_PORT}/"; then
    echo "ℹ️ Frontend already responding on port ${FRONTEND_PORT}; reusing it."
elif port_is_listening "${FRONTEND_PORT}"; then
    echo "ℹ️ Frontend port ${FRONTEND_PORT} is already in use; Vite will not be started again."
    echo "   If the page hangs, stop that process and rerun this script."
else
    (cd Frontend && npm run dev -- --host 0.0.0.0 --port "${FRONTEND_PORT}" < /dev/null) &
    FRONTEND_PID=$!
fi

# Clean up background processes when you press Ctrl+C
cleanup() {
    echo ""
    echo "🛑 Stopping local servers..."
    if [[ -n "${BACKEND_PID:-}" ]]; then
        kill "$BACKEND_PID" 2>/dev/null
    fi
    if [[ -n "${FRONTEND_PID:-}" ]]; then
        kill "$FRONTEND_PID" 2>/dev/null
    fi
    echo "🛑 Stopping database container..."
    docker compose stop db
    if [[ "${START_MONITORING}" == "true" ]]; then
        echo "🛑 Stopping monitoring containers..."
        docker compose stop postgres-exporter prometheus grafana
    fi
    if [[ "${JENKINS_STARTED_BY_SCRIPT}" == "true" ]]; then
        echo "🛑 Stopping Jenkins CI/CD container..."
        docker compose -f "${JENKINS_COMPOSE_FILE}" stop jenkins
    fi
    if [[ "${SONARQUBE_STARTED_BY_SCRIPT}" == "true" ]]; then
        echo "🛑 Stopping SonarQube containers..."
        docker compose -f "${JENKINS_COMPOSE_FILE}" stop sonarqube sonarqube-db
    fi
    echo "👋 All stopped. Goodbye!"
    exit
}

# Trap Ctrl+C (SIGINT) and run the cleanup function
trap cleanup SIGINT SIGTERM

echo "--------------------------------------------------------"
echo "✅ Local development services are running!"
echo "   - Frontend: http://localhost:${FRONTEND_PORT}"
echo "   - Backend:  http://localhost:${BACKEND_PORT}"
echo "   - Database: localhost:5432"
if [[ "${START_JENKINS}" == "true" ]]; then
    echo "   - Jenkins CI/CD: http://localhost:${JENKINS_PORT}"
    echo "   - Jenkins login: ${JENKINS_ADMIN_USERNAME} / ${JENKINS_ADMIN_PASSWORD}"
fi
if [[ "${START_SONARQUBE}" == "true" ]]; then
    echo "   - SonarQube: http://localhost:${SONARQUBE_PORT}"
    echo "   - SonarQube login: admin / admin"
fi
if [[ "${START_MONITORING}" == "true" ]]; then
    echo "   - Prometheus: http://localhost:9090"
    echo "   - Grafana: http://localhost:3001"
fi
echo ""
echo "Press Ctrl+C at any time to carefully shut down everything."
echo "--------------------------------------------------------"

# Keep the script running to catch the Ctrl+C
wait
