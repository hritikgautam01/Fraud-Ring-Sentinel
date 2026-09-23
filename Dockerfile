# Stage 1: Build Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend Runtime
FROM python:3.11-slim

# Create non-root user (Hugging Face requirement: user ID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

WORKDIR /home/user/app

# Install Python dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy backend code, models, datasets
COPY --chown=user api/ ./api/
COPY --chown=user ml/ ./ml/
COPY --chown=user test.py ./

# Copy built frontend assets from stage 1
COPY --chown=user --from=frontend-builder /app/frontend/dist ./frontend/dist

# Hugging Face Spaces standard port is 7860
EXPOSE 7860

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
