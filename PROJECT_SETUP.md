# PROJECT SETUP

## Overview

Jules is an AI-powered household companion that helps families plan meals through SMS conversation. This setup guide will get you running locally and prepare you for production deployment.

## Prerequisites

### Required Software
- **Python 3.11+** - Core runtime
- **PostgreSQL 15+** - Primary database
- **Redis 6+** - Task queue and caching
- **Node.js 18+** - Frontend build tools
- **Docker & Docker Compose** - Local development environment

### Required Accounts
- **Twilio** - SMS messaging service
- **OpenAI** - AI/ML capabilities
- **AWS Account** - File storage and production infrastructure
- **Stripe** - Payment processing

### Development Tools
- **Git** - Version control
- **VS Code** or similar IDE
- **Postman** or similar API testing tool

## Quick Start with Docker

### 1. Clone Repository
git clone https://github.com/your-org/jules-ai.git
cd jules-ai

### 2. Environment Setup
cp .env.example .env

Edit `.env` with your credentials:
# Database
DATABASE_URL=postgresql://jules:jules123@localhost:5432/jules_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Twilio SMS
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# OpenAI
OPENAI_API_KEY=sk-your-openai-key

# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=jules-files-dev
AWS_REGION=us-east-1

# Application
SECRET_KEY=your-long-random-secret-key
ENVIRONMENT=development
DEBUG=true

### 3. Start Services
docker-compose up -d

This starts:
- PostgreSQL database on port 5432
- Redis on port 6379
- Backend API on port 8000
- Frontend on port 3000

### 4. Initialize Database
docker-compose exec backend alembic upgrade head
docker-compose exec backend python -m scripts.seed_dev_data

### 5. Verify Installation
- Backend API: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Health check: http://localhost:8000/health

## Manual Setup (Alternative)

### 1. Backend Setup

#### Install Python Dependencies
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

#### Database Setup
# Create database
createdb jules_dev

# Run migrations
alembic upgrade head

# Seed development data
python -m scripts.seed_dev_data

#### Start Backend Services
# Terminal 1: API server
uvicorn main:app --reload --port 8000

# Terminal 2: Celery worker
celery -A core.celery worker --loglevel=info

# Terminal 3: Celery scheduler
celery -A core.celery beat --loglevel=info

### 2. Frontend Setup

#### Install Dependencies
cd frontend
npm install

#### Start Development Server
npm run dev

Frontend available at http://localhost:3000

## Project Structure

jules-ai/
├── backend/                 # Python FastAPI backend
│   ├── alembic/            # Database migrations
│   ├── core/               # Core configuration and setup
│   │   ├── __init__.py
│   │   ├── config.py       # Settings and environment variables
│   │   ├── database.py     # Database connection
│   │   ├── celery.py       # Background task setup
│   │   └── security.py     # Authentication utilities
│   ├── models/             # SQLAlchemy database models
│   │   ├── __init__.py
│   │   ├── household.py    # Household and member models
│   │   ├── recipe.py       # Family recipe models
│   │   ├── pantry.py       # Pantry and inventory models
│   │   ├── conversation.py # SMS conversation state
│   │   └── message.py      # Message and communication models
│   ├── services/           # Business logic layer
│   │   ├── __init__.py
│   │   ├── sms_service.py  # SMS handling and routing
│   │   ├── ai_service.py   # OpenAI integration
│   │   ├── recipe_service.py # Recipe extraction and management
│   │   ├── pantry_service.py # Pantry scanning and tracking
│   │   ├── conversation_service.py # Conversation flow management
│   │   └── auth_service.py # Authentication and authorization
│   ├── api/                # FastAPI routes
│   │   ├── __init__.py
│   │   ├── auth.py         # Authentication endpoints
│   │   ├── households.py   # Household management
│   │   ├── members.py      # Member management
│   │   ├── recipes.py      # Family recipe book
│   │   ├── pantry.py       # Pantry management
│   │   ├── planning.py     # Meal planning
│   │   └── webhooks.py     # Twilio webhooks
│   ├── workers/            # Celery background tasks
│   │   ├── __init__.py
│   │   ├── ai_tasks.py     # AI processing tasks
│   │   ├── sms_tasks.py    # SMS sending tasks
│   │   └── scheduled_tasks.py # Recurring tasks
│   ├── utils/              # Utility functions
│   │   ├── __init__.py
│   │   ├── validators.py   # Input validation
│   │   ├── formatters.py   # Message formatting
│   │   └── helpers.py      # General helpers
│   ├── schemas/            # Pydantic models for API
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── household.py
│   │   ├── recipe.py
│   │   └── conversation.py
│   ├── tests/              # Test suite
│   │   ├── test_api/
│   │   ├── test_services/
│   │   └── test_models/
│   ├── scripts/            # Utility scripts
│   │   ├── seed_dev_data.py
│   │   └── migrate_data.py
│   ├── main.py             # FastAPI application entry point
│   ├── requirements.txt    # Python dependencies
│   └── alembic.ini         # Database migration config
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # Reusable React components
│   │   │   ├── common/     # Generic components
│   │   │   ├── auth/       # Authentication components
│   │   │   ├── dashboard/  # Dashboard components
│   │   │   ├── recipes/    # Recipe book components
│   │   │   ├── planning/   # Meal planning components
│   │   │   ├── pantry/     # Pantry management
│   │   │   └── members/    # Member management
│   │   ├── pages/          # Page components
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── RecipeBook.tsx
│   │   │   ├── MealPlanning.tsx
│   │   │   ├── Pantry.tsx
│   │   │   └── Settings.tsx
│   │   ├── hooks/          # Custom React hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useApi.ts
│   │   │   └── useWebSocket.ts
│   │   ├── services/       # API service layer
│   │   │   ├── api.ts      # Base API configuration
│   │   │   ├── auth.ts     # Authentication API
│   │   │   ├── households.ts
│   │   │   ├── recipes.ts
│   │   │   └── planning.ts
│   │   ├── utils/          # Frontend utilities
│   │   │   ├── formatters.ts
│   │   │   ├── validators.ts
│   │   │   └── constants.ts
│   │   ├── types/          # TypeScript type definitions
│   │   │   ├── auth.ts
│   │   │   ├── household.ts
│   │   │   ├── recipe.ts
│   │   │   └── api.ts
│   │   ├── styles/         # CSS and styling
│   │   │   └── globals.css
│   │   ├── App.tsx         # Main application component
│   │   └── main.tsx        # Application entry point
│   ├── public/             # Static assets
│   ├── package.json        # Node.js dependencies
│   ├── tsconfig.json       # TypeScript configuration
│   ├── vite.config.ts      # Vite build configuration
│   └── tailwind.config.js  # Tailwind CSS configuration
├── infrastructure/         # Infrastructure as code
│   ├── terraform/          # Terraform configurations
│   ├── docker/             # Docker configurations
│   └── scripts/            # Deployment scripts
├── docs/                   # Documentation
│   ├── api.md              # API documentation
│   ├── deployment.md       # Deployment guide
│   └── architecture.md     # System architecture
├── docker-compose.yml      # Local development environment
├── docker-compose.prod.yml # Production environment
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # Project overview

## Environment Configuration

### Development (.env)
# Application
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production
API_BASE_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql://jules:jules123@localhost:5432/jules_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Twilio (Development)
TWILIO_ACCOUNT_SID=your_dev_account_sid
TWILIO_AUTH_TOKEN=your_dev_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok.io

# OpenAI
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4-vision-preview

# AWS S3 (Development)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=jules-files-dev
AWS_REGION=us-east-1
AWS_CLOUDFRONT_DOMAIN=your-dev-cloudfront.amazonaws.com

# Email (Development)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@jules-dev.com

# Stripe (Development)
STRIPE_PUBLISHABLE_KEY=pk_test_your_key
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
DATADOG_API_KEY=your_datadog_key

# Feature Flags
ENABLE_RECIPE_EXTRACTION=true
ENABLE_PANTRY_SCANNING=true
ENABLE_GROUP_MESSAGING=true

### Production (.env.prod)
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=super-secure-production-key
API_BASE_URL=https://api.jules.ai

# Database
DATABASE_URL=postgresql://username:password@prod-db-host:5432/jules_prod

# Redis
REDIS_URL=redis://prod-redis-host:6379/0

# Twilio (Production)
TWILIO_ACCOUNT_SID=your_prod_account_sid
TWILIO_AUTH_TOKEN=your_prod_auth_token
TWILIO_PHONE_NUMBER=+1555123456
TWILIO_WEBHOOK_BASE_URL=https://api.jules.ai

# OpenAI
OPENAI_API_KEY=sk-your-production-openai-key
OPENAI_MODEL=gpt-4-vision-preview

# AWS S3 (Production)
AWS_ACCESS_KEY_ID=your_prod_access_key
AWS_SECRET_ACCESS_KEY=your_prod_secret_key
AWS_S3_BUCKET=jules-files-prod
AWS_REGION=us-east-1
AWS_CLOUDFRONT_DOMAIN=files.jules.ai

# Email (Production)
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your_ses_user
SMTP_PASSWORD=your_ses_password
FROM_EMAIL=noreply@jules.ai

# Stripe (Production)
STRIPE_PUBLISHABLE_KEY=pk_live_your_key
STRIPE_SECRET_KEY=sk_live_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_live_webhook_secret

# Monitoring
SENTRY_DSN=https://your-production-sentry-dsn@sentry.io/project
DATADOG_API_KEY=your_production_datadog_key

# Security
CORS_ORIGINS=https://jules.ai,https://www.jules.ai
ALLOWED_HOSTS=jules.ai,www.jules.ai,api.jules.ai

# Performance
WORKER_COUNT=4
MAX_REQUESTS_PER_WORKER=1000

## Database Setup

### Initial Migration
# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head

### Development Data
# Seed development data
python -m scripts.seed_dev_data

This creates:
- Test household with sample members
- Sample family recipes
- Pantry items for testing
- Conversation states for flow testing

### Database Schema

Key tables created by migrations:

**households** - Core household information
**members** - Family members with opt-in status
**family_recipes** - User-submitted recipes with AI extraction
**pantry_items** - Household inventory tracking
**conversation_states** - SMS conversation flow state
**messages** - All SMS communication history
**planned_meals** - Weekly meal planning
**shopping_lists** - Generated grocery lists

## External Service Setup

### Twilio SMS Configuration

1. **Create Twilio Account**
   - Sign up at https://twilio.com
   - Get Account SID and Auth Token
   - Purchase phone number

2. **Configure Webhooks**
   
   Webhook URL: https://yourdomain.com/api/webhooks/sms
   HTTP Method: POST
   

3. **Development with ngrok**
   bash
   # Install ngrok
   npm install -g ngrok
   
   # Expose local server
   ngrok http 8000
   
   # Update TWILIO_WEBHOOK_BASE_URL in .env
   

### OpenAI Configuration

1. **Get API Key**
   - Sign up at https://platform.openai.com
   - Generate API key
   - Add to environment variables

2. **Model Access**
   - Ensure access to GPT-4 Vision
   - Set usage limits for development

### AWS S3 Setup

1. **Create S3 Bucket**
   bash
   aws s3 mb s3://jules-files-dev
   aws s3 mb s3://jules-files-prod
   

2. **Set CORS Policy**
   
   {
     "CORSRules": [
       {
         "AllowedOrigins": ["https://yourdomain.com"],
         "AllowedMethods": ["GET", "PUT", "POST"],
         "AllowedHeaders": ["*"],
         "MaxAgeSeconds": 3000
       }
     ]
   }
   

3. **IAM User Policy**
   
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:GetObject",
           "s3:PutObject",
           "s3:DeleteObject"
         ],
         "Resource": "arn:aws:s3:::jules-files-*/*"
       }
     ]
   }
   

## Development Workflow

### Running Tests
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

### Code Quality
# Python formatting
black backend/
isort backend/

# Python linting
flake8 backend/
mypy backend/

# Frontend linting
cd frontend
npm run lint
npm run type-check

### Database Operations
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Reset database (development only)
alembic downgrade base
alembic upgrade head

## Common Development Tasks

### Adding a New API Endpoint

1. **Create Pydantic Schema**
   python
   # backend/schemas/new_feature.py
   from pydantic import BaseModel
   
   class NewFeatureRequest(BaseModel):
       name: str
       description: str
   
   class NewFeatureResponse(BaseModel):
       id: int
       name: str
       created_at: datetime
   

2. **Create Database Model**
   python
   # backend/models/new_feature.py
   from sqlalchemy import Column, Integer, String, DateTime
   from core.database import Base
   
   class NewFeature(Base):
       __tablename__ = "new_features"
       
       id = Column(Integer, primary_key=True)
       name = Column(String, nullable=False)
       created_at = Column(DateTime, default=datetime.utcnow)
   

3. **Create Service**
   python
   # backend/services/new_feature_service.py
   from models.new_feature import NewFeature
   from schemas.new_feature import NewFeatureRequest
   
   async def create_new_feature(request: NewFeatureRequest) -> NewFeature:
       feature = NewFeature(name=request.name)
       # Add to database
       return feature
   

4. **Create API Route**
   python
   # backend/api/new_features.py
   from fastapi import APIRouter, Depends
   from services.new_feature_service import create_new_feature
   
   router = APIRouter(prefix="/new-features", tags=["new-features"])
   
   @router.post("/", response_model=NewFeatureResponse)
   async def create_feature(request: NewFeatureRequest):
       return await create_new_feature(request)
   

5. **Add to Main App**
   python
   # backend/main.py
   from api.new_features import router as new_features_router
   
   app.include_router(new_features_router)
   

### Adding a Conversation Flow

1. **Define Flow States**
   python
   # backend/services/conversation_service.py
   class NewFlow(ConversationFlow):
       INITIAL = "initial"
       COLLECT_INFO = "collect_info"
       CONFIRM = "confirm"
       COMPLETE = "complete"
       
       async def handle_initial(self, message: str) -> FlowResponse:
           return FlowResponse(
               message="Starting new flow...",
               next_state=self.COLLECT_INFO
           )
   

2. **Register Flow**
   python
   # backend/services/conversation_service.py
   CONVERSATION_FLOWS = {
       "new_flow": NewFlow,
       # ... other flows
   }
   

3. **Add Trigger**
   python
   # backend/services/sms_service.py
   async def route_message(message: str, phone: str) -> None:
       if "start new flow" in message.lower():
           await start_conversation_flow("new_flow", phone)
   

### Adding a Frontend Component

1. **Create Component**
   typescript
   // frontend/src/components/NewFeature.tsx
   import React from 'react';
   
   interface NewFeatureProps {
     data: string;
   }
   
   export const NewFeature: React.FC<NewFeatureProps> = ({ data }) => {
     return (
       <div className="p-4 bg-white rounded-lg shadow">
         <h2 className="text-xl font-bold">{data}</h2>
       </div>
     );
   };
   

2. **Add API Service**
   typescript
   // frontend/src/services/newFeature.ts
   import { api } from './api';
   
   export interface NewFeatureData {
     id: number;
     name: string;
   }
   
   export const newFeatureService = {
     getAll: () => api.get<NewFeatureData[]>('/new-features'),
     create: (data: { name: string }) => 
       api.post<NewFeatureData>('/new-features', data),
   };
   

3. **Add to Page**
   typescript
   // frontend/src/pages/Dashboard.tsx
   import { NewFeature } from '../components/NewFeature';
   
   export const Dashboard: React.FC = () => {
     return (
       <div>
         <NewFeature data="Sample Data" />
       </div>
     );
   };
   

## Troubleshooting

### Common Issues

**Database Connection Failed**
# Check PostgreSQL is running
docker-compose ps
pg_isready -h localhost -p 5432

# Reset database
docker-compose down -v
docker-compose up -d db

**Redis Connection Failed**
# Check Redis is running
docker-compose ps
redis-cli ping

# Restart Redis
docker-compose restart redis

**SMS Webhooks Not Working**
# Check ngrok is running for development
ngrok http 8000

# Verify webhook URL in Twilio console
# Check server logs for incoming requests

**AI Processing Failures**
# Check OpenAI API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Check rate limits and usage
# Verify image processing pipeline

**File Upload Issues**
# Check S3 credentials
aws s3 ls s3://your-bucket-name

# Verify CORS configuration
# Check file size limits

### Log Locations

**Development Logs**
- Backend: Console output from uvicorn
- Frontend: Browser console
- Celery: Console output from worker

**Production Logs**
- Application: `/var/log/jules/app.log`
- Nginx: `/var/log/nginx/access.log`
- Database: PostgreSQL logs
- SMS: Twilio console

### Performance Monitoring

**Local Development**
# Monitor API performance
curl -w "@curl-format.txt" http://localhost:8000/health

# Monitor database queries
tail -f /var/log/postgresql/query.log

# Monitor Redis
redis-cli monitor

**Production Monitoring**
- Application: Sentry error tracking
- Infrastructure: DataDog metrics
- SMS: Twilio insights
- Database: AWS RDS monitoring

## Security Checklist

### Development Security
- [ ] Use environment variables for secrets
- [ ] Never commit API keys
- [ ] Use HTTPS for webhooks (ngrok)
- [ ] Validate all inputs
- [ ] Sanitize user uploads

### Production Security
- [ ] Rotate all API keys
- [ ] Enable database encryption
- [ ] Configure WAF rules
- [ ] Set up SSL certificates
- [ ] Enable audit logging
- [ ] Configure CORS properly
- [ ] Set rate limits
- [ ] Enable two-factor authentication

## Deployment

### Local Production Simulation
# Build production images
docker-compose -f docker-compose.prod.yml build

# Run production stack locally
docker-compose -f docker-compose.prod.yml up

### Production Deployment
See `docs/deployment.md` for detailed production deployment instructions including:
- AWS ECS configuration
- Load balancer setup
- Database migration
- SSL certificate setup
- Monitoring configuration

## Support

### Getting Help
- **Documentation**: Check `docs/` directory
- **Issues**: Create GitHub issue
- **API Docs**: http://localhost:8000/docs (when running)
- **Team Chat**: Slack #jules-dev channel

### Contributing
1. Fork repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request
5. Code review process
6. Merge to main

## Next Steps

After completing setup:

1. **Verify SMS Integration**
   - Send test message to your phone
   - Confirm webhooks receive responses
   - Test conversation flows

2. **Test AI Features**
   - Upload sample recipe images
   - Test pantry scanning
   - Verify recipe extraction

3. **Configure Production**
   - Set up AWS infrastructure
   - Configure monitoring
   - Plan deployment strategy

4. **Load Testing**
   - Test SMS message volume
   - Verify AI processing capacity
   - Monitor database performance

Ready to start building! 🚀