# Jules AI Household Companion - Architecture Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [System Architecture](#system-architecture)
4. [Component Architecture](#component-architecture)
5. [Data Architecture](#data-architecture)
6. [API Architecture](#api-architecture)
7. [SMS Communication Architecture](#sms-communication-architecture)
8. [AI Processing Architecture](#ai-processing-architecture)
9. [Security Architecture](#security-architecture)
10. [Infrastructure Architecture](#infrastructure-architecture)
11. [Deployment Architecture](#deployment-architecture)
12. [Monitoring & Observability](#monitoring--observability)
13. [Data Flow Patterns](#data-flow-patterns)
14. [Conversation State Management](#conversation-state-management)
15. [Scalability Design](#scalability-design)

## System Overview

Jules is an SMS-first AI household companion built on an event-driven microservices architecture. The system processes natural language conversations, extracts recipes from photos using computer vision, manages family meal planning workflows, and maintains compliance with SMS regulations.

### Core Design Philosophy

- **SMS-First**: All user interactions optimized for SMS delivery with fallback web interface
- **Event-Driven**: Asynchronous processing with message queues for scalability
- **AI-Centric**: Computer vision and NLP integrated throughout the user experience
- **Compliance-First**: TCPA/CTIA compliance built into every SMS interaction
- **Family-Focused**: Multi-member households with role-based permissions

## Architecture Principles

### 1. Separation of Concerns

Each service owns a specific domain with clear boundaries:
- SMS Service: Message routing and carrier integration
- AI Service: Computer vision and natural language processing
- Conversation Service: Workflow orchestration and state management
- Notification Service: Outbound message delivery with rate limiting

### 2. Event-Driven Design

Services communicate through Redis-backed message queues:
- Loose coupling between components
- Horizontal scaling of processing workloads
- Resilient failure handling with retry mechanisms
- Audit trail of all system events

### 3. Stateful Conversation Management

Finite state machines track conversation flows:
- Recipe extraction workflows
- Weekly planning voting processes
- Pantry scanning confirmations
- Member onboarding sequences

### 4. Compliance by Design

SMS regulations embedded in architecture:
- Opt-in state tracked in database with immutable audit log
- Rate limiting to prevent spam classification
- Automatic STOP keyword processing
- Geographic number validation

## System Architecture

┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   React Frontend    │    │   SMS Providers     │    │   AI Services       │
│   (Web Dashboard)   │    │   (Twilio, etc.)    │    │   (OpenAI, Custom)  │
└─────────┬───────────┘    └─────────┬───────────┘    └─────────┬───────────┘
          │                          │                          │
          │ HTTPS                    │ Webhook/API              │ API
          │                          │                          │
┌─────────▼───────────────────────────▼──────────────────────────▼───────────┐
│                           API Gateway (FastAPI)                            │
│                        Authentication & Rate Limiting                      │
└─────────┬─────────────────┬─────────────────┬─────────────────┬───────────┘
          │                 │                 │                 │
          │ HTTP            │ HTTP            │ HTTP            │ HTTP
          │                 │                 │                 │
┌─────────▼──────┐ ┌────────▼────────┐ ┌──────▼──────┐ ┌────────▼────────┐
│  SMS Service   │ │ Conversation    │ │ AI Service  │ │ Notification    │
│                │ │ Service         │ │             │ │ Service         │
│ • Twilio       │ │ • State Machine │ │ • GPT-4V    │ │ • Rate Limiting │
│ • Validation   │ │ • Flow Control  │ │ • Recipe AI │ │ • Delivery      │
│ • Compliance   │ │ • Context Mgmt  │ │ • Image OCR │ │ • Templates     │
└─────────┬──────┘ └────────┬────────┘ └──────┬──────┘ └────────┬────────┘
          │                 │                 │                 │
          │ Redis Events    │ Redis Events    │ Redis Events    │ Redis Events
          │                 │                 │                 │
└─────────▼─────────────────▼─────────────────▼─────────────────▼───────────┐
│                         Redis Event Bus                                    │
│                    • Message Queues                                        │
│                    • Pub/Sub Events                                        │
│                    • Session Storage                                       │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              │ Persistent Data
                              │
┌─────────────────────────────▼───────────────────────────────────────────┐
│                       PostgreSQL Database                               │
│                                                                         │
│ • Households & Members      • Family Recipes                          │
│ • Conversation State        • Pantry Items                            │
│ • Messages & Audit Logs     • Shopping Lists                          │
│ • Compliance Records        • Meal Plans                              │
└─────────────────────────────────────────────────────────────────────────┘

## Component Architecture

### Core Services

#### 1. SMS Service
**Responsibility**: SMS provider integration and message routing

# core/sms/service.py
class SMSService:
    def __init__(self):
        self.providers = {
            'primary': TwilioProvider(),
            'backup': AlternativeProvider()
        }
        
    async def send_message(self, to: str, message: str, channel: str):
        # Route to appropriate channel handler
        handler = self.get_channel_handler(channel)
        await handler.send(to, message)
        
    async def process_inbound(self, webhook_data: dict):
        # Parse provider-specific format
        message = self.parse_webhook(webhook_data)
        
        # Emit event to conversation service
        await self.event_bus.emit('message.received', message)

#### 2. Conversation Service
**Responsibility**: Workflow orchestration and state management

# core/conversation/service.py
class ConversationService:
    def __init__(self):
        self.state_machines = {
            'recipe_extraction': RecipeExtractionFlow(),
            'weekly_planning': WeeklyPlanningFlow(),
            'pantry_scan': PantryImageFlow()
        }
        
    async def handle_message(self, message: InboundMessage):
        # Determine conversation context
        context = await self.get_context(message.household_id, message.member_id)
        
        # Route to appropriate flow
        flow = self.determine_flow(message, context)
        response = await flow.process(message, context)
        
        # Send response via notification service
        await self.notification_service.send_response(response)

#### 3. AI Service
**Responsibility**: Computer vision and natural language processing

# core/ai/service.py
class AIService:
    def __init__(self):
        self.vision_client = OpenAIClient(model="gpt-4-vision-preview")
        self.nlp_client = OpenAIClient(model="gpt-4-turbo")
        
    async def extract_recipe(self, image_url: str) -> RecipeExtraction:
        # Process image with vision model
        prompt = self.get_recipe_extraction_prompt()
        response = await self.vision_client.analyze(image_url, prompt)
        
        # Structure response into recipe format
        return self.parse_recipe_response(response)
        
    async def identify_pantry_items(self, image_url: str) -> List[PantryItem]:
        # Identify items in pantry photo
        prompt = self.get_pantry_identification_prompt()
        response = await self.vision_client.analyze(image_url, prompt)
        
        return self.parse_pantry_response(response)

#### 4. Notification Service
**Responsibility**: Outbound message delivery with compliance

# core/notification/service.py
class NotificationService:
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.template_engine = TemplateEngine()
        
    async def send_individual(self, member_id: str, template: str, data: dict):
        # Check opt-in status
        member = await self.get_member(member_id)
        if not member.can_receive_individual_messages():
            return
            
        # Apply rate limiting
        await self.rate_limiter.check_individual_limit(member_id)
        
        # Send via SMS service
        message = self.template_engine.render(template, data)
        await self.sms_service.send_message(member.phone, message, 'individual')

### Supporting Components

#### Authentication Middleware
# core/auth/middleware.py
class AuthMiddleware:
    async def authenticate_request(self, request: Request):
        # Web dashboard: JWT token validation
        # SMS webhook: Provider signature verification
        # API access: API key validation
        pass

#### Database Models
# core/models/household.py
class Household(SQLAlchemyBase):
    __tablename__ = 'households'
    
    id = Column(UUID, primary_key=True)
    name = Column(String(255), nullable=False)
    budget_tier = Column(Enum(BudgetTier))
    timezone = Column(String(50), default='UTC')
    
    members = relationship("Member", back_populates="household")
    recipes = relationship("FamilyRecipe", back_populates="household")

#### Event Bus Implementation
# core/events/bus.py
class EventBus:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        
    async def emit(self, event_type: str, data: dict):
        event = Event(type=event_type, data=data, timestamp=utcnow())
        await self.redis.lpush(f"events:{event_type}", event.json())
        
    async def subscribe(self, event_type: str, handler: Callable):
        while True:
            event_data = await self.redis.brpop(f"events:{event_type}")
            event = Event.parse_raw(event_data[1])
            await handler(event)

## Data Architecture

### Database Design

#### Core Entities

**Households**
- Primary aggregation entity
- Subscription and billing anchor
- Timezone and preferences container

**Members**
- Individual users within household
- Opt-in status and communication preferences
- Role-based permissions (adult, teen, child)

**Family Recipes**
- User-submitted recipes with AI extraction
- Original file preservation
- Metadata and categorization

**Conversation State**
- Finite state machine persistence
- Flow-specific data storage
- Cross-session continuity

#### Data Relationships

-- Core relationship structure
households (1) → (*) members
households (1) → (*) family_recipes
households (1) → (*) conversation_states
households (1) → (*) planned_meals
households (1) → (*) shopping_lists
households (1) → (*) pantry_items

-- Cross-reference tables
planned_meals (*) → (?) family_recipes
conversation_states (*) → (1) members
messages (*) → (1) households
messages (*) → (?) members  -- null for group messages

#### Indexing Strategy

-- Performance-critical indexes
CREATE INDEX idx_members_phone ON members(phone_number);
CREATE INDEX idx_messages_household_timestamp ON messages(household_id, created_at);
CREATE INDEX idx_conversation_state_active ON conversation_states(household_id, member_id) 
    WHERE current_flow IS NOT NULL;
CREATE INDEX idx_family_recipes_search ON family_recipes 
    USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));

### Data Storage Patterns

#### Image Storage
- **Primary**: AWS S3 with CloudFront CDN
- **Organization**: `{household_id}/{type}/{year}/{month}/{file_id}.{ext}`
- **Lifecycle**: Original images preserved, thumbnails auto-generated
- **Security**: Signed URLs with expiration

#### JSON Data Storage
- **PostgreSQL JSONB** for flexible schema fields:
  - Recipe ingredients and instructions
  - Conversation flow state data
  - Member preferences and dietary restrictions
  - Shopping list items with metadata

#### Caching Strategy
- **Redis** for session data and frequently accessed objects:
  - Active conversation states
  - Member opt-in status cache
  - Rate limiting counters
  - Temporary AI processing results

## API Architecture

### RESTful Design

#### Resource Structure
/api/v1/
├── households/
│   ├── {household_id}/
│   │   ├── members/
│   │   ├── recipes/
│   │   ├── pantry/
│   │   ├── meals/
│   │   └── shopping-lists/
├── members/
│   └── {member_id}/
│       ├── conversations/
│       └── preferences/
├── sms/
│   ├── webhook/
│   └── status/
└── auth/
    ├── login/
    ├── register/
    └── refresh/

#### Authentication Flows

**Web Dashboard**
# JWT-based authentication
POST /api/v1/auth/login
{
    "email": "user@example.com",
    "password": "secure_password"
}

Response:
{
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "expires_in": 3600
}

**SMS Webhook**
# Signature verification
@app.post("/api/v1/sms/webhook")
async def sms_webhook(request: Request):
    # Verify Twilio signature
    signature = request.headers.get("X-Twilio-Signature")
    is_valid = twilio_validator.validate(request.url, request.body, signature)
    
    if not is_valid:
        raise HTTPException(401)

### OpenAPI Specification

openapi: 3.0.0
info:
  title: Jules AI API
  version: 1.0.0
  description: AI-powered household companion API

paths:
  /api/v1/households/{household_id}/recipes:
    post:
      summary: Submit family recipe
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                image:
                  type: string
                  format: binary
                url:
                  type: string
                  format: uri
                text:
                  type: string
      responses:
        202:
          description: Recipe extraction started
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ExtractionJob'

## SMS Communication Architecture

### Provider Integration

#### Primary Provider: Twilio
# integrations/sms/twilio.py
class TwilioProvider:
    def __init__(self, account_sid: str, auth_token: str):
        self.client = Client(account_sid, auth_token)
        
    async def send_message(self, to: str, body: str, from_: str):
        try:
            message = await self.client.messages.create(
                body=body,
                from_=from_,
                to=to
            )
            return SMSDeliveryResult(
                provider='twilio',
                message_id=message.sid,
                status='sent'
            )
        except TwilioException as e:
            # Fallback to secondary provider
            raise SMSDeliveryException(str(e))

#### Fallback Strategy
# core/sms/delivery.py
class SMSDeliveryService:
    def __init__(self):
        self.providers = [
            TwilioProvider(),
            BackupProvider()
        ]
    
    async def send_with_fallback(self, message: SMSMessage):
        for provider in self.providers:
            try:
                result = await provider.send(message)
                return result
            except SMSDeliveryException:
                continue
        
        raise AllProvidersFailedException()

### Message Routing

#### Channel Determination
# core/sms/routing.py
class MessageRouter:
    def determine_channel(self, message: InboundMessage) -> Channel:
        # Check if message is to group number
        if message.to_number == self.group_number:
            return Channel.GROUP
            
        # Individual message to member's direct line
        return Channel.INDIVIDUAL
    
    def get_recipients(self, household_id: str, channel: Channel) -> List[Member]:
        if channel == Channel.GROUP:
            return self.get_opted_in_adults(household_id)
        else:
            return [self.get_member_by_phone(message.from_number)]

### Compliance Implementation

#### Opt-In Tracking
# core/compliance/opt_in.py
class OptInManager:
    async def process_opt_in_response(self, phone: str, message: str):
        response_type = self.classify_response(message)
        
        if response_type == OptInResponse.ACCEPT:
            await self.activate_member(phone)
            await self.send_welcome_message(phone)
        elif response_type == OptInResponse.DECLINE:
            await self.mark_declined(phone)
            await self.send_decline_confirmation(phone)
            
    def classify_response(self, message: str) -> OptInResponse:
        positive_keywords = {'yes', 'y', 'yeah', 'sure', 'ok', 'okay'}
        negative_keywords = {'no', 'n', 'nope', 'stop', 'cancel'}
        
        message_lower = message.lower().strip()
        
        if any(word in message_lower for word in positive_keywords):
            return OptInResponse.ACCEPT
        elif any(word in message_lower for word in negative_keywords):
            return OptInResponse.DECLINE
        else:
            return OptInResponse.UNCLEAR

#### Rate Limiting
# core/compliance/rate_limiting.py
class SMSRateLimit:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        
    async def check_individual_limit(self, phone: str):
        # CTIA guidelines: max 10 messages per day
        key = f"sms_limit:individual:{phone}:{date.today().isoformat()}"
        count = await self.redis.incr(key)
        
        if count == 1:
            await self.redis.expire(key, 86400)  # 24 hours
            
        if count > 10:
            raise RateLimitExceededException("Daily individual limit exceeded")
    
    async def check_group_limit(self, household_id: str):
        # Conservative: max 5 group messages per day
        key = f"sms_limit:group:{household_id}:{date.today().isoformat()}"
        count = await self.redis.incr(key)
        
        if count == 1:
            await self.redis.expire(key, 86400)
            
        if count > 5:
            raise RateLimitExceededException("Daily group limit exceeded")

## AI Processing Architecture

### Computer Vision Pipeline

#### Recipe Extraction
# core/ai/vision.py
class RecipeExtractionPipeline:
    def __init__(self):
        self.vision_client = OpenAIVisionClient()
        self.ocr_client = OCRClient()
        self.nlp_client = OpenAINLPClient()
        
    async def extract_recipe(self, image_url: str) -> RecipeExtraction:
        # Step 1: Image preprocessing
        processed_image = await self.preprocess_image(image_url)
        
        # Step 2: Vision AI analysis
        vision_result = await self.vision_client.analyze(
            processed_image,
            prompt=self.get_recipe_extraction_prompt()
        )
        
        # Step 3: Structure extraction
        structured_recipe = await self.nlp_client.structure_recipe(
            vision_result.text,
            schema=RecipeSchema
        )
        
        # Step 4: Validation and confidence scoring
        return self.validate_and_score(structured_recipe)
        
    def get_recipe_extraction_prompt(self) -> str:
        return """
        Analyze this image and extract any recipes you find. 
        
        Look for:
        - Recipe title
        - Ingredients list with quantities
        - Step-by-step instructions
        - Cooking times and temperatures
        - Serving size
        
        Handle handwritten text, printed text, and mixed formats.
        If multiple recipes are present, extract all of them.
        Preserve original attribution if visible.
        
        Return structured JSON with confidence scores.
        """

#### Pantry Item Identification
# core/ai/pantry.py
class PantryVisionPipeline:
    async def identify_items(self, image_url: str) -> List[PantryItem]:
        # Specialized prompt for pantry/fridge/freezer contents
        vision_result = await self.vision_client.analyze(
            image_url,
            prompt=self.get_pantry_identification_prompt()
        )
        
        # Parse identified items
        items = self.parse_pantry_items(vision_result)
        
        # Estimate quantities where visible
        for item in items:
            item.quantity_estimate = self.estimate_quantity(item, vision_result)
            
        return items
        
    def get_pantry_identification_prompt(self) -> str:
        return """
        Identify all food items visible in this pantry/refrigerator/freezer image.
        
        For each item, provide:
        - Item name (normalized, e.g., "pasta" not "spaghetti noodles")
        - Quantity if visible (e.g., "3 cans", "half bag", "nearly full")
        - Confidence level (high/medium/low)
        - Location context if helpful (shelf, door, freezer)
        
        Focus on:
        - Packaged goods with visible labels
        - Fresh produce
        - Dairy products
        - Frozen items
        - Condiments and sauces
        
        Ignore non-food items.
        Group similar items (e.g., count all tomato cans together).
        """

### Natural Language Processing

#### Conversation Classification
# core/ai/conversation.py
class ConversationClassifier:
    def __init__(self):
        self.nlp_client = OpenAINLPClient()
        
    async def classify_intent(self, message: str, context: ConversationContext) -> Intent:
        prompt = f"""
        Classify the intent of this message in a family meal planning context:
        
        Message: "{message}"
        Previous context: {context.summary}
        
        Possible intents:
        - recipe_submission: User sharing a recipe to save
        - pantry_scan: User showing pantry/fridge contents
        - meal_request: User asking "what's for dinner?" or meal suggestions
        - shopping_list_update: Adding/removing items from shopping list
        - preference_update: Dietary restrictions or food preferences
        - general_question: Recipe details, cooking help, etc.
        
        Return the most likely intent with confidence score.
        """
        
        response = await self.nlp_client.complete(prompt)
        return self.parse_intent_response(response)

#### Recipe Generation
# core/ai/recipe_generation.py
class RecipeGenerator:
    async def generate_meal_suggestions(self, 
                                      pantry_items: List[PantryItem],
                                      preferences: List[Preference],
                                      constraints: MealConstraints) -> List[Recipe]:
        
        context = self.build_generation_context(pantry_items, preferences, constraints)
        
        prompt = f"""
        Suggest 3-4 meal options based on:
        
        Available ingredients: {context.pantry_summary}
        Dietary preferences: {context.preferences_summary}
        Constraints: {context.constraints_summary}
        
        For each suggestion, provide:
        - Meal name
        - Brief description
        - Prep time
        - Ingredients needed (mark what they already have)
        - Difficulty level
        
        Prioritize meals that use available ingredients.
        Consider family preferences and restrictions.
        Include at least one quick option under 30 minutes.
        """
        
        response = await self.nlp_client.complete(prompt)
        return self.parse_recipe_suggestions(response)

## Security Architecture

### Authentication & Authorization

#### JWT Implementation
# core/auth/jwt.py
class JWTManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        
    def create_access_token(self, member_id: str, household_id: str) -> str:
        payload = {
            "sub": member_id,
            "household_id": household_id,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
    def verify_token(self, token: str) -> TokenData:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return TokenData(**payload)
        except JWTError:
            raise InvalidTokenException()

#### Role-Based Access Control
# core/auth/permissions.py
class Permission(Enum):
    HOUSEHOLD_ADMIN = "household:admin"
    RECIPE_SUBMIT = "recipe:submit"
    MEAL_VOTE = "meal:vote"
    PANTRY_UPDATE = "pantry:update"

class RolePermissions:
    ROLES = {
        "account_holder": [
            Permission.HOUSEHOLD_ADMIN,
            Permission.RECIPE_SUBMIT,
            Permission.MEAL_VOTE,
            Permission.PANTRY_UPDATE
        ],
        "adult": [
            Permission.RECIPE_SUBMIT,
            Permission.MEAL_VOTE,
            Permission.PANTRY_UPDATE
        ],
        "teen": [
            Permission.RECIPE_SUBMIT,
            Permission.MEAL_VOTE
        ],
        "child": []  # No SMS permissions
    }

def require_permission(permission: Permission):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            member = await get_current_member(request)
            if not member.has_permission(permission):
                raise HTTPException(403, "Insufficient permissions")
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

### Data Protection

#### Encryption at Rest
# core/security/encryption.py
class DataEncryption:
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
        
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt PII like phone numbers"""
        return self.cipher.encrypt(data.encode()).decode()
        
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# Usage in models
class Member(SQLAlchemyBase):
    phone_number_encrypted = Column(Text)
    
    @property
    def phone_number(self) -> str:
        return encryption_service.decrypt_sensitive_data(self.phone_number_encrypted)
    
    @phone_number.setter
    def phone_number(self, value: str):
        self.phone_number_encrypted = encryption_service.encrypt_sensitive_data(value)

#### Input Validation
# core/security/validation.py
class InputValidator:
    PHONE_REGEX = re.compile(r'^\+1[0-9]{10}$')
    
    @classmethod
    def validate_phone_number(cls, phone: str) -> str:
        """Validate and normalize phone number to E.164 format"""
        # Remove non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Add country code if missing
        if len(digits) == 10:
            digits = '1' + digits
        elif len(digits) == 11 and digits.startswith('1'):
            pass
        else:
            raise ValidationException("Invalid phone number format")
            
        formatted = f"+{digits}"
        
        if not cls.PHONE_REGEX.match(formatted):
            raise ValidationException("Invalid phone number format")
            
        return formatted
    
    @classmethod
    def sanitize_message_content(cls, content: str) -> str:
        """Remove potential malicious content from messages"""
        # Remove potential injection attempts
        sanitized = content.replace('<', '&lt;').replace('>', '&gt;')
        
        # Truncate to reasonable length
        if len(sanitized) > 1600:  # SMS limit
            sanitized = sanitized[:1600] + "..."
            
        return sanitized

## Infrastructure Architecture

### Container Orchestration

#### Docker Configuration
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

#### AWS ECS Service Definition
{
  "family": "jules-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/julesTaskRole",
  "containerDefinitions": [
    {
      "name": "jules-api",
      "image": "jules-api:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "DATABASE_URL", "value": "postgresql://..."},
        {"name": "REDIS_URL", "value": "redis://..."}
      ],
      "secrets": [
        {"name": "TWILIO_AUTH_TOKEN", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/jules-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}

### Database Infrastructure

#### PostgreSQL Configuration
# RDS Configuration
Engine: postgres
EngineVersion: 15.4
DBInstanceClass: db.t3.medium
AllocatedStorage: 100
StorageType: gp3
StorageEncrypted: true
MultiAZ: true
BackupRetentionPeriod: 7
DeletionProtection: true

Parameters:
  shared_preload_libraries: pg_stat_statements
  log_statement: all
  log_min_duration_statement: 1000
  max_connections: 200

#### Redis Configuration
# ElastiCache Configuration
CacheNodeType: cache.t3.medium
Engine: redis
EngineVersion: 7.0
NumCacheNodes: 1
TransitEncryptionEnabled: true
AtRestEncryptionEnabled: true
AutomaticFailoverEnabled: false
MultiAZEnabled: false
SnapshotRetentionLimit: 5
SnapshotWindow: 03:00-04:00

### Content Delivery

#### S3 Bucket Structure
jules-images-prod/
├── households/
│   └── {household_id}/
│       ├── recipes/
│       │   └── {year}/
│       │       └── {month}/
│       │           └── {recipe_id}/
│       │               ├── original.{ext}
│       │               └── thumbnail.jpg
│       └── pantry/
│           └── {year}/
│               └── {month}/
│                   └── {scan_id}.{ext}
├── system/
│   └── placeholder-images/
└── temp/
    └── uploads/

#### CloudFront Distribution
{
  "DistributionConfig": {
    "Origins": [
      {
        "Id": "S3Origin",
        "DomainName": "jules-images-prod.s3.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": "origin-access-identity/cloudfront/..."
        }
      }
    ],
    "DefaultCacheBehavior": {
      "TargetOriginId": "S3Origin",
      "ViewerProtocolPolicy": "redirect-to-https",
      "CachePolicyId": "managed-caching-optimized",
      "Compress": true
    },
    "PriceClass": "PriceClass_100",
    "Enabled": true
  }
}

## Deployment Architecture

### Environment Configuration

#### Production Environment
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    image: jules-api:${VERSION}
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    secrets:
      - twilio_auth_token
      - openai_api_key
      - jwt_secret_key
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 30s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  worker:
    image: jules-worker:${VERSION}
    command: ["celery", "worker", "-A", "core.tasks", "--loglevel=info"]
    environment:
      - ENVIRONMENT=production
      - REDIS_URL=${REDIS_URL}
    deploy:
      replicas: 2

  scheduler:
    image: jules-worker:${VERSION}
    command: ["celery", "beat", "-A", "core.tasks", "--loglevel=info"]
    environment:
      - ENVIRONMENT=production
      - REDIS_URL=${REDIS_URL}
    deploy:
      replicas: 1

secrets:
  twilio_auth_token:
    external: true
  openai_api_key:
    external: true
  jwt_secret_key:
    external: true

#### CI/CD Pipeline
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit
          
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and push images
        run: |
          docker build -t jules-api:${{ github.sha }} .
          docker tag jules-api:${{ github.sha }} jules-api:latest
          # Push to ECR
          
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster jules-production \
            --service jules-api \
            --force-new-deployment

## Monitoring & Observability

### Application Monitoring

#### Health Checks
# core/health.py
class HealthChecker:
    def __init__(self):
        self.checks = {
            'database': self.check_database,
            'redis': self.check_redis,
            'sms_provider': self.check_sms_provider,
            'ai_service': self.check_ai_service
        }
    
    async def health_check(self) -> HealthStatus:
        results = {}
        overall_status = "healthy"
        
        for name, check_func in self.checks.items():
            try:
                result = await check_func()
                results[name] = result
                if result.status != "healthy":
                    overall_status = "degraded"
            except Exception as e:
                results[name] = HealthResult(status="unhealthy", error=str(e))
                overall_status = "unhealthy"
                
        return HealthStatus(status=overall_status, checks=results)

#### Metrics Collection
# core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# SMS metrics
sms_messages_sent = Counter('sms_messages_sent_total', 'SMS messages sent', ['channel', 'status'])
sms_delivery_duration = Histogram('sms_delivery_duration_seconds', 'SMS delivery time')

# AI processing metrics
ai_processing_duration = Histogram('ai_processing_duration_seconds', 'AI processing time', ['operation'])
ai_requests_total = Counter('ai_requests_total', 'AI requests', ['operation', 'status'])

# Conversation metrics
active_conversations = Gauge('active_conversations', 'Active conversation flows')
conversation_completion_rate = Counter('conversations_completed_total', 'Completed conversations', ['flow_type'])

# Usage in services
async def send_sms(self, message: SMSMessage):
    start_time = time.time()
    try:
        result = await self.provider.send(message)
        sms_messages_sent.labels(channel=message.channel, status='success').inc()
    except Exception as e:
        sms_messages_sent.labels(channel=message.channel, status='error').inc()
        raise
    finally:
        sms_delivery_duration.observe(time.time() - start_time)

#### Logging Strategy
# core/logging.py
import structlog

logger = structlog.get_logger()

class StructuredLogger:
    def __init__(self):
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.JSONRenderer()
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    def log_sms_sent(self, member_id: str, message_id: str, channel: str):
        logger.info("SMS sent", 
                   member_id=member_id,
                   message_id=message_id,
                   channel=channel,
                   service="sms")
    
    def log_recipe_extracted(self, household_id: str, recipe_id: str, confidence: float):
        logger.info("Recipe extracted",
                   household_id=household_id,
                   recipe_id=recipe_id,
                   confidence=confidence,
                   service="ai")

### Error Tracking

#### Sentry Integration
# core/error_tracking.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

def configure_sentry():
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[
            FastApiIntegration(auto_enabling_integrations=False),
            SqlalchemyIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
        before_send=filter_sensitive_data
    )

def filter_sensitive_data(event, hint):
    # Remove phone numbers and other PII from error reports
    if 'extra' in event:
        for key in list(event['extra'].keys()):
            if 'phone' in key.lower():
                event['extra'][key] = "[REDACTED]"
    return event

### Performance Monitoring

#### Database Query Monitoring
# core/database/monitoring.py
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    
    # Log slow queries
    if total > 1.0:  # 1 second threshold
        logger.warning("Slow query detected",
                      duration=total,
                      statement=statement[:100])
    
    # Record metrics
    db_query_duration.observe(total)

## Data Flow Patterns

### SMS Processing Flow

sequenceDiagram
    participant U as User
    participant T as Twilio
    participant S as SMS Service
    participant C as Conversation Service
    participant A as AI Service
    participant N as Notification Service
    participant D as Database
    
    U->>T: Sends SMS
    T->>S: Webhook notification
    S->>D: Store inbound message
    S->>C: Emit message.received event
    C->>D: Load conversation context
    C->>A: Process message (if needed)
    A-->>C: Return AI response
    C->>D: Update conversation state
    C->>N: Emit response.required event
    N->>S: Send outbound message
    S->>T: API call
    T->>U: Delivers SMS

### Recipe Extraction Flow

sequenceDiagram
    participant U as User
    participant S as SMS Service
    participant A as AI Service
    participant C as Conversation Service
    participant DB as Database
    participant S3 as S3 Storage
    
    U->>S: Sends photo + text
    S->>S3: Upload image
    S->>C: Trigger recipe extraction flow
    C->>DB: Create extraction job
    C->>A: Process image (async)
    A->>A: Vision AI analysis
    A->>DB: Store extraction result
    A->>C: Emit extraction.completed event
    C->>S: Send confirmation to user
    
    Note over C,S: User confirms/corrects
    
    S->>C: User confirmation
    C->>DB: Save final recipe
    C->>S: Send success confirmation

### Weekly Planning Flow

sequenceDiagram
    participant S as Scheduler
    participant C as Conversation Service
    participant D as Database
    participant N as Notification Service
    participant SMS as SMS Service
    participant F as Family Members
    
    S->>C: Trigger weekly planning
    C->>D: Load household preferences
    C->>D: Generate meal options
    C->>N: Send planning poll to group
    N->>SMS: Deliver group message
    SMS->>F: Planning poll SMS
    
    loop Voting Process
        F->>SMS: Vote responses
        SMS->>C: Process votes
        C->>D: Store votes
    end
    
    C->>C: Determine winners
    C->>D: Save meal plan
    C->>N: Send confirmation to group
    N->>SMS: Final plan message
    SMS->>F: Weekly plan confirmation

## Conversation State Management

### State Machine Design

#### Base State Machine
# core/conversation/state_machine.py
from enum import Enum
from typing import Dict, Any, Optional

class ConversationState(Enum):
    IDLE = "idle"
    WAITING_FOR_RESPONSE = "waiting_for_response"
    PROCESSING = "processing"
    CONFIRMING = "confirming"
    COMPLETED = "completed"
    ERROR = "error"

class ConversationFlow:
    def __init__(self, household_id: str, member_id: Optional[str] = None):
        self.household_id = household_id
        self.member_id = member_id
        self.state = ConversationState.IDLE
        self.data: Dict[str, Any] = {}
        
    async def process_message(self, message: InboundMessage) -> FlowResponse:
        handler = getattr(self, f"handle_{self.state.value}")
        return await handler(message)
        
    async def transition_to(self, new_state: ConversationState, data: Dict[str, Any] = None):
        if data:
            self.data.update(data)
        self.state = new_state
        await self.save_state()

#### Recipe Extraction State Machine
# core/conversation/flows/recipe_extraction.py
class RecipeExtractionFlow(ConversationFlow):
    
    async def handle_idle(self, message: InboundMessage) -> FlowResponse:
        # User sent image - start extraction
        if message.has_image:
            await self.transition_to(ConversationState.PROCESSING)
            
            # Start AI processing
            extraction_job = await self.ai_service.extract_recipe(message.image_url)
            await self.transition_to(
                ConversationState.WAITING_FOR_RESPONSE,
                {"extraction_job_id": extraction_job.id}
            )
            
            return FlowResponse(
                message="Got it! Let me take a look at this recipe...",
                requires_response=False
            )
    
    async def handle_waiting_for_response(self, message: InboundMessage) -> FlowResponse:
        # AI processing completed
        if message.type == MessageType.SYSTEM_EVENT:
            extraction_result = await self.get_extraction_result()
            
            await self.transition_to(
                ConversationState.CONFIRMING,
                {"extracted_recipe": extraction_result.recipe}
            )
            
            return FlowResponse(
                message=self.format_recipe_confirmation(extraction_result.recipe),
                requires_response=True
            )
    
    async def handle_confirming(self, message: InboundMessage) -> FlowResponse:
        response = message.content.lower().strip()
        
        if any(word in response for word in ['yes', 'perfect', 'correct', 'good']):
            # Save recipe
            recipe = await self.save_recipe(self.data["extracted_recipe"])
            await self.transition_to(ConversationState.COMPLETED)
            
            return FlowResponse(
                message=f"Saved {recipe.title} to your family recipe book! I can suggest it for meal planning now.",
                requires_response=False
            )
            
        elif any(word in response for word in ['no', 'wrong', 'fix']):
            # Handle corrections
            await self.transition_to(ConversationState.WAITING_FOR_RESPONSE)
            
            return FlowResponse(
                message="What needs to be fixed? You can tell me specifically what to change.",
                requires_response=True
            )

### Context Management

#### Conversation Context
# core/conversation/context.py
class ConversationContext:
    def __init__(self, household_id: str, member_id: Optional[str] = None):
        self.household_id = household_id
        self.member_id = member_id
        self._household_data: Optional[Household] = None
        self._member_data: Optional[Member] = None
        
    async def load_household_context(self):
        """Load household preferences, recipes, pantry, etc."""
        self._household_data = await self.db.get_household(self.household_id)
        
        return {
            "preferences": await self.get_household_preferences(),
            "pantry_items": await self.get_pantry_items(),
            "family_recipes": await self.get_family_recipes(),
            "recent_meals": await self.get_recent_meals(),
            "shopping_list": await self.get_current_shopping_list()
        }
    
    async def load_member_context(self):
        """Load individual member data"""
        if not self.member_id:
            return {}
            
        self._member_data = await self.db.get_member(self.member_id)
        
        return {
            "individual_preferences": await self.get_member_preferences(),
            "conversation_history": await self.get_recent_conversations(),
            "permissions": self._member_data.get_permissions()
        }

#### Cross-Channel Context Sharing
# core/conversation/cross_channel.py
class CrossChannelContextManager:
    async def get_shared_context(self, household_id: str) -> SharedContext:
        """Get context that should be available across all channels"""
        return SharedContext(
            planned_meals=await self.get_weekly_plan(household_id),
            pantry_status=await self.get_pantry_summary(household_id),
            active_shopping_list=await self.get_shopping_list(household_id),
            recent_family_decisions=await self.get_recent_group_decisions(household_id)
        )
    
    async def update_shared_context(self, household_id: str, update: ContextUpdate):
        """Update context that affects all channels"""
        if update.type == ContextUpdateType.PANTRY_UPDATE:
            await self.update_pantry(household_id, update.data)
            await self.notify_relevant_conversations(household_id, update)
        elif update.type == ContextUpdateType.RECIPE_ADDED:
            await self.add_to_family_recipes(household_id, update.data)
            await self.notify_meal_planning_flows(household_id, update)

## Scalability Design

### Horizontal Scaling Strategy

#### Service Scaling
# core/scaling/service_scaling.py
class ServiceScaler:
    def __init__(self):
        self.scaling_policies = {
            'sms_service': {
                'min_instances': 2,
                'max_instances': 10,
                'target_cpu_utilization': 70,
                'scale_up_cooldown': 300,  # 5 minutes
                'scale_down_cooldown': 600  # 10 minutes
            },
            'ai_service': {
                'min_instances': 1,
                'max_instances': 5,
                'target_memory_utilization': 80,
                'queue_length_threshold': 50
            }
        }
    
    async def check_scaling_triggers(self):
        for service, policy in self.scaling_policies.items():
            metrics = await self.get_service_metrics(service)
            
            if self.should_scale_up(metrics, policy):
                await self.scale_service(service, 'up')
            elif self.should_scale_down(metrics, policy):
                await self.scale_service(service, 'down')

#### Database Scaling
# core/database/scaling.py
class DatabaseScalingStrategy:
    def __init__(self):
        self.read_replicas = [
            'jules-db-read-1',
            'jules-db-read-2'
        ]
        
    async def get_database_connection(self, query_type: str = 'read'):
        if query_type == 'write':
            return await self.get_primary_connection()
        else:
            # Load balance across read replicas
            replica = self.select_read_replica()
            return await self.get_replica_connection(replica)
    
    def select_read_replica(self) -> str:
        # Simple round-robin, could be enhanced with health checking
        return random.choice(self.read_replicas)

# Usage in repositories
class HouseholdRepository:
    async def get_household(self, household_id: str) -> Household:
        # Read operation - use replica
        conn = await self.db_scaling.get_database_connection('read')
        return await conn.fetch_one(select_query, household_id)
    
    async def update_household(self, household: Household):
        # Write operation - use primary
        conn = await self.db_scaling.get_database_connection('write')
        return await conn.execute(update_query, household.dict())

### Performance Optimization

#### Caching Strategy
# core/caching/strategy.py
class CacheManager:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.cache_ttl = {
            'household_context': 300,    # 5 minutes
            'member_permissions': 3600,  # 1 hour
            'pantry_items': 1800,       # 30 minutes
            'family_recipes': 7200      # 2 hours
        }
    
    async def get_or_set(self, key: str, factory_func: Callable, ttl: int = None):
        # Try cache first
        cached_value = await self.redis.get(key)
        if cached_value:
            return json.loads(cached_value)
        
        # Cache miss - generate value
        value = await factory_func()
        
        # Store in cache
        cache_ttl = ttl or self.cache_ttl.get(key.split(':')[0], 300)
        await self.redis.setex(key, cache_ttl, json.dumps(value, default=str))
        
        return value

#### Background Processing
# core/tasks/celery_tasks.py
from celery import Celery

celery_app = Celery('jules', broker='redis://localhost:6379/0')

@celery_app.task(bind=True, max_retries=3)
async def extract_recipe_from_image(self, household_id: str, image_url: str):
    try:
        ai_service = AIService()
        extraction_result = await ai_service.extract_recipe(image_url)
        
        # Emit completion event
        await event_bus.emit('recipe.extraction.completed', {
            'household_id': household_id,
            'extraction_result': extraction_result.dict()
        })
        
    except Exception as exc:
        # Retry with exponential backoff
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown)

@celery_app.task
async def send_weekly_planning_reminders():
    """Weekly task to trigger meal planning for all households"""
    households = await get_households_needing_planning()
    
    for household in households:
        await conversation_service.start_weekly_planning_flow(household.id)

This architecture document provides a comprehensive technical blueprint for building Jules as an SMS-first AI household companion. The design emphasizes scalability, compliance, and the unique dual-channel communication model that sets Jules apart from app-based competitors.