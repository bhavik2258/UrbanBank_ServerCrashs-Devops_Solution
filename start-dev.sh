#!/bin/bash

BACKEND_PORT=8000
FRONTEND_PORT=8080

port_is_listening() {
    local port="$1"
    ss -ltn "sport = :${port}" 2>/dev/null | tail -n +2 | grep -q .
}

echo "🚀 Starting database via Docker..."
docker compose up db -d

echo "📈 Starting Prometheus via Docker..."
docker compose up prometheus -d

echo "📊 Starting Grafana via Docker..."
docker compose up grafana -d

echo "🐍 Starting Python Backend (FastAPI)..."
if curl -fsS "http://localhost:${BACKEND_PORT}/health" >/dev/null 2>&1; then
    echo "ℹ️ Backend already responding on port ${BACKEND_PORT}; reusing the existing process."
elif port_is_listening "${BACKEND_PORT}"; then
    echo "⚠️ Port ${BACKEND_PORT} is already in use, but it is not the UrbanBank backend."
    echo "   Stop the process using that port or set a different BACKEND_PORT before rerunning."
    exit 1
else
    (cd Backend && source ../.venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port "${BACKEND_PORT}") &
    BACKEND_PID=$!
fi

echo "⚛️ Starting React/Vite Frontend..."
if port_is_listening "${FRONTEND_PORT}"; then
    echo "ℹ️ Frontend port ${FRONTEND_PORT} is already in use; Vite will not be started again."
else
    (cd Frontend && npm run dev) &
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
    docker compose stop db prometheus grafana
    echo "👋 All stopped. Goodbye!"
    exit
}

# Trap Ctrl+C (SIGINT) and run the cleanup function
trap cleanup SIGINT SIGTERM

echo "--------------------------------------------------------"
echo "✅ Local development services are running!"
echo "   - Frontend: http://localhost:${FRONTEND_PORT}"
echo "   - Backend:  http://localhost:${BACKEND_PORT}"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3001"
echo "   - Database: localhost:5432"
echo ""
echo "Press Ctrl+C at any time to carefully shut down everything."
echo "--------------------------------------------------------"

# Keep the script running to catch the Ctrl+C
wait