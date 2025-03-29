#!/bin/bash

# Build and start the Docker containers
echo "Starting URL Snake with MongoDB..."
docker-compose up -d

# Wait for containers to be ready
echo "Waiting for services to be ready..."
sleep 5

# Show the running containers
echo "Services running:"
docker-compose ps

echo ""
echo "URL Snake is running at: http://localhost:5000"
echo "To stop the services, run: docker-compose down"
