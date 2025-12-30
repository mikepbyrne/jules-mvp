# Jules - AI Household Companion

> Your family's meal planning assistant that lives in your text messages

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Jules is an AI-powered household companion that helps families plan meals, manage groceries, and build better eating habits through natural conversation via SMS. Unlike competitors that require daily app engagement, Jules lives entirely in your family's text messages.

## 🌟 Key Features

### SMS-First Communication
- **No app required** - Works entirely through text messages
- **Dual channel architecture** - Group planning and individual conversations
- **Full SMS compliance** - Proper opt-in/opt-out for all family members

### AI-Powered Recipe Management
- **Handwritten recipe extraction** - Digitize grandma's recipe cards with AI
- **Family recipe book** - Preserve treasured family recipes from photos, PDFs, URLs
- **Smart meal suggestions** - AI learns your family's preferences over time

### Collaborative Meal Planning
- **Family voting** - Everyone participates in weekly meal selection
- **Photo pantry scanning** - Update inventory by texting pictures
- **Intelligent shopping lists** - Auto-generated based on planned meals and pantry status

### Natural Conversation Interface
- **"What's for dinner?"** - Get instant answers based on plans and pantry
- **Recipe scaling** - "Make mom's lasagna for 12 people"
- **Ingredient substitutions** - "I don't have ricotta for the lasagna"

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 6+
- Twilio account (for SMS)
- OpenAI API key (for AI features)

### Environment Setup

1. **Clone the repository**
git clone https://github.com/yourusername/jules.git
cd jules

2. **Create virtual environment**
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. **Install dependencies**
pip install -r requirements.txt

4. **Set up environment variables**
cp .env.example .env
# Edit .env with your configuration

### Required Environment Variables

# Database
DATABASE_URL=postgresql://user:password@localhost/jules

# Redis
REDIS_URL=redis://localhost:6379

# Twilio SMS
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# OpenAI
OPENAI_API_KEY=your_openai_key

# AWS (for file storage)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=jules-uploads

# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# Environment
ENVIRONMENT=development
DEBUG=true

### Database Setup

1. **Create database**
createdb jules

2. **Run migrations**
alembic upgrade head

3. **Create initial data** (optional)
python scripts/seed_data.py

### Running the Application

1. **Start Redis**
redis-server

2. **Start Celery worker**
celery -A core.celery worker --loglevel=info

3. **Start the API server**
uvicorn main:app --reload --host 0.0.0.0 --port 8000

4. **Start the frontend** (in a new terminal)
cd web
npm install
npm run dev

The application will be available at:
- **API**: http://localhost:8000
- **Web Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## 📱 How Jules Works

### For Families

1. **Sign up** via web dashboard at jules.app
2. **Add family members** with phone numbers
3. **Members opt in** by replying YES to invitation text
4. **Start planning** - Jules texts the group every Sunday
5. **Vote on meals** - Family collaborates on weekly menu
6. **Get shopping list** - Delivered via text before shopping day
7. **Ask questions** - Text Jules individually anytime

### Sample Conversations

**Weekly Planning (Group Text)**
Jules: Happy Sunday! Ready to plan meals? I've got Taco Tuesday locked in. 
5 dinners to plan. Anyone eating out this week?

Dad: Thursday we have dinner plans
Mom: Wednesday might need something quick

Jules: Got it! Thursday out, Wednesday under 30 min. Here are Monday options:
1. Honey garlic salmon (30 min)
2. ⭐ Grandma's pot roast (Family recipe)
3. Chicken stir fry (25 min)
Vote by number!

Dad: 2
Mom: 2  
Teen: 1

Jules: Grandma's pot roast wins! Moving to Tuesday...

**Individual Questions**
You: What's for dinner tonight?
Jules: Tonight is honey garlic salmon with roasted broccoli. You should 
have everything except the salmon. Want me to send the recipe?

You: We just ran out of olive oil
Jules: Got it, marking olive oil as out. Added to the shopping list.

You: [photo of handwritten recipe card]
Jules: That looks like a recipe! Let me extract it...

I found: Mom's Lasagna
- 1 lb ground beef
- 1 jar marinara sauce  
- 15 oz ricotta cheese
[...full recipe...]

Does this look right?

## 🏗️ Architecture

### Tech Stack

**Backend**
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM with Alembic migrations
- **Celery + Redis** - Asynchronous task processing
- **Twilio** - SMS communication with provider fallback
- **OpenAI GPT-4V** - Multimodal AI for vision and language processing

**Frontend**
- **React 18** with TypeScript for type safety
- **Vite** for fast development and building
- **Tailwind CSS** for utility-first styling

**Infrastructure**
- **PostgreSQL 15+** - Primary database with JSON support
- **Redis 6+** - Session management and task queuing
- **AWS S3 + CloudFront** - File storage and CDN
- **Docker** - Containerization for deployment

### Project Structure

jules/
├── core/                   # Core application logic
│   ├── models/            # SQLAlchemy database models
│   ├── services/          # Business logic services
│   ├── integrations/      # External API integrations
│   └── utils/             # Shared utilities
├── api/                   # FastAPI routes and endpoints
│   ├── auth/              # Authentication endpoints
│   ├── households/        # Household management
│   ├── recipes/           # Recipe book functionality
│   ├── messaging/         # SMS handling
│   └── webhooks/          # External webhooks
├── workers/               # Celery background tasks
│   ├── ai_processing.py   # AI extraction tasks
│   ├── sms_tasks.py       # SMS sending/receiving
│   └── pantry_tasks.py    # Pantry scanning
├── web/                   # React frontend
│   ├── src/components/    # Reusable components
│   ├── src/pages/         # Page components
│   ├── src/services/      # API client
│   └── src/hooks/         # Custom React hooks
├── migrations/            # Alembic database migrations
├── tests/                 # Test suite
├── scripts/               # Utility scripts
└── docs/                  # Documentation

### Key Services

**SMS Service** (`core/services/sms_service.py`)
- Handles all Twilio interactions
- Message routing and delivery
- Opt-in/opt-out compliance

**AI Service** (`core/services/ai_service.py`)
- Recipe extraction from images
- Handwriting recognition
- Conversational processing

**Conversation Service** (`core/services/conversation_service.py`)
- State machine management
- Flow orchestration
- Context preservation

**Recipe Service** (`core/services/recipe_service.py`)
- Family recipe book management
- AI-powered extraction
- Original file preservation

## 🔧 Development

### Setting Up Development Environment

1. **Install development dependencies**
pip install -r requirements-dev.txt

2. **Install pre-commit hooks**
pre-commit install

3. **Run tests**
pytest

### Code Style

We use several tools to maintain code quality:

- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking

Run formatting:
black .
isort .

Run linting:
flake8 .
mypy .

### Testing

Run the full test suite:
pytest

Run with coverage:
pytest --cov=core --cov-report=html

Run specific tests:
pytest tests/test_sms_service.py
pytest -k "test_recipe_extraction"

### Database Migrations

Create new migration:
alembic revision --autogenerate -m "Add new feature"

Apply migrations:
alembic upgrade head

Rollback migration:
alembic downgrade -1

## 🔐 Security & Compliance

### SMS Compliance

Jules follows TCPA and CTIA guidelines:
- **Prior express consent** required before sending messages
- **Clear opt-out** instructions in every interaction
- **Immediate STOP processing** within seconds
- **Audit trail** of all consent actions

### Data Privacy

- **End-to-end encryption** for sensitive data
- **Automatic data retention** policies
- **COPPA compliance** for children under 13
- **Full data export** and deletion capabilities

### Security Features

- **JWT authentication** with refresh tokens
- **Rate limiting** on all endpoints
- **Input validation** and sanitization
- **SQL injection prevention** via SQLAlchemy ORM
- **XSS protection** in frontend

## 📊 Monitoring & Observability

### Logging

Structured logging with:
- **Correlation IDs** for request tracing
- **Security events** logging
- **Performance metrics** capture
- **Error context** preservation

### Metrics

Key metrics tracked:
- **SMS delivery rates** and failures
- **AI processing times** and accuracy
- **User engagement** patterns
- **System performance** indicators

### Error Handling

- **Sentry** integration for error tracking
- **Graceful degradation** for external service failures
- **Circuit breakers** for SMS and AI services
- **Retry mechanisms** with exponential backoff

## 🚀 Deployment

### Docker Deployment

1. **Build images**
docker-compose build

2. **Start services**
docker-compose up -d

### Environment-Specific Configs

**Development** (`docker-compose.yml`)
- Local PostgreSQL and Redis
- Debug mode enabled
- Hot reload for development

**Production** (`docker-compose.prod.yml`)
- External managed databases
- Health checks enabled
- Resource limits set
- SSL/TLS termination

### AWS Deployment

Terraform configurations provided for:
- **ECS** with Fargate for containerized services
- **RDS** for managed PostgreSQL
- **ElastiCache** for managed Redis
- **Application Load Balancer** with SSL
- **CloudFront** CDN for static assets
- **S3** for file storage

Deploy with:
cd terraform/
terraform init
terraform plan
terraform apply

## 📈 Performance

### Optimization Strategies

**Database**
- Indexed queries for common patterns
- Connection pooling with SQLAlchemy
- Read replicas for analytics queries
- Partitioning for large tables

**Caching**
- Redis for session data
- Application-level caching for AI responses
- CDN for static assets
- Database query result caching

**SMS Processing**
- Async message handling with Celery
- Bulk operations for group messages
- Rate limiting to prevent spam
- Intelligent retry logic

### Scaling Considerations

- **Horizontal scaling** via container orchestration
- **Database sharding** by household ID
- **AI service scaling** with dedicated GPU instances
- **Message queue partitioning** for high throughput

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Start for Contributors

1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/amazing-feature`)
3. **Install development dependencies** (`pip install -r requirements-dev.txt`)
4. **Make your changes**
5. **Add tests** for new functionality
6. **Run tests** (`pytest`)
7. **Run linting** (`black . && flake8 .`)
8. **Commit changes** (`git commit -m 'Add amazing feature'`)
9. **Push to branch** (`git push origin feature/amazing-feature`)
10. **Open Pull Request**

### Development Guidelines

- **Write tests** for all new features
- **Follow PEP 8** style guidelines
- **Add type hints** for all functions
- **Update documentation** for API changes
- **Keep commits small** and focused

## 📝 API Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

**Authentication**
- `POST /api/auth/register` - Create new household account
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/refresh` - Refresh JWT token

**Households**
- `GET /api/households/me` - Get current household info
- `PUT /api/households/me` - Update household settings
- `POST /api/households/members` - Add family member
- `PUT /api/households/members/{id}` - Update member info

**Recipes**
- `GET /api/recipes/family` - List family recipe book
- `POST /api/recipes/family` - Add new family recipe
- `POST /api/recipes/extract` - Extract recipe from image/URL
- `PUT /api/recipes/family/{id}` - Update family recipe

**Messaging**
- `POST /api/sms/webhook` - Twilio webhook handler
- `GET /api/conversations` - Get conversation history
- `POST /api/conversations/send` - Send message to household

**Meal Planning**
- `GET /api/meals/planned` - Get planned meals for week
- `POST /api/meals/plan` - Create meal plan
- `PUT /api/meals/planned/{id}` - Update planned meal

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** - For GPT-4V powering our AI features
- **Twilio** - For reliable SMS infrastructure
- **The open source community** - For the amazing tools and libraries

## 📞 Support

- **Documentation**: [docs.jules.app](https://docs.jules.app)
- **Email Support**: help@jules.app
- **GitHub Issues**: [github.com/jules/issues](https://github.com/jules/issues)
- **Community Discord**: [discord.gg/jules](https://discord.gg/jules)

---

**Jules - Where family meal planning becomes conversation, not chore.**

*Built with ❤️ for families who want to eat better together.*