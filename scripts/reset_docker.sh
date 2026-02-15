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
i=0
max_attempts=30  # 30 attempts * 2 seconds = 60 seconds timeout
until curl -s -f http://localhost:8000/health > /dev/null; do
    if [ $i -ge $max_attempts ]; then
        echo ""
        echo "❌ Error: App failed to become healthy after ${max_attempts} attempts (60 seconds)"
        echo "Check logs with: docker compose logs app"
        exit 1
    fi
    printf '.'
    sleep 2
    i=$((i + 1))
done
echo " App is ready!"

echo "✅  Environment reset complete!"
echo "📊  Grafana: http://localhost:3000 (admin/admin)"
echo "🔍  Jaeger: http://localhost:16686"
echo "📈  Prometheus: http://localhost:9090"
echo "🚀  App: http://localhost:8000"
