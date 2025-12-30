# Jules Backend - Quick Start Guide

Get Jules up and running in 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- Git installed
- Text editor

## Step 1: Clone and Navigate

```bash
cd jules-backend
```

## Step 2: Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

**Required API Keys:**
```env
ANTHROPIC_API_KEY=sk-ant-...        # Get from console.anthropic.com
OPENAI_API_KEY=sk-...               # Get from platform.openai.com (backup)
BANDWIDTH_ACCOUNT_ID=...            # Get from Bandwidth dashboard
BANDWIDTH_USERNAME=...
BANDWIDTH_PASSWORD=...
BANDWIDTH_APPLICATION_ID=...
BANDWIDTH_PHONE_NUMBER=+1...
```

**Generate Secure Keys:**
```bash
# Run these commands and paste results into .env
openssl rand -hex 32  # SECRET_KEY
openssl rand -hex 32  # ENCRYPTION_KEY
openssl rand -hex 32  # JWT_SECRET_KEY
```

## Step 3: Start Services

```bash
# Start PostgreSQL, Redis, and API
docker-compose up -d

# View logs
docker-compose logs -f api
```

## Step 4: Run Migrations

```bash
# Run database migrations
docker-compose exec api alembic upgrade head
```

## Step 5: Verify Installation

```bash
# Check health
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "checks": {
#     "database": "healthy",
#     "redis": "healthy"
#   }
# }
```

## Step 6: Test SMS Flow

```bash
# Send test SMS to your Bandwidth number
# Or use the webhook endpoint directly:

curl -X POST http://localhost:8000/webhooks/sms \
  -H "Content-Type: application/json" \
  -d '[{
    "type": "message-received",
    "message": {
      "id": "msg-test-123",
      "from": "+15551234567",
      "text": "Hello Jules!"
    }
  }]'
```

## Access Points

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Database UI (Adminer)**: http://localhost:8080
- **Redis UI**: http://localhost:8081

## Common Commands

```bash
# View logs
docker-compose logs -f api

# Restart API
docker-compose restart api

# Stop all services
docker-compose down

# Run tests
docker-compose exec api pytest -v

# Create migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Database shell
docker-compose exec postgres psql -U jules -d jules_dev
```

## Troubleshooting

### Database Connection Error

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Redis Connection Error

```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli -a jules_redis_password ping
```

### API Not Starting

```bash
# View detailed logs
docker-compose logs api

# Check environment variables
docker-compose exec api env | grep DATABASE_URL

# Rebuild container
docker-compose up -d --build api
```

## Next Steps

1. **Configure Webhooks**
   - Set Bandwidth webhook URL to `https://yourdomain.com/webhooks/sms`
   - Set Stripe webhook URL to `https://yourdomain.com/webhooks/stripe`

2. **Test Features**
   - Send test SMS
   - Test crisis detection ("I'm feeling sad" vs "I want to hurt myself")
   - Test STOP command
   - Review message history in database

3. **Run Tests**
   ```bash
   docker-compose exec api pytest -v --cov=src
   ```

4. **Review Logs**
   ```bash
   docker-compose logs -f api | grep ERROR
   ```

5. **Production Deployment**
   - See [DEPLOYMENT.md](DEPLOYMENT.md) for full guide
   - See [README.md](README.md) for detailed documentation

## Development Workflow

```bash
# Make code changes (hot reload enabled)
# Files in src/ are mounted as volume

# Run tests
make test

# Format code
make format

# Run linters
make lint

# Create migration after model changes
make migrate-create MSG="Add new field"

# Apply migrations
make migrate
```

## API Testing

### Health Check

```bash
curl http://localhost:8000/health
```

### SMS Webhook

```bash
curl -X POST http://localhost:8000/webhooks/sms \
  -H "Content-Type: application/json" \
  -d '[{
    "type": "message-received",
    "time": "2024-01-01T00:00:00Z",
    "message": {
      "id": "msg-123",
      "from": "+15551234567",
      "to": ["+15559876543"],
      "text": "What should I make for dinner?",
      "applicationId": "app-123"
    }
  }]'
```

### Check API Docs

Open browser: http://localhost:8000/docs

Interactive Swagger UI with:
- All endpoints documented
- Try it out feature
- Request/response schemas

## Database Inspection

```bash
# Connect to database
docker-compose exec postgres psql -U jules -d jules_dev

# List tables
\dt

# View users
SELECT id, phone_number, subscription_tier, created_at FROM users;

# View conversations
SELECT id, user_id, started_at, ended_at FROM conversations LIMIT 10;

# View messages (encrypted)
SELECT id, conversation_id, role, direction, created_at FROM messages LIMIT 10;

# Exit
\q
```

## Redis Inspection

```bash
# Connect to Redis
docker-compose exec redis redis-cli -a jules_redis_password

# List all keys
KEYS *

# Get a key value
GET context:user:1:conv:1

# Check TTL
TTL context:user:1:conv:1

# Exit
exit
```

## Tips

1. **Hot Reload**: Changes to Python files auto-reload (no restart needed)
2. **Database UI**: Use Adminer at http://localhost:8080 for visual DB management
3. **Redis UI**: Use Redis Commander at http://localhost:8081 for Redis visualization
4. **Logs**: Use `docker-compose logs -f api` to follow logs in real-time
5. **Tests**: Run tests frequently with `make test` during development

## Getting Help

- Check logs: `docker-compose logs api`
- Review docs: `README.md`, `DEPLOYMENT.md`
- Run health check: `curl http://localhost:8000/health`
- Test database: `docker-compose exec postgres psql -U jules -d jules_dev -c "SELECT 1"`

## Success!

If you can:
1. ✅ Access http://localhost:8000/health and see "healthy"
2. ✅ Send a test SMS webhook and get 200 response
3. ✅ See the message in database
4. ✅ Run tests successfully

You're ready to develop! 🚀

Next: Read [README.md](README.md) for full documentation.
