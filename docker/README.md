# Build image
docker build -t episodic-pivot-scanner .

# Run API server
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./data/episodic_pivot.db \
  -v $(pwd)/data:/app/data \
  episodic-pivot-scanner python run_api.py

# Run with docker-compose (recommended)
docker-compose up -d api

# View logs
docker-compose logs -f api

# Stop containers
docker-compose down
