# Optional Railway deploy via Dockerfile (docs/deployment-plan.md).
FROM python:3.11-slim

WORKDIR /app

COPY requirements-api.txt requirements-core.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt

COPY api/ api/
COPY src/ src/
COPY scripts/start-api.sh scripts/start-api.sh
COPY data/processed/restaurants.parquet data/processed/

ENV PYTHONPATH=src
ENV DATA_PATH=data/processed/restaurants.parquet

RUN chmod +x scripts/start-api.sh

EXPOSE 8000
CMD ["bash", "scripts/start-api.sh"]
