### Multi-stage build: frontend (Vite/React) + backend (FastAPI)

FROM node:20-alpine AS frontend_builder
WORKDIR /frontend

# Install deps first for better caching
# (package-lock.json is optional)
COPY frontend/package*.json ./

RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY frontend ./
RUN npm run build


FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

# Copy built frontend into backend static directory
COPY --from=frontend_builder /frontend/dist ./app/static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
