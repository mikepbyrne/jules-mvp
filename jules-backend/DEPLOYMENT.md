# Jules Backend Deployment Guide

This guide covers deploying the Jules backend to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Database Setup](#database-setup)
- [Deployment Options](#deployment-options)
  - [Docker Deployment](#docker-deployment)
  - [Kubernetes Deployment](#kubernetes-deployment)
  - [Cloud Platform Deployment](#cloud-platform-deployment)
- [Post-Deployment](#post-deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Services

1. **PostgreSQL 16+**
   - Managed service recommended (AWS RDS, Google Cloud SQL, etc.)
   - Minimum 2GB RAM, 20GB storage
   - Automated backups enabled

2. **Redis 7+**
   - Managed service recommended (AWS ElastiCache, Redis Cloud, etc.)
   - Minimum 1GB RAM
   - Persistence enabled

3. **External APIs**
   - Bandwidth account for SMS
   - Anthropic API key for Claude
   - OpenAI API key (backup)
   - Stripe account for payments
   - Veriff account for age verification
   - Sentry account for error tracking (optional)
   - Langfuse account for LLM monitoring (optional)

### SSL/TLS Certificate

- Production requires HTTPS
- Use Let's Encrypt or cloud provider certificates
- Certificate must cover webhook endpoints

## Environment Setup

### 1. Generate Secure Keys

```bash
# Generate strong random keys (32+ characters)
openssl rand -hex 32  # SECRET_KEY
openssl rand -hex 32  # ENCRYPTION_KEY
openssl rand -hex 32  # JWT_SECRET_KEY
```

### 2. Create Production Environment File

Create `.env.production`:

```env
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=<generated-secret-key>

# Database (use managed PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/jules_production
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis (use managed Redis)
REDIS_URL=redis://:password@host:6379/0
REDIS_SESSION_TTL=14400

# SMS Provider (Bandwidth)
BANDWIDTH_ACCOUNT_ID=<your-account-id>
BANDWIDTH_USERNAME=<your-username>
BANDWIDTH_PASSWORD=<your-password>
BANDWIDTH_APPLICATION_ID=<your-app-id>
BANDWIDTH_PHONE_NUMBER=<your-phone-number>

# LLM Providers
ANTHROPIC_API_KEY=<your-anthropic-key>
OPENAI_API_KEY=<your-openai-key>
DEFAULT_LLM_PROVIDER=anthropic
DEFAULT_MODEL=claude-3-5-haiku-20241022

# Age Verification
VERIFF_API_KEY=<your-veriff-key>
VERIFF_API_SECRET=<your-veriff-secret>

# Payment
STRIPE_SECRET_KEY=<sk_live_...>
STRIPE_PUBLISHABLE_KEY=<pk_live_...>
STRIPE_WEBHOOK_SECRET=<whsec_...>
STRIPE_PRICE_ID_MONTHLY=<price_...>
STRIPE_PRICE_ID_ANNUAL=<price_...>

# Monitoring
SENTRY_DSN=<your-sentry-dsn>
LANGFUSE_PUBLIC_KEY=<your-langfuse-public-key>
LANGFUSE_SECRET_KEY=<your-langfuse-secret-key>

# Security
ENCRYPTION_KEY=<generated-encryption-key>
JWT_SECRET_KEY=<generated-jwt-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Compliance
CRISIS_HOTLINE_NUMBER=988
AI_DISCLOSURE_INTERVAL_HOURS=3
ALLOWED_ORIGINS=https://yourdomain.com
```

## Database Setup

### 1. Create Database

```sql
-- Connect to PostgreSQL
psql -h your-db-host -U postgres

-- Create database
CREATE DATABASE jules_production;

-- Create user
CREATE USER jules WITH ENCRYPTED PASSWORD 'secure-password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE jules_production TO jules;
```

### 2. Run Migrations

```bash
# Set DATABASE_URL
export DATABASE_URL="postgresql+asyncpg://jules:password@host:5432/jules_production"

# Run migrations
poetry run alembic upgrade head

# Verify
poetry run alembic current
```

### 3. Create Indexes

Alembic migrations create necessary indexes, but verify:

```sql
-- Check indexes
\di

-- Key indexes should include:
-- - users.phone_number
-- - conversations.user_id
-- - messages.conversation_id
-- - compliance_disclosures.user_id
```

## Deployment Options

### Docker Deployment

#### Build Production Image

```bash
docker build --target production -t jules-backend:latest .
```

#### Run Container

```bash
docker run -d \
  --name jules-api \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env.production \
  --health-cmd "curl -f http://localhost:8000/health || exit 1" \
  --health-interval 30s \
  --health-timeout 10s \
  --health-retries 3 \
  jules-backend:latest
```

#### Docker Compose (Production)

```yaml
version: '3.8'

services:
  api:
    image: jules-backend:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Kubernetes Deployment

#### Create Secrets

```bash
kubectl create secret generic jules-secrets \
  --from-env-file=.env.production
```

#### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jules-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: jules-backend
  template:
    metadata:
      labels:
        app: jules-backend
    spec:
      containers:
      - name: api
        image: jules-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: jules-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: jules-backend
spec:
  selector:
    app: jules-backend
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Cloud Platform Deployment

#### AWS (ECS Fargate)

1. Create ECS cluster
2. Create task definition with Docker image
3. Configure environment variables
4. Set up Application Load Balancer
5. Configure auto-scaling

#### Google Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/jules-backend

# Deploy
gcloud run deploy jules-backend \
  --image gcr.io/PROJECT_ID/jules-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars $(cat .env.production | xargs)
```

#### Heroku

```bash
# Login
heroku login

# Create app
heroku create jules-backend-prod

# Set environment variables
heroku config:set $(cat .env.production | xargs)

# Deploy
git push heroku main

# Run migrations
heroku run alembic upgrade head
```

## Post-Deployment

### 1. Configure Webhooks

#### Bandwidth SMS Webhook

- Go to Bandwidth dashboard
- Set webhook URL: `https://yourdomain.com/webhooks/sms`
- Enable "Message Received" events

#### Stripe Webhooks

- Go to Stripe dashboard → Webhooks
- Add endpoint: `https://yourdomain.com/webhooks/stripe`
- Select events:
  - `checkout.session.completed`
  - `customer.subscription.created`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_succeeded`
  - `invoice.payment_failed`
- Copy webhook signing secret to `STRIPE_WEBHOOK_SECRET`

### 2. Verify Health

```bash
curl https://yourdomain.com/health

# Expected response:
{
  "status": "healthy",
  "service": "jules-backend",
  "checks": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### 3. Test SMS Flow

1. Send test SMS to your Bandwidth number
2. Verify webhook received
3. Check response sent
4. Review logs

### 4. Set Up Monitoring

#### Sentry

- Errors automatically captured
- View in Sentry dashboard
- Set up alerts for critical errors

#### Langfuse

- LLM calls automatically tracked
- Monitor token usage
- Analyze conversation quality

## Monitoring

### Key Metrics

- **API Response Time**: Target < 500ms for webhooks
- **LLM Latency**: Target < 2s for response generation
- **Error Rate**: Target < 0.1%
- **Database Connections**: Monitor pool usage
- **Redis Hit Rate**: Target > 80%

### Alerts

Set up alerts for:

- High error rate (> 1%)
- Slow API responses (> 2s p95)
- Database connection exhaustion
- Redis connection failures
- High LLM costs

### Logs

```bash
# View application logs
docker logs -f jules-api

# Filter errors
docker logs jules-api 2>&1 | grep ERROR

# Follow specific user
docker logs jules-api 2>&1 | grep "user_id: 123"
```

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check connection pool
docker exec jules-api python -c "from src.core.database import engine; print(engine.pool.status())"
```

### Redis Connection Issues

```bash
# Test Redis
redis-cli -u $REDIS_URL ping

# Check memory
redis-cli -u $REDIS_URL info memory
```

### High Memory Usage

```bash
# Check container stats
docker stats jules-api

# Reduce workers if needed
# Update CMD in Dockerfile: --workers 2
```

### Webhook Failures

```bash
# Check webhook signature verification
# Review logs for signature errors

# Test webhook manually
curl -X POST https://yourdomain.com/webhooks/sms \
  -H "Content-Type: application/json" \
  -d '[{"type":"message-received","message":{"from":"+15551234567","text":"test"}}]'
```

## Rollback Procedure

```bash
# 1. Deploy previous version
docker pull jules-backend:previous-tag
docker service update --image jules-backend:previous-tag jules-api

# 2. Rollback database if needed
alembic downgrade -1

# 3. Verify health
curl https://yourdomain.com/health

# 4. Monitor for errors
```

## Security Checklist

- [ ] HTTPS enabled for all endpoints
- [ ] Strong random keys generated (32+ chars)
- [ ] Database credentials secured
- [ ] API keys stored in secrets/environment
- [ ] Webhook signatures verified
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Database backups automated
- [ ] Monitoring and alerting active
- [ ] Logs reviewed regularly

## Support

For deployment issues:
1. Check logs: `docker logs jules-api`
2. Verify health: `curl /health`
3. Review error tracking (Sentry)
4. Contact development team
