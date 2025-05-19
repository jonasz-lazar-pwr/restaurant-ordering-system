# payment-service/Dockerfile

# Build stage – install dependencies
FROM python:3.11-alpine AS build-stage

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache gcc musl-dev libpq-dev

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Final stage – runtime only
FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache libpq

WORKDIR /app

COPY --from=build-stage /usr/local /usr/local

COPY . .

RUN rm -rf /root/.cache

EXPOSE 8004

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8004"]
