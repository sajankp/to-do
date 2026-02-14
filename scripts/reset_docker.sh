#!/bin/bash
# Reset Docker Compose environment and rebuild
set -e

echo "🗑️  Stopping and removing all containers..."
docker compose down -v

echo "🧹  Cleaning up Docker system..."
docker system prune -f

echo "🔨  Rebuilding and starting services..."
docker compose up --build -d

echo "⏳  Waiting for services to be ready..."
# Wait for the main app to be healthy
echo "Waiting for FastTodo app..."
until curl -s -f http://localhost:8000/health > /dev/null; do
    printf '.'
    sleep 2
done
echo " App is ready!"

echo "✅  Environment reset complete!"
echo "📊  Grafana: http://localhost:3000 (admin/admin)"
echo "🔍  Jaeger: http://localhost:16686"
echo "📈  Prometheus: http://localhost:9090"
echo "🚀  App: http://localhost:8000"
