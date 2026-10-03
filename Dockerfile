FROM node:24-alpine AS frontend
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 bench
COPY backend/app ./app
COPY backend/migrations ./migrations
COPY backend/alembic.ini ./
COPY --from=frontend /build/backend/static ./static
RUN mkdir /data && chown bench /data
USER bench
ENV DATABASE_URL=sqlite:////data/agentbench.db
EXPOSE 8100
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8100"]
