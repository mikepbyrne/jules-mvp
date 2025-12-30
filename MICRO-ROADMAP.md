# MICRO-ROADMAP.md

## Jules AI Household Companion - MVP Development Roadmap

### Overview

This micro-roadmap breaks down the development of Jules MVP into 8 phases with 3-8 micro-tasks each. Each task is designed to take 1-4 hours and builds toward the five core MVP features: SMS-First Interface, Dual Channel Architecture, AI-Powered Handwritten Recipe Extraction, Conversational Meal Planning, and SMS Compliance and Opt-In System.

---

## Phase 1: Foundation & Infrastructure
**Duration:** 1-2 weeks  
**Goal:** Establish core backend infrastructure, database, and basic API structure

### Task 1.1: Project Setup & Environment Configuration (3 hours)
- Initialize FastAPI project with proper directory structure
- Set up Docker development environment with Python 3.11
- Configure environment variables and secrets management
- Create requirements.txt with core dependencies (FastAPI, SQLAlchemy, Celery, Redis)
- Set up basic CI/CD pipeline with GitHub Actions

### Task 1.2: Database Schema & Models (4 hours)
- Design PostgreSQL database schema based on data model
- Create SQLAlchemy models for core entities (Households, Members, Messages)
- Set up Alembic for database migrations
- Create initial migration files
- Add database connection pooling and configuration

### Task 1.3: Redis & Celery Setup (2 hours)
- Configure Redis for session storage and task queuing
- Set up Celery worker configuration
- Create basic task structure for async processing
- Test Redis connection and Celery task execution

### Task 1.4: Basic API Structure (3 hours)
- Create FastAPI app with proper middleware configuration
- Set up CORS, logging, and error handling
- Create health check endpoints
- Implement basic authentication middleware structure
- Add request/response logging

### Task 1.5: AWS Infrastructure Setup (4 hours)
- Configure AWS ECS for container deployment
- Set up Application Load Balancer
- Configure S3 buckets for file storage with proper permissions
- Set up CloudFront CDN for static assets
- Configure AWS SES for transactional emails

---

## Phase 2: SMS Infrastructure & Twilio Integration
**Duration:** 1-2 weeks  
**Goal:** Build robust SMS handling with proper routing and compliance

### Task 2.1: Twilio SDK Integration (3 hours)
- Install and configure Twilio Python SDK
- Set up webhook endpoints for inbound SMS
- Create outbound SMS service with rate limiting
- Implement SMS delivery status tracking
- Add error handling for failed SMS sends

### Task 2.2: SMS Message Processing Pipeline (4 hours)
- Create message ingestion service for inbound SMS
- Implement message validation and sanitization
- Build message routing logic for group vs individual threads
- Add message persistence to database
- Create async task queuing for message processing

### Task 2.3: Phone Number Management (3 hours)
- Implement E.164 phone number validation
- Create phone number normalization utilities
- Build lookup service for member identification
- Add support for multiple SMS provider fallbacks
- Implement phone number verification flow

### Task 2.4: SMS Rate Limiting & Compliance (2 hours)
- Implement per-number rate limiting
- Add SMS cost tracking and budget controls
- Create opt-out keyword detection (STOP, UNSUBSCRIBE, etc.)
- Build compliance audit logging
- Add message content validation for carrier requirements

### Task 2.5: Channel Detection & Routing (4 hours)
- Build logic to distinguish group vs individual messages
- Implement household context identification from phone numbers
- Create message threading and conversation grouping
- Add support for multiple members per household
- Build message history tracking per channel

---

## Phase 3: Authentication & Member Management
**Duration:** 1-2 weeks  
**Goal:** Implement secure authentication and compliant member invitation system

### Task 3.1: Web Authentication System (4 hours)
- Implement JWT-based authentication for web dashboard
- Create user registration and login endpoints
- Add password hashing with bcrypt
- Build session management and token refresh
- Implement password reset functionality

### Task 3.2: Household Creation & Management (3 hours)
- Create household registration API endpoints
- Build household settings management
- Implement household-level preference storage
- Add household subscription tier handling
- Create household deletion and data export

### Task 3.3: Member Invitation System (4 hours)
- Build member addition interface in web dashboard
- Create SMS invitation sending service
- Implement invitation tracking and status updates
- Add invitation expiration (7 days) logic
- Build invitation resend functionality with cooldowns

### Task 3.4: Opt-In/Opt-Out Compliance (3 hours)
- Implement explicit consent tracking for all members
- Create opt-in confirmation flow via SMS
- Build automatic opt-out processing for STOP keywords
- Add opt-out status persistence and enforcement
- Implement rejoin flow for previously opted-out members

### Task 3.5: Member Status Management (2 hours)
- Create member status tracking (pending, active, declined, opted_out)
- Build dashboard views for member status monitoring
- Add automatic status updates based on SMS responses
- Implement account holder notification system
- Create member activity timestamp tracking

---

## Phase 4: Basic Conversation Framework
**Duration:** 1-2 weeks  
**Goal:** Build conversation state management and basic SMS response system

### Task 4.1: Conversation State Machine (4 hours)
- Design finite state machine for conversation flows
- Implement state persistence in database
- Create state transition logic and validation
- Build conversation timeout and cleanup
- Add support for multiple concurrent conversations per household

### Task 4.2: Natural Language Intent Detection (3 hours)
- Integrate OpenAI API for intent classification
- Create intent detection service for common queries
- Build confidence scoring for intent matches
- Implement fallback responses for unrecognized intents
- Add conversation context awareness

### Task 4.3: Basic Response Generation (3 hours)
- Create response template system
- Build dynamic response generation with user context
- Implement response personalization based on member data
- Add response length optimization for SMS limits
- Create response queue management for multiple sends

### Task 4.4: Command Recognition System (2 hours)
- Implement keyword detection for SMS commands (HELP, LIST, etc.)
- Create command routing and execution
- Build help system with available commands
- Add command validation and error handling
- Implement context-aware command suggestions

### Task 4.5: Conversation Flow Testing (2 hours)
- Create unit tests for state machine transitions
- Build integration tests for conversation flows
- Add mock SMS testing infrastructure
- Create conversation simulation tools
- Implement conversation flow debugging tools

---

## Phase 5: AI-Powered Recipe Extraction
**Duration:** 2-3 weeks  
**Goal:** Build core AI functionality for handwritten recipe extraction and processing

### Task 5.1: Image Processing Pipeline (4 hours)
- Set up image upload handling to S3
- Implement image preprocessing (resize, enhance, rotate)
- Create image format validation and conversion
- Build image metadata extraction
- Add image compression and optimization

### Task 5.2: OpenAI Vision Integration (3 hours)
- Integrate GPT-4V for image analysis
- Create prompt engineering for recipe extraction
- Implement structured recipe parsing from vision output
- Add confidence scoring for extracted elements
- Build retry logic for failed extractions

### Task 5.3: Handwriting Recognition Service (4 hours)
- Build specialized prompts for handwritten recipe cards
- Implement OCR fallback for printed text
- Create handwriting confidence assessment
- Add support for mixed handwritten/printed content
- Build correction and clarification request system

### Task 5.4: Recipe Structuring & Validation (3 hours)
- Create recipe data model with ingredients, steps, metadata
- Implement ingredient parsing and normalization
- Build cooking time and serving size estimation
- Add recipe completeness validation
- Create nutrition estimation service

### Task 5.5: Recipe Extraction Workflow (3 hours)
- Build end-to-end extraction conversation flow
- Implement user confirmation and correction system
- Create recipe preview generation for SMS
- Add recipe saving with original image preservation
- Build extraction error handling and retry logic

### Task 5.6: Family Recipe Book Storage (2 hours)
- Create family recipe database schema
- Implement recipe search and categorization
- Build recipe tagging and collection system
- Add recipe sharing within household
- Create recipe export functionality

---

## Phase 6: Conversational Meal Planning
**Duration:** 2-3 weeks  
**Goal:** Implement intelligent meal suggestions and basic planning capabilities

### Task 6.1: Meal Suggestion Engine (4 hours)
- Build recipe database with diverse meal options
- Create meal suggestion algorithms based on preferences
- Implement dietary restriction filtering
- Add meal variety and rotation logic
- Build suggestion personalization based on household history

### Task 6.2: "What's for Dinner" Intelligence (4 hours)
- Create context-aware dinner suggestion system
- Implement pantry-based meal recommendations
- Build time-constraint filtering (quick meals, slow cooking)
- Add family recipe integration in suggestions
- Create ingredient-based meal matching

### Task 6.3: Basic Weekly Planning Flow (3 hours)
- Build simplified weekly planning conversation
- Implement meal selection and voting system
- Create plan persistence and modification
- Add standing ritual (Pizza Friday) support
- Build plan summary generation

### Task 6.4: Shopping List Generation (3 hours)
- Create ingredient aggregation from planned meals
- Implement shopping list formatting and organization
- Build pantry integration to avoid duplicate purchases
- Add quantity estimation for ingredients
- Create shopping list delivery via SMS

### Task 6.5: Preference Learning System (2 hours)
- Implement basic preference tracking from conversations
- Create meal rating and feedback collection
- Build preference inference from choices
- Add family member preference differentiation
- Create preference confidence scoring

---

## Phase 7: Dual Channel Architecture
**Duration:** 1-2 weeks  
**Goal:** Implement sophisticated channel routing and group communication

### Task 7.1: Group Thread Management (4 hours)
- Build group message broadcasting to opted-in members
- Implement household-wide conversation state
- Create group voting and polling system
- Add group message threading and context
- Build group activity tracking and metrics

### Task 7.2: Individual Thread Isolation (3 hours)
- Create member-specific conversation contexts
- Implement private query handling
- Build personal preference and history tracking
- Add individual message history and search
- Create cross-channel context sharing

### Task 7.3: Channel Selection Logic (3 hours)
- Build intelligent routing between group and individual channels
- Implement message type classification (group vs personal)
- Create escalation from individual to group conversations
- Add channel preference learning
- Build channel-appropriate response formatting

### Task 7.4: Cross-Channel Context Awareness (2 hours)
- Implement shared household state between channels
- Create context synchronization between individual and group threads
- Build awareness of group decisions in individual conversations
- Add cross-channel notification system
- Create context conflict resolution

### Task 7.5: Polling and Voting System (3 hours)
- Build SMS-based voting with number options
- Implement vote collection and tallying
- Create real-time vote status updates
- Add vote deadline and automatic closing
- Build voting result announcement system

---

## Phase 8: Web Dashboard & Integration
**Duration:** 2-3 weeks  
**Goal:** Build user-friendly web interface and complete system integration

### Task 8.1: React Frontend Setup (3 hours)
- Initialize React 18 project with TypeScript
- Set up Vite build tooling and development server
- Configure Tailwind CSS for styling
- Create basic routing with React Router
- Set up API client with proper error handling

### Task 8.2: Authentication & Dashboard Layout (4 hours)
- Build login and registration forms
- Create protected route system with JWT handling
- Design responsive dashboard layout
- Implement navigation and sidebar components
- Add user profile and household switching

### Task 8.3: Member Management Interface (3 hours)
- Create member addition and invitation forms
- Build member status display with visual indicators
- Implement invitation management (resend, cancel)
- Add member activity and message history views
- Create member role and permission management

### Task 8.4: Family Recipe Book Interface (4 hours)
- Build recipe upload interface (photo, PDF, URL)
- Create recipe gallery with search and filtering
- Implement recipe detail views with original image display
- Add recipe editing and metadata management
- Build recipe collection and tagging system

### Task 8.5: Meal Planning Dashboard (3 hours)
- Create weekly meal plan calendar view
- Build meal planning interface with drag-and-drop
- Implement shopping list view and management
- Add meal history and favorites tracking
- Create household settings and preferences interface

### Task 8.6: System Integration & Testing (4 hours)
- Connect frontend to backend APIs
- Implement real-time updates for SMS conversations
- Build comprehensive error handling and user feedback
- Add loading states and optimistic updates
- Create end-to-end testing for critical user flows

### Task 8.7: Mobile Responsiveness & Polish (2 hours)
- Optimize interface for mobile devices
- Implement touch-friendly interactions
- Add progressive web app (PWA) capabilities
- Create smooth animations and transitions
- Perform cross-browser compatibility testing

---

## Success Metrics & Testing

### Testing Strategy
- **Unit Tests:** Each service and utility function
- **Integration Tests:** API endpoints and database operations
- **SMS Flow Tests:** End-to-end conversation simulation
- **Load Tests:** High-volume SMS processing
- **Security Tests:** Authentication and data protection

### Performance Targets
- **SMS Response Time:** < 3 seconds for simple queries
- **Image Processing:** < 30 seconds for recipe extraction
- **Web Dashboard Load:** < 2 seconds initial load
- **Database Queries:** < 100ms for common operations
- **System Uptime:** 99.9% availability

### MVP Success Criteria
- **Technical:** All core features functional and tested
- **Compliance:** TCPA/CTIA compliance verified
- **Usability:** Intuitive SMS conversation flow
- **Performance:** Meets all response time targets
- **Security:** Data protection and privacy measures implemented

---

## Risk Mitigation

### Technical Risks
- **SMS Provider Downtime:** Multiple provider fallback system
- **AI Service Limits:** Rate limiting and queue management
- **Database Performance:** Connection pooling and query optimization
- **Image Processing Failures:** Graceful degradation and retry logic

### Compliance Risks
- **SMS Regulations:** Legal review of all messaging flows
- **Data Privacy:** GDPR/CCPA compliance implementation
- **Children's Privacy:** COPPA compliance for family features
- **Opt-out Enforcement:** Automated compliance monitoring

### Deployment Strategy
- **Staging Environment:** Complete production replica for testing
- **Feature Flags:** Gradual rollout of new capabilities
- **Monitoring:** Comprehensive logging and alerting
- **Rollback Plan:** Quick revert capability for critical issues

---

## Next Steps After MVP

### Post-MVP Enhancements
1. **Advanced Pantry Scanning:** Inventory tracking and expiration management
2. **Sophisticated Meal Planning:** Learning algorithms and advanced preferences
3. **Nutrition Intelligence:** Detailed nutritional analysis and health insights
4. **Budget Optimization:** Cost tracking and budget-conscious meal suggestions
5. **Integration Ecosystem:** Calendar, grocery delivery, and smart home integrations

### Scaling Considerations
- **Multi-tenant Architecture:** Efficient household isolation
- **Global SMS Support:** International phone number handling
- **Advanced AI Models:** Custom fine-tuned models for recipe extraction
- **Real-time Features:** WebSocket support for instant updates
- **Analytics Platform:** User behavior analysis and optimization

This roadmap provides a clear path to MVP while maintaining flexibility for iterative development and early user feedback integration.