FROM node:24-bookworm-slim AS node
FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=node /usr/local/bin/node /usr/local/bin/node
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 KL8_REQUIRE_AUTH=1 \
    KL8_DATABASE=/data/fusion.sqlite OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
EXPOSE 8080
CMD ["sh", "-c", "exec python run.py --host 0.0.0.0 --port ${PORT:-8080}"]
