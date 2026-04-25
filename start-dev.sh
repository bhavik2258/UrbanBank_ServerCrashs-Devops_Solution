#!/bin/bash

echo "🚀 Starting database via Docker..."
docker compose up db -d

echo "📈 Starting Prometheus via Docker..."
docker compose up prometheus -d

echo "📊 Starting Grafana via Docker..."
docker compose up grafana -d

echo "🐍 Starting Python Backend (FastAPI)..."
(cd Backend && source ../.venv/bin/activate && uvicorn main:app --reload) &
BACKEND_PID=$!

echo "⚛️ Starting React/Vite Frontend..."
(cd Frontend && npm run dev) &
FRONTEND_PID=$!

# Clean up background processes when you press Ctrl+C
cleanup() {
    echo ""
    echo "🛑 Stopping local servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "🛑 Stopping database container..."
    docker compose stop db prometheus grafana
    echo "👋 All stopped. Goodbye!"
    exit
}

# Trap Ctrl+C (SIGINT) and run the cleanup function
trap cleanup SIGINT SIGTERM

echo "--------------------------------------------------------"
echo "✅ Local development services are running!"
echo "   - Frontend: http://localhost:8080"
echo "   - Backend:  http://localhost:8000"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3001"
echo "   - Database: localhost:5432"
echo ""
echo "Press Ctrl+C at any time to carefully shut down everything."
echo "--------------------------------------------------------"

# Keep the script running to catch the Ctrl+C
wait