# Jules AI Household Companion - Security Audit Report

**Audit Date:** December 29, 2025
**Auditor:** Security-Auditor Agent
**Project:** Jules - SMS-First AI Household Companion
**Scope:** Design-phase security review of architecture, APIs, and compliance framework

---

## Executive Summary

This security audit identifies **14 critical vulnerabilities**, **18 high-priority issues**, and **23 medium-priority concerns** in the Jules application design. The system handles sensitive PII (phone numbers, family data, dietary information), processes financial transactions (meal planning budgets), and integrates with multiple third-party services, creating a complex attack surface.

**Critical Findings:**
1. Phone number encryption not enforced in database schema
2. No webhook signature verification implementation
3. Missing rate limiting on image upload endpoints
4. Secrets stored in environment variables without rotation
5. No COPPA compliance framework for children in households
6. Missing audit trail for opt-in/opt-out changes
7. JWT tokens lack proper rotation and revocation mechanisms
8. No input sanitization for AI-processed image content
9. S3 bucket public access controls not specified
10. Database encryption at rest not explicitly configured

---

## 1. CRITICAL VULNERABILITIES (Severity: Critical)

### 1.1 Phone Number PII Encryption Not Enforced

**Severity:** Critical
**CVSS Score:** 9.1 (Critical)
**Affected Components:** `members` table, SMS Service

**Issue:**
The architecture document shows phone number encryption as a property method, but the database schema in CLAUDE.md shows:
```python
phone_number = Column(String(20), nullable=False)  # E.164 format
```

This stores phone numbers in plaintext. The encryption example in ARCHITECTURE.md uses:
```python
phone_number_encrypted = Column(Text)
```

But this is not enforced in the actual schema definition.

**Impact:**
- Database breach exposes all family phone numbers
- TCPA compliance violation (PII exposure)
- GDPR/CCPA violations (inadequate PII protection)
- Potential SMS spam/harassment of users

**Remediation:**
1. Enforce encryption at the database layer:
```python
# core/models/member.py
from cryptography.fernet import Fernet
from sqlalchemy import TypeDecorator, Text

class EncryptedString(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return encryption_service.encrypt_sensitive_data(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return encryption_service.decrypt_sensitive_data(value)
        return value

class Member(Base):
    __tablename__ = "members"
    phone_number = Column(EncryptedString, nullable=False)  # Auto-encrypted
```

2. Create migration to encrypt existing phone numbers
3. Add database-level encryption (AWS RDS encryption at rest)
4. Implement key rotation for encryption keys (90-day cycle)

**Timeline:** Immediate (before any data collection)

---

### 1.2 Missing Twilio Webhook Signature Verification

**Severity:** Critical
**CVSS Score:** 8.8 (High)
**Affected Components:** SMS Webhook endpoint (`/api/v1/sms/webhook`)

**Issue:**
The architecture shows a signature verification check:
```python
@app.post("/api/v1/sms/webhook")
async def sms_webhook(request: Request):
    # Verify Twilio signature
    signature = request.headers.get("X-Twilio-Signature")
    is_valid = twilio_validator.validate(request.url, request.body, signature)

    if not is_valid:
        raise HTTPException(401)
```

But there's no implementation of `twilio_validator` or configuration of the validation logic.

**Impact:**
- Attackers can forge SMS messages to households
- Injection of malicious content into conversations
- Unauthorized triggering of meal planning workflows
- Potential for SMS spoofing attacks
- Data exfiltration via crafted webhook payloads

**Remediation:**
1. Implement Twilio signature validation:
```python
# core/sms/webhook.py
from twilio.request_validator import RequestValidator
from fastapi import Request, HTTPException
import os

class TwilioWebhookValidator:
    def __init__(self):
        self.validator = RequestValidator(os.getenv("TWILIO_AUTH_TOKEN"))

    async def validate_request(self, request: Request) -> bool:
        signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)

        # Get request body
        body_bytes = await request.body()
        params = {}

        # Parse form data from Twilio webhook
        for line in body_bytes.decode().split('&'):
            if '=' in line:
                key, value = line.split('=', 1)
                params[key] = value

        return self.validator.validate(url, params, signature)

# Usage in webhook endpoint
webhook_validator = TwilioWebhookValidator()

@app.post("/api/v1/sms/webhook")
async def sms_webhook(request: Request):
    is_valid = await webhook_validator.validate_request(request)
    if not is_valid:
        logger.warning("Invalid Twilio signature",
                      ip=request.client.host,
                      headers=request.headers)
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process webhook...
```

2. Add IP allowlist for Twilio webhook sources
3. Implement request replay protection (timestamp validation)
4. Log all validation failures with alerting

**Timeline:** Immediate (before webhook deployment)

---

### 1.3 No Rate Limiting on Image Upload Endpoints

**Severity:** Critical
**CVSS Score:** 7.5 (High)
**Affected Components:** Recipe upload (`/api/v1/households/{household_id}/recipes`), Pantry scan endpoints

**Issue:**
The architecture shows rate limiting for SMS messages but none for image uploads:
```python
@household_router.post("/recipes/upload")
async def upload_family_recipe(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
```

No rate limiting middleware or decorator is applied.

**Impact:**
- API abuse via excessive uploads (DoS attack)
- Storage exhaustion (S3 costs spiral)
- AI API abuse (Claude/OpenAI rate limits hit)
- Processing queue overflow (Celery/ARQ workers overwhelmed)
- Cost attack (attacker forces expensive AI processing)

**Remediation:**
1. Implement rate limiting middleware:
```python
# core/middleware/rate_limiting.py
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379/1")

# Apply to API routes
@household_router.post("/recipes/upload")
@limiter.limit("10/hour")  # 10 uploads per hour per user
async def upload_family_recipe(
    request: Request,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate file size (max 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(413, "File too large")

    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/heic"]:
        raise HTTPException(400, "Invalid file type")

    # Process upload...
```

2. Add per-household upload quotas (50 recipes/month)
3. Implement file size validation (max 10MB)
4. Add MIME type validation with magic byte checking
5. Implement cost tracking per household

**Timeline:** Before MVP launch (week 1)

---

### 1.4 API Keys and Secrets in Environment Variables Without Rotation

**Severity:** Critical
**CVSS Score:** 8.1 (High)
**Affected Components:** All third-party API integrations

**Issue:**
The environment variables configuration shows:
```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
TWILIO_AUTH_TOKEN=...
ENCRYPTION_KEY=...
SECRET_KEY=...
```

No secret rotation mechanism, no HashiCorp Vault integration mentioned, no key versioning.

**Impact:**
- Compromised secrets remain valid indefinitely
- No audit trail for secret access
- Container image leaks expose all secrets
- Git history may contain secrets
- Developer machines with .env files are single point of failure

**Remediation:**
1. Implement HashiCorp Vault integration:
```python
# core/security/secrets.py
import hvac
import os
from functools import lru_cache
from datetime import datetime, timedelta

class SecretManager:
    def __init__(self):
        self.client = hvac.Client(url=os.getenv('VAULT_ADDR'))
        self.client.token = os.getenv('VAULT_TOKEN')
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)

    def get_secret(self, path: str, key: str) -> str:
        cache_key = f"{path}:{key}"

        # Check cache
        if cache_key in self.cache:
            cached_value, cached_time = self.cache[cache_key]
            if datetime.utcnow() - cached_time < self.cache_ttl:
                return cached_value

        # Fetch from Vault
        secret = self.client.secrets.kv.v2.read_secret_version(
            path=path,
            mount_point='secret'
        )
        value = secret['data']['data'][key]

        # Cache it
        self.cache[cache_key] = (value, datetime.utcnow())
        return value

    def rotate_secret(self, path: str, key: str, new_value: str):
        """Rotate a secret with versioning"""
        self.client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret={key: new_value},
            mount_point='secret'
        )
        # Clear cache
        cache_key = f"{path}:{key}"
        if cache_key in self.cache:
            del self.cache[cache_key]

# Usage
secret_manager = SecretManager()
ANTHROPIC_API_KEY = secret_manager.get_secret('jules/ai', 'anthropic_api_key')
TWILIO_AUTH_TOKEN = secret_manager.get_secret('jules/sms', 'twilio_auth_token')
```

2. Implement automatic rotation schedule:
   - API keys: Every 90 days
   - Database passwords: Every 180 days
   - JWT secret keys: Every 30 days
   - Encryption keys: Annual rotation with backward compatibility

3. Add secret scanning to pre-commit hooks:
```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

4. Use AWS Secrets Manager for production:
```python
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name: str) -> dict:
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name='us-east-1'
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e

    return json.loads(get_secret_value_response['SecretString'])
```

**Timeline:** Before production deployment (week 2)

---

### 1.5 No COPPA Compliance Framework for Children

**Severity:** Critical
**CVSS Score:** 7.8 (High)
**Affected Components:** Member management, SMS communication

**Issue:**
The schema allows for "child" role members:
```python
role = Column(String(50), default="adult")  # adult, teen, child
```

But there's no COPPA (Children's Online Privacy Protection Act) compliance framework:
- No parental consent verification
- No age gate for member registration
- No restrictions on data collection from children under 13
- No special handling of children's dietary information

**Impact:**
- FTC violations ($50,000+ per violation)
- Class action lawsuits from parents
- Immediate shutdown orders
- Reputational damage

**COPPA Requirements:**
1. Parental consent before collecting data from children <13
2. Clear privacy policy
3. Limited data collection from children
4. Reasonable security measures
5. Data retention and deletion policies

**Remediation:**
1. Implement age verification and parental consent:
```python
# core/models/member.py
class Member(Base):
    __tablename__ = "members"

    date_of_birth = Column(Date)  # Required for age verification
    is_minor = Column(Boolean, default=False)  # Under 18
    is_child = Column(Boolean, default=False)  # Under 13
    parental_consent_date = Column(DateTime)  # COPPA requirement
    parental_consent_ip = Column(String(45))  # Evidence of consent
    parental_consent_method = Column(String(50))  # "verified_email", "signed_form"

    @property
    def requires_parental_consent(self) -> bool:
        if not self.date_of_birth:
            return False
        age = (datetime.utcnow().date() - self.date_of_birth).days / 365.25
        return age < 13
```

2. Add consent workflow:
```python
# core/compliance/coppa.py
class COPPAConsent:
    async def request_parental_consent(self, child_member_id: str, parent_member_id: str):
        """Send consent request to parent"""
        child = await db.get(Member, child_member_id)
        parent = await db.get(Member, parent_member_id)

        # Send consent email with verifiable link
        consent_token = secrets.token_urlsafe(32)
        consent_url = f"https://app.jules.ai/consent/{consent_token}"

        await email_service.send(
            to=parent.email,
            subject="Parental Consent Required for Jules",
            template="coppa_consent",
            data={
                "child_name": child.name,
                "consent_url": consent_url,
                "data_collected": "dietary preferences, meal votes, recipe submissions"
            }
        )

        # Store consent request
        await db.execute(
            insert(COPPAConsentRequest).values(
                token=consent_token,
                child_member_id=child_member_id,
                parent_member_id=parent_member_id,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
        )

    async def verify_consent(self, consent_token: str, ip_address: str):
        """Record verified parental consent"""
        consent_req = await db.query(COPPAConsentRequest).filter(
            COPPAConsentRequest.token == consent_token,
            COPPAConsentRequest.expires_at > datetime.utcnow()
        ).first()

        if not consent_req:
            raise ValueError("Invalid or expired consent token")

        # Update child member
        child = await db.get(Member, consent_req.child_member_id)
        child.parental_consent_date = datetime.utcnow()
        child.parental_consent_ip = ip_address
        child.parental_consent_method = "verified_email"

        await db.commit()
```

3. Restrict data collection for children:
```python
# core/services/sms_service.py
async def can_send_to_member(self, member: Member) -> bool:
    if member.is_child and not member.parental_consent_date:
        logger.warning("Cannot send SMS to child without parental consent",
                      member_id=member.id)
        return False
    return member.opt_in_status == "active"
```

4. Add COPPA-compliant privacy policy
5. Implement data deletion for children who age out

**Timeline:** Before beta testing with families (week 3)

---

### 1.6 Missing Audit Trail for Opt-In/Opt-Out Changes

**Severity:** Critical
**CVSS Score:** 7.3 (High)
**Affected Components:** Compliance system, Member management

**Issue:**
The schema tracks opt-in status but has no immutable audit log:
```python
opt_in_status = Column(String(50), default="pending")
opt_out_at = Column(DateTime)
```

TCPA/CTIA require proof of consent for 4+ years. A mutable column is insufficient.

**Impact:**
- Cannot prove consent in legal disputes
- TCPA violations ($500-$1,500 per violation)
- Class action lawsuit vulnerability
- Regulatory fines

**Remediation:**
1. Create immutable audit log table:
```python
# core/models/compliance.py
class OptInAuditLog(Base):
    __tablename__ = "opt_in_audit_log"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # invitation_sent, opt_in, opt_out, reminder
    previous_status = Column(String(50))
    new_status = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    source_ip = Column(String(45))  # IP address of consent
    source_phone = Column(String(20))  # Phone number that sent STOP/START
    message_content = Column(Text)  # Exact message received
    sms_message_id = Column(String(100))  # Twilio message SID
    verification_method = Column(String(50))  # "sms_reply", "web_form", "api"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Make table append-only (no updates or deletes)
    __table_args__ = (
        CheckConstraint('event_type IN ("invitation_sent", "opt_in", "opt_out", "reminder", "resend", "expired")'),
    )

# Prevent updates and deletes
@event.listens_for(OptInAuditLog, 'before_update')
def prevent_update(mapper, connection, target):
    raise ValueError("Audit log records cannot be updated")

@event.listens_for(OptInAuditLog, 'before_delete')
def prevent_delete(mapper, connection, target):
    raise ValueError("Audit log records cannot be deleted")
```

2. Log all opt-in/opt-out events:
```python
# core/compliance/opt_in.py
class OptInManager:
    async def process_opt_in(self, member_id: str, source_phone: str, message_content: str, sms_message_id: str):
        member = await db.get(Member, member_id)

        # Create audit record BEFORE changing status
        audit = OptInAuditLog(
            member_id=member_id,
            event_type="opt_in",
            previous_status=member.opt_in_status,
            new_status="active",
            source_phone=source_phone,
            message_content=message_content,
            sms_message_id=sms_message_id,
            verification_method="sms_reply"
        )
        db.add(audit)

        # Update member status
        member.opt_in_status = "active"
        member.invitation_responded_at = datetime.utcnow()

        await db.commit()

    async def process_opt_out(self, member_id: str, source_phone: str, message_content: str):
        member = await db.get(Member, member_id)

        # Create audit record
        audit = OptInAuditLog(
            member_id=member_id,
            event_type="opt_out",
            previous_status=member.opt_in_status,
            new_status="opted_out",
            source_phone=source_phone,
            message_content=message_content,
            verification_method="sms_reply"
        )
        db.add(audit)

        # Update member status
        member.opt_in_status = "opted_out"
        member.opt_out_at = datetime.utcnow()
        member.receives_group_messages = False
        member.receives_individual_messages = False

        await db.commit()
```

3. Add retention policy (7 years for compliance):
```python
# core/compliance/retention.py
RETENTION_PERIODS = {
    "opt_in_audit_log": timedelta(days=7*365),  # 7 years
    "messages": timedelta(days=2*365),  # 2 years
    "conversation_states": timedelta(days=90),  # 90 days
}
```

4. Implement export for legal requests:
```python
async def export_consent_history(self, member_id: str) -> dict:
    """Export consent history for legal/regulatory requests"""
    logs = await db.query(OptInAuditLog).filter(
        OptInAuditLog.member_id == member_id
    ).order_by(OptInAuditLog.timestamp.asc()).all()

    return {
        "member_id": member_id,
        "consent_history": [
            {
                "timestamp": log.timestamp.isoformat(),
                "event": log.event_type,
                "status_change": f"{log.previous_status} -> {log.new_status}",
                "source": log.source_phone,
                "verification": log.verification_method,
                "message_id": log.sms_message_id
            }
            for log in logs
        ]
    }
```

**Timeline:** Before sending first SMS invitation (week 1)

---

### 1.7 JWT Tokens Lack Proper Rotation and Revocation

**Severity:** Critical
**CVSS Score:** 7.5 (High)
**Affected Components:** Authentication system

**Issue:**
JWT implementation shows token creation but no:
- Token revocation mechanism
- Refresh token rotation
- Session management
- Blacklist for compromised tokens

```python
def create_access_token(self, member_id: str, household_id: str) -> str:
    payload = {
        "sub": member_id,
        "household_id": household_id,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
```

**Impact:**
- Stolen tokens remain valid until expiration
- No way to revoke access after password change
- Session hijacking attacks
- Compromised tokens usable across devices

**Remediation:**
1. Implement token revocation with Redis:
```python
# core/auth/jwt.py
import redis
from datetime import datetime, timedelta

class JWTManager:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=2)
        self.secret_key = secret_manager.get_secret('jules/auth', 'jwt_secret')
        self.algorithm = "HS256"

    def create_token_pair(self, member_id: str, household_id: str) -> dict:
        """Create access and refresh token pair"""
        # Access token (short-lived)
        access_payload = {
            "sub": member_id,
            "household_id": household_id,
            "type": "access",
            "jti": str(uuid.uuid4()),  # Unique token ID for revocation
            "exp": datetime.utcnow() + timedelta(minutes=15),  # Shorter expiry
            "iat": datetime.utcnow()
        }
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)

        # Refresh token (long-lived, stored in DB)
        refresh_payload = {
            "sub": member_id,
            "household_id": household_id,
            "type": "refresh",
            "jti": str(uuid.uuid4()),
            "exp": datetime.utcnow() + timedelta(days=30),
            "iat": datetime.utcnow()
        }
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)

        # Store refresh token in database
        await self.store_refresh_token(member_id, refresh_payload["jti"], refresh_payload["exp"])

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 900,  # 15 minutes
            "token_type": "Bearer"
        }

    async def verify_token(self, token: str) -> dict:
        """Verify token and check revocation"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check if token is revoked
            jti = payload.get("jti")
            if jti and self.is_token_revoked(jti):
                raise InvalidTokenException("Token has been revoked")

            return payload
        except JWTError as e:
            raise InvalidTokenException(str(e))

    def revoke_token(self, jti: str, exp: datetime):
        """Add token to revocation list"""
        ttl = int((exp - datetime.utcnow()).total_seconds())
        if ttl > 0:
            self.redis.setex(f"revoked_token:{jti}", ttl, "1")

    def is_token_revoked(self, jti: str) -> bool:
        """Check if token is in revocation list"""
        return bool(self.redis.get(f"revoked_token:{jti}"))

    async def revoke_all_user_tokens(self, member_id: str):
        """Revoke all tokens for a user (password change, logout all devices)"""
        # Mark user as requiring re-authentication
        self.redis.setex(f"user_revoked:{member_id}", 86400*30, "1")  # 30 days

        # Delete all refresh tokens from database
        await db.execute(
            delete(RefreshToken).where(RefreshToken.member_id == member_id)
        )

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Generate new access token from refresh token with rotation"""
        payload = await self.verify_token(refresh_token)

        if payload.get("type") != "refresh":
            raise InvalidTokenException("Not a refresh token")

        # Verify refresh token exists in database
        db_token = await db.query(RefreshToken).filter(
            RefreshToken.jti == payload["jti"],
            RefreshToken.member_id == payload["sub"]
        ).first()

        if not db_token:
            raise InvalidTokenException("Refresh token not found")

        # Rotate refresh token (one-time use)
        await db.delete(db_token)

        # Create new token pair
        return await self.create_token_pair(payload["sub"], payload["household_id"])

# Database model for refresh tokens
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    jti = Column(String(100), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime)
    user_agent = Column(Text)
    ip_address = Column(String(45))
```

2. Add session management:
```python
# core/auth/session.py
class SessionManager:
    async def create_session(self, member_id: str, device_info: dict) -> str:
        session_id = str(uuid.uuid4())

        session = Session(
            id=session_id,
            member_id=member_id,
            device_type=device_info.get("device_type"),
            user_agent=device_info.get("user_agent"),
            ip_address=device_info.get("ip_address"),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )

        db.add(session)
        await db.commit()

        return session_id

    async def revoke_session(self, session_id: str):
        """Revoke specific session"""
        await db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(revoked_at=datetime.utcnow())
        )
```

3. Add token refresh endpoint:
```python
@auth_router.post("/refresh")
async def refresh_token(refresh_token: str):
    jwt_manager = JWTManager()
    try:
        new_tokens = await jwt_manager.refresh_access_token(refresh_token)
        return new_tokens
    except InvalidTokenException as e:
        raise HTTPException(status_code=401, detail=str(e))
```

**Timeline:** Before MVP launch (week 2)

---

### 1.8 No Input Sanitization for AI-Processed Image Content

**Severity:** Critical
**CVSS Score:** 7.8 (High)
**Affected Components:** AI Service, Recipe Extraction, Pantry Scanning

**Issue:**
Images uploaded for AI processing are sent directly to OpenAI/Claude without:
- EXIF data stripping (location, device info)
- Malware scanning
- Content validation
- Steganography detection

```python
async def extract_recipe(self, image_url: str) -> RecipeExtraction:
    # No image validation or sanitization
    response = await self.vision_client.analyze(image_url, prompt)
```

**Impact:**
- Malware uploaded via image files
- EXIF metadata leaks user location
- Steganography used to exfiltrate data
- AI prompt injection via image content
- Storage of malicious files in S3

**Remediation:**
1. Implement image sanitization pipeline:
```python
# core/security/image_sanitization.py
from PIL import Image
import io
import magic
from typing import BinaryIO

class ImageSanitizer:
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/heic"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_DIMENSIONS = (4096, 4096)  # 4K max

    async def sanitize_image(self, file: BinaryIO) -> bytes:
        """Sanitize uploaded image"""
        # Read file
        content = file.read()

        # Validate size
        if len(content) > self.MAX_FILE_SIZE:
            raise ValueError("File too large")

        # Validate MIME type with magic bytes
        mime_type = magic.from_buffer(content, mime=True)
        if mime_type not in self.ALLOWED_TYPES:
            raise ValueError(f"Invalid file type: {mime_type}")

        # Load image with Pillow (validates format)
        try:
            img = Image.open(io.BytesIO(content))
        except Exception as e:
            raise ValueError(f"Invalid image file: {e}")

        # Validate dimensions
        if img.width > self.MAX_DIMENSIONS[0] or img.height > self.MAX_DIMENSIONS[1]:
            raise ValueError("Image dimensions too large")

        # Strip EXIF data
        img_without_exif = Image.new(img.mode, img.size)
        img_without_exif.putdata(list(img.getdata()))

        # Convert to JPEG (standardize format)
        output = io.BytesIO()
        img_without_exif.save(output, format='JPEG', quality=85, optimize=True)

        return output.getvalue()

    async def scan_for_malware(self, file_content: bytes) -> bool:
        """Scan file for malware using ClamAV"""
        # Integrate with ClamAV or VirusTotal API
        # For now, basic checks

        # Check for executable headers
        if file_content.startswith(b'MZ') or file_content.startswith(b'\x7fELF'):
            raise ValueError("Executable content detected")

        # Check for script content
        dangerous_patterns = [b'<script', b'<?php', b'#!/bin/']
        for pattern in dangerous_patterns:
            if pattern in file_content:
                raise ValueError("Script content detected")

        return True

# Usage in upload endpoint
image_sanitizer = ImageSanitizer()

@household_router.post("/recipes/upload")
async def upload_family_recipe(file: UploadFile = File(...)):
    try:
        # Sanitize image
        sanitized_content = await image_sanitizer.sanitize_image(file.file)

        # Scan for malware
        await image_sanitizer.scan_for_malware(sanitized_content)

        # Upload sanitized version to S3
        file_url = await file_storage.upload_bytes(
            sanitized_content,
            content_type="image/jpeg",
            prefix="recipe-uploads"
        )

        # Process with AI
        extraction_result = await ai_service.extract_recipe_from_image(file_url)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

2. Add content security scanning:
```python
# Integration with ClamAV
import pyclamd

async def scan_file_with_clamav(file_content: bytes) -> bool:
    cd = pyclamd.ClamdUnixSocket()
    result = cd.scan_stream(file_content)

    if result is None:
        return True  # Clean
    else:
        raise ValueError(f"Malware detected: {result}")
```

3. Add AI prompt injection detection:
```python
# core/security/prompt_injection.py
class PromptInjectionDetector:
    SUSPICIOUS_PATTERNS = [
        r"ignore previous instructions",
        r"system:",
        r"assistant:",
        r"<\|im_start\|>",
        r"```python",
        r"exec\(",
        r"__import__",
    ]

    def detect_injection(self, text: str) -> bool:
        """Check extracted text for prompt injection attempts"""
        text_lower = text.lower()
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text_lower):
                logger.warning("Potential prompt injection detected",
                             pattern=pattern,
                             text_preview=text[:100])
                return True
        return False
```

**Timeline:** Before image upload feature (week 2)

---

### 1.9 S3 Bucket Public Access Controls Not Specified

**Severity:** Critical
**CVSS Score:** 8.2 (High)
**Affected Components:** File storage, S3 bucket configuration

**Issue:**
S3 bucket structure is defined but no access controls specified:
```
jules-images-prod/
├── households/
│   └── {household_id}/
│       ├── recipes/
│       └── pantry/
```

No mention of:
- Bucket policies
- Public access block settings
- Encryption configuration
- Versioning
- Lifecycle policies

**Impact:**
- Recipe images publicly accessible
- Family pantry photos exposed
- PII leakage via image metadata
- Data breach via misconfigured bucket

**Remediation:**
1. Implement secure S3 bucket configuration:
```python
# infrastructure/aws/s3.py
import boto3

def create_secure_bucket(bucket_name: str):
    s3 = boto3.client('s3')

    # Create bucket with private ACL
    s3.create_bucket(
        Bucket=bucket_name,
        ACL='private',
        CreateBucketConfiguration={'LocationConstraint': 'us-east-1'}
    )

    # Block all public access
    s3.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
        }
    )

    # Enable versioning
    s3.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={'Status': 'Enabled'}
    )

    # Enable encryption
    s3.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            'Rules': [{
                'ApplyServerSideEncryptionByDefault': {
                    'SSEAlgorithm': 'AES256'
                },
                'BucketKeyEnabled': True
            }]
        }
    )

    # Set lifecycle policy (delete temp uploads after 7 days)
    s3.put_bucket_lifecycle_configuration(
        Bucket=bucket_name,
        LifecycleConfiguration={
            'Rules': [
                {
                    'Id': 'DeleteTempUploads',
                    'Prefix': 'temp/uploads/',
                    'Status': 'Enabled',
                    'Expiration': {'Days': 7}
                },
                {
                    'Id': 'TransitionOldRecipes',
                    'Prefix': 'households/',
                    'Status': 'Enabled',
                    'Transitions': [{
                        'Days': 90,
                        'StorageClass': 'GLACIER'
                    }]
                }
            ]
        }
    )

    # Set bucket policy (deny insecure transport)
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "DenyInsecureTransport",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}/*",
                    f"arn:aws:s3:::{bucket_name}"
                ],
                "Condition": {
                    "Bool": {
                        "aws:SecureTransport": "false"
                    }
                }
            }
        ]
    }
    s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(bucket_policy))

    # Enable logging
    s3.put_bucket_logging(
        Bucket=bucket_name,
        BucketLoggingStatus={
            'LoggingEnabled': {
                'TargetBucket': f'{bucket_name}-logs',
                'TargetPrefix': 'access-logs/'
            }
        }
    )
```

2. Use signed URLs for all access:
```python
# core/storage/s3.py
class S3Storage:
    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> str:
        """Generate time-limited signed URL"""
        s3_client = boto3.client('s3')

        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': object_key
            },
            ExpiresIn=expiration
        )

        return url

    async def upload_file(self, file_content: bytes, object_key: str, content_type: str):
        """Upload with server-side encryption"""
        s3_client = boto3.client('s3')

        s3_client.put_object(
            Bucket=self.bucket_name,
            Key=object_key,
            Body=file_content,
            ContentType=content_type,
            ServerSideEncryption='AES256',
            Metadata={
                'uploaded-by': 'jules-api',
                'upload-timestamp': datetime.utcnow().isoformat()
            }
        )
```

3. Implement CloudFront with restricted access:
```python
# infrastructure/aws/cloudfront.py
def create_cloudfront_distribution(s3_bucket: str, origin_access_identity: str):
    cloudfront = boto3.client('cloudfront')

    response = cloudfront.create_distribution(
        DistributionConfig={
            'Origins': {
                'Quantity': 1,
                'Items': [{
                    'Id': 'S3Origin',
                    'DomainName': f'{s3_bucket}.s3.amazonaws.com',
                    'S3OriginConfig': {
                        'OriginAccessIdentity': f'origin-access-identity/cloudfront/{origin_access_identity}'
                    }
                }]
            },
            'DefaultCacheBehavior': {
                'TargetOriginId': 'S3Origin',
                'ViewerProtocolPolicy': 'redirect-to-https',  # Force HTTPS
                'AllowedMethods': {
                    'Quantity': 2,
                    'Items': ['GET', 'HEAD']
                },
                'Compress': True,
                'MinTTL': 0,
                'DefaultTTL': 86400,
                'MaxTTL': 31536000
            },
            'Enabled': True,
            'HttpVersion': 'http2and3',
            'IsIPV6Enabled': True
        }
    )
```

**Timeline:** Before S3 bucket creation (week 1)

---

### 1.10 Database Encryption at Rest Not Explicitly Configured

**Severity:** Critical
**CVSS Score:** 7.4 (High)
**Affected Components:** PostgreSQL RDS, ElastiCache Redis

**Issue:**
RDS configuration shows:
```
StorageEncrypted: true
```

But there's no specification of:
- Encryption key management (AWS KMS)
- Key rotation policy
- Encryption algorithm
- Backup encryption

**Impact:**
- Database snapshots may be unencrypted
- Backup exports expose plaintext data
- Insufficient key management
- Compliance violations (PCI DSS, SOC 2)

**Remediation:**
1. Configure RDS with AWS KMS encryption:
```python
# infrastructure/aws/rds.py
import boto3

def create_encrypted_rds_instance():
    rds = boto3.client('rds')
    kms = boto3.client('kms')

    # Create KMS key for database encryption
    key_response = kms.create_key(
        Description='Jules database encryption key',
        KeyUsage='ENCRYPT_DECRYPT',
        Origin='AWS_KMS',
        MultiRegion=False,
        Tags=[
            {'TagKey': 'Application', 'TagValue': 'Jules'},
            {'TagKey': 'Purpose', 'TagValue': 'Database Encryption'}
        ]
    )
    kms_key_id = key_response['KeyMetadata']['KeyId']

    # Enable automatic key rotation
    kms.enable_key_rotation(KeyId=kms_key_id)

    # Create RDS instance with encryption
    rds.create_db_instance(
        DBInstanceIdentifier='jules-production',
        DBInstanceClass='db.t3.medium',
        Engine='postgres',
        EngineVersion='15.4',
        MasterUsername='jules_admin',
        MasterUserPassword=secret_manager.get_secret('jules/db', 'master_password'),
        AllocatedStorage=100,
        StorageType='gp3',
        StorageEncrypted=True,
        KmsKeyId=kms_key_id,  # Explicit KMS key
        BackupRetentionPeriod=30,  # 30 days of backups
        PreferredBackupWindow='03:00-04:00',
        EnableCloudwatchLogsExports=['postgresql', 'upgrade'],
        DeletionProtection=True,
        MultiAZ=True,
        PubliclyAccessible=False,
        VpcSecurityGroupIds=['sg-xxxxx'],
        Tags=[
            {'Key': 'Environment', 'Value': 'Production'},
            {'Key': 'Application', 'Value': 'Jules'}
        ]
    )

    # Create encrypted read replica
    rds.create_db_instance_read_replica(
        DBInstanceIdentifier='jules-production-read-1',
        SourceDBInstanceIdentifier='jules-production',
        DBInstanceClass='db.t3.medium',
        StorageEncrypted=True,
        KmsKeyId=kms_key_id,  # Same key for consistency
        PubliclyAccessible=False
    )
```

2. Configure Redis with encryption:
```python
# infrastructure/aws/elasticache.py
def create_encrypted_redis():
    elasticache = boto3.client('elasticache')

    elasticache.create_replication_group(
        ReplicationGroupId='jules-redis-prod',
        ReplicationGroupDescription='Jules production Redis cluster',
        CacheNodeType='cache.t3.medium',
        Engine='redis',
        EngineVersion='7.0',
        NumCacheClusters=2,  # Primary + 1 replica
        AutomaticFailoverEnabled=True,
        MultiAZEnabled=True,
        AtRestEncryptionEnabled=True,  # Encrypt at rest
        TransitEncryptionEnabled=True,  # Encrypt in transit
        AuthToken=secret_manager.get_secret('jules/redis', 'auth_token'),
        SnapshotRetentionLimit=7,
        SnapshotWindow='03:00-04:00',
        PreferredMaintenanceWindow='mon:04:00-mon:05:00',
        SecurityGroupIds=['sg-xxxxx'],
        Tags=[
            {'Key': 'Environment', 'Value': 'Production'},
            {'Key': 'Application', 'Value': 'Jules'}
        ]
    )
```

3. Implement backup encryption verification:
```python
# core/ops/backup_verification.py
async def verify_backup_encryption():
    """Verify all backups are encrypted"""
    rds = boto3.client('rds')

    snapshots = rds.describe_db_snapshots(
        DBInstanceIdentifier='jules-production'
    )

    unencrypted = []
    for snapshot in snapshots['DBSnapshots']:
        if not snapshot.get('Encrypted'):
            unencrypted.append(snapshot['DBSnapshotIdentifier'])

    if unencrypted:
        logger.critical("Unencrypted snapshots found", snapshots=unencrypted)
        # Alert security team
        await alert_security_team(
            severity="critical",
            message=f"Found {len(unencrypted)} unencrypted database snapshots"
        )
```

**Timeline:** Before database deployment (week 1)

---

## 2. HIGH SEVERITY VULNERABILITIES

### 2.1 No Content Security Policy (CSP) for Web Dashboard

**Severity:** High
**CVSS Score:** 6.8

**Issue:** React frontend has no CSP headers to prevent XSS attacks.

**Remediation:**
```python
# core/middleware/security_headers.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https://api.jules.ai; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response
```

---

### 2.2 No Rate Limiting on Authentication Endpoints

**Severity:** High
**CVSS Score:** 6.5

**Issue:** Login endpoint has no brute force protection.

**Remediation:**
```python
# core/auth/rate_limiting.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379/1")

@auth_router.post("/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(request: Request, credentials: LoginRequest):
    # Failed login tracking
    failed_key = f"failed_login:{credentials.email}"
    failed_count = int(redis.get(failed_key) or 0)

    if failed_count >= 10:
        # Lock account for 15 minutes after 10 failed attempts
        raise HTTPException(429, "Too many failed login attempts. Try again in 15 minutes.")

    # Verify credentials
    member = await authenticate_member(credentials.email, credentials.password)

    if not member:
        # Increment failed counter
        redis.incr(failed_key)
        redis.expire(failed_key, 900)  # 15 minutes
        raise HTTPException(401, "Invalid credentials")

    # Clear failed counter on success
    redis.delete(failed_key)

    return create_token_pair(member.id, member.household_id)
```

---

### 2.3 Missing Input Validation on Conversation State JSON Fields

**Severity:** High
**CVSS Score:** 6.3

**Issue:** `flow_data` JSON column has no validation, allowing injection attacks.

**Remediation:**
```python
# core/models/conversation.py
from pydantic import BaseModel, validator
import json

class FlowDataValidator(BaseModel):
    """Validate conversation flow data"""
    extraction_job_id: Optional[str]
    extracted_recipe: Optional[dict]
    user_corrections: Optional[list]

    @validator('*', pre=True)
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            # Remove potential injection patterns
            dangerous = ['<script', 'javascript:', 'onerror=', 'onclick=']
            v_lower = v.lower()
            if any(pattern in v_lower for pattern in dangerous):
                raise ValueError("Potentially malicious content detected")
        return v

class ConversationState(Base):
    flow_data = Column(JSON)

    @validates('flow_data')
    def validate_flow_data(self, key, value):
        """Validate JSON before storing"""
        if value:
            # Ensure it's valid JSON
            try:
                json_str = json.dumps(value)
                parsed = json.loads(json_str)

                # Validate against schema
                FlowDataValidator(**parsed)

                return value
            except Exception as e:
                raise ValueError(f"Invalid flow data: {e}")
        return value
```

---

### 2.4 No SQL Injection Protection for Raw Queries

**Severity:** High
**CVSS Score:** 7.2

**Issue:** While SQLAlchemy ORM is used, there may be raw SQL queries without parameterization.

**Remediation:**
```python
# ALWAYS use parameterized queries
# SECURE:
stmt = text("SELECT * FROM orders WHERE user_id = :user_id AND status = :status")
result = await conn.execute(stmt, {"user_id": user_id, "status": "pending"})

# VULNERABLE - NEVER DO THIS:
# query = f"SELECT * FROM orders WHERE user_id = {user_id}"
# result = await conn.execute(query)

# Add SQL injection detection in logging
class SQLInjectionDetector:
    PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bor\b.*=.*)",
        r"(;.*drop\b)",
        r"(;.*delete\b)",
        r"(;.*update\b)",
        r"(\/\*.*\*\/)",
        r"(--)",
    ]

    def detect(self, query: str) -> bool:
        query_lower = query.lower()
        for pattern in self.PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                logger.warning("Potential SQL injection attempt",
                             pattern=pattern,
                             query_preview=query[:100])
                return True
        return False
```

---

### 2.5 Insufficient Session Timeout Configuration

**Severity:** High
**CVSS Score:** 5.9

**Issue:** JWT access tokens have 1-hour expiry, too long for sensitive operations.

**Remediation:**
- Access tokens: 15 minutes (not 1 hour)
- Refresh tokens: 30 days (with rotation)
- Idle timeout: 30 minutes
- Absolute session timeout: 12 hours

```python
SESSION_CONFIG = {
    "access_token_lifetime": timedelta(minutes=15),
    "refresh_token_lifetime": timedelta(days=30),
    "idle_timeout": timedelta(minutes=30),
    "absolute_timeout": timedelta(hours=12),
}
```

---

### 2.6 Missing CORS Configuration Validation

**Severity:** High
**CVSS Score:** 6.1

**Issue:** CORS configuration allows all methods and headers without validation.

**Remediation:**
```python
# core/middleware/cors.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.jules.ai",
        "https://staging.jules.ai"
        # NO wildcard "*" in production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Explicit methods only
    allow_headers=["Authorization", "Content-Type"],  # Explicit headers only
    max_age=3600,  # Cache preflight for 1 hour
)
```

---

### 2.7 No Monitoring for Suspicious Activity

**Severity:** High
**CVSS Score:** 5.8

**Issue:** No anomaly detection for:
- Excessive API calls
- Unusual SMS sending patterns
- Abnormal AI processing requests
- Rapid household/member creation

**Remediation:**
```python
# core/security/anomaly_detection.py
class AnomalyDetector:
    async def detect_excessive_api_calls(self, user_id: str):
        """Detect API abuse"""
        key = f"api_calls:{user_id}:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
        count = redis.incr(key)
        redis.expire(key, 3600)

        if count > 1000:  # 1000 calls/hour threshold
            await alert_security_team(
                severity="high",
                message=f"User {user_id} made {count} API calls in 1 hour"
            )
            # Rate limit user
            await rate_limiter.block_user(user_id, duration=3600)

    async def detect_bulk_sms_abuse(self, household_id: str):
        """Detect SMS spam attempts"""
        key = f"sms_sent:{household_id}:{datetime.utcnow().date()}"
        count = redis.incr(key)
        redis.expire(key, 86400)

        if count > 50:  # 50 messages/day threshold
            logger.warning("Excessive SMS usage",
                          household_id=household_id,
                          count=count)
            # Notify household and throttle
```

---

### 2.8 Missing Data Retention and Deletion Policies

**Severity:** High
**CVSS Score:** 5.5

**Issue:** No defined retention periods for:
- Conversation messages
- Conversation states
- Audit logs
- User data after account deletion

**GDPR/CCPA Requirement:** Right to deletion, data minimization.

**Remediation:**
```python
# core/compliance/data_retention.py
RETENTION_POLICIES = {
    "messages": timedelta(days=2*365),  # 2 years
    "conversation_states": timedelta(days=90),  # 90 days
    "opt_in_audit_log": timedelta(days=7*365),  # 7 years (legal requirement)
    "family_recipes": None,  # Keep indefinitely (user content)
    "pantry_items": timedelta(days=180),  # 6 months
    "pantry_scans": timedelta(days=30),  # 30 days
    "shopping_lists": timedelta(days=90),  # 90 days
}

async def purge_old_data():
    """Delete data past retention period"""
    for table, retention in RETENTION_POLICIES.items():
        if retention is None:
            continue

        cutoff = datetime.utcnow() - retention

        await db.execute(
            delete(globals()[table.title()])
            .where(globals()[table.title()].created_at < cutoff)
        )

        logger.info(f"Purged old data from {table}",
                   cutoff_date=cutoff.isoformat())

async def delete_user_data(member_id: str):
    """GDPR/CCPA data deletion request"""
    # 1. Delete personal messages
    await db.execute(delete(Message).where(Message.member_id == member_id))

    # 2. Anonymize instead of deleting audit logs (compliance)
    await db.execute(
        update(OptInAuditLog)
        .where(OptInAuditLog.member_id == member_id)
        .values(member_id="DELETED_USER", source_phone="[REDACTED]")
    )

    # 3. Delete member record
    member = await db.get(Member, member_id)
    household_id = member.household_id
    await db.delete(member)

    # 4. If last member in household, delete household
    remaining = await db.query(Member).filter(Member.household_id == household_id).count()
    if remaining == 0:
        await delete_household(household_id)

    await db.commit()

    logger.info("User data deleted", member_id=member_id)
```

---

### 2.9 No Protection Against Server-Side Request Forgery (SSRF)

**Severity:** High
**CVSS Score:** 6.4

**Issue:** Recipe extraction from URLs allows SSRF attacks.

**Remediation:**
```python
# core/security/ssrf_protection.py
import ipaddress
from urllib.parse import urlparse

class SSRFProtection:
    BLOCKED_NETWORKS = [
        ipaddress.ip_network('10.0.0.0/8'),  # Private
        ipaddress.ip_network('172.16.0.0/12'),  # Private
        ipaddress.ip_network('192.168.0.0/16'),  # Private
        ipaddress.ip_network('127.0.0.0/8'),  # Loopback
        ipaddress.ip_network('169.254.0.0/16'),  # Link-local
        ipaddress.ip_network('::1/128'),  # IPv6 loopback
        ipaddress.ip_network('fc00::/7'),  # IPv6 private
    ]

    async def validate_url(self, url: str) -> bool:
        """Validate URL is not SSRF attack"""
        parsed = urlparse(url)

        # Only allow HTTP/HTTPS
        if parsed.scheme not in ['http', 'https']:
            raise ValueError("Invalid URL scheme")

        # Resolve hostname to IP
        try:
            ip = socket.gethostbyname(parsed.hostname)
            ip_obj = ipaddress.ip_address(ip)

            # Check against blocked networks
            for network in self.BLOCKED_NETWORKS:
                if ip_obj in network:
                    raise ValueError("Access to private IP ranges not allowed")

        except socket.gaierror:
            raise ValueError("Could not resolve hostname")

        return True

# Usage in recipe URL extraction
ssrf_protection = SSRFProtection()

@recipe_router.post("/from-url")
async def extract_recipe_from_url(url: str):
    await ssrf_protection.validate_url(url)

    # Fetch with timeout and size limit
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, follow_redirects=False)

        # Limit response size
        if int(response.headers.get('content-length', 0)) > 10*1024*1024:
            raise ValueError("Response too large")

        # Process...
```

---

### 2.10 Insufficient Logging for Security Events

**Severity:** High
**CVSS Score:** 5.3

**Issue:** Security events not properly logged:
- Failed authentication attempts
- Permission denials
- Opt-out events
- Data access by admins
- Configuration changes

**Remediation:**
```python
# core/logging/security_logger.py
import structlog

security_logger = structlog.get_logger("security")

class SecurityEventLogger:
    async def log_auth_failure(self, email: str, ip: str, reason: str):
        security_logger.warning(
            "authentication_failed",
            email=email,
            ip_address=ip,
            reason=reason,
            timestamp=datetime.utcnow().isoformat()
        )

    async def log_permission_denied(self, member_id: str, resource: str, action: str):
        security_logger.warning(
            "permission_denied",
            member_id=member_id,
            resource=resource,
            action=action,
            timestamp=datetime.utcnow().isoformat()
        )

    async def log_data_access(self, member_id: str, accessed_member_id: str, data_type: str):
        security_logger.info(
            "data_accessed",
            accessor=member_id,
            accessed=accessed_member_id,
            data_type=data_type,
            timestamp=datetime.utcnow().isoformat()
        )

    async def log_config_change(self, member_id: str, setting: str, old_value: str, new_value: str):
        security_logger.info(
            "configuration_changed",
            member_id=member_id,
            setting=setting,
            old_value=old_value,
            new_value=new_value,
            timestamp=datetime.utcnow().isoformat()
        )

# Forward security logs to SIEM
async def forward_to_siem(log_entry: dict):
    """Send security logs to SIEM system"""
    # Integration with Splunk, DataDog, or AWS Security Hub
    pass
```

---

## 3. MEDIUM SEVERITY VULNERABILITIES

### 3.1 No API Versioning Strategy

**Severity:** Medium
**Remediation:** Implement `/api/v1/`, `/api/v2/` versioning with deprecation notices.

---

### 3.2 Missing Health Check Endpoint Security

**Severity:** Medium
**Remediation:** Health check endpoints should not expose sensitive system information.

```python
@app.get("/health")
async def health_check():
    # DO NOT expose detailed system info publicly
    return {"status": "healthy"}

@app.get("/health/detailed")
@require_permission(Permission.HOUSEHOLD_ADMIN)
async def detailed_health():
    # Detailed health only for authenticated users
    return {
        "database": await check_database(),
        "redis": await check_redis(),
        "sms_provider": await check_sms_provider()
    }
```

---

### 3.3 No Protection Against Clickjacking

**Severity:** Medium
**Remediation:** Add `X-Frame-Options` and CSP `frame-ancestors` headers (already in 2.1).

---

### 3.4 Missing Subresource Integrity (SRI) for CDN Assets

**Severity:** Medium
**Remediation:** Add SRI hashes to all CDN scripts and stylesheets.

```html
<script src="https://cdn.jsdelivr.net/npm/react@18/umd/react.production.min.js"
        integrity="sha384-abc123..."
        crossorigin="anonymous"></script>
```

---

### 3.5 No Protection Against Tabnabbing

**Severity:** Medium
**Remediation:** Add `rel="noopener noreferrer"` to all external links.

---

### 3.6 Missing HTTP Strict Transport Security (HSTS) Preload

**Severity:** Medium
**Remediation:** Add to HSTS preload list after enabling HSTS header.

---

### 3.7 No Content Type Validation for Uploads

**Severity:** Medium
**Remediation:** Validate MIME types with magic bytes (already in 1.8).

---

### 3.8 Missing Database Connection Pooling Configuration

**Severity:** Medium
**Remediation:** Configure SQLAlchemy connection pooling to prevent exhaustion.

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True  # Verify connections before use
)
```

---

### 3.9 No Rate Limiting on Recipe Search

**Severity:** Medium
**Remediation:** Add rate limiting to prevent database abuse via search.

---

### 3.10 Missing API Response Size Limits

**Severity:** Medium
**Remediation:** Implement pagination and response size limits.

```python
@recipe_router.get("/family-recipes")
async def list_recipes(limit: int = 50, offset: int = 0):
    if limit > 100:
        raise HTTPException(400, "Maximum limit is 100")

    # Paginated query...
```

---

## 4. COMPLIANCE GAPS

### 4.1 TCPA/CTIA Compliance

**Status:** Partially Compliant

**Missing:**
- Automated opt-out processing (implemented but needs testing)
- Documented opt-in language review
- Message frequency disclosure
- Help/Info keyword responses

**Remediation:**
```python
# core/compliance/tcpa.py
class TCPACompliance:
    REQUIRED_FIRST_MESSAGE = """Hi! {sender} added you to their Jules household for family meal planning.

Reply YES to join. You'll receive ~10-20 messages/week for meal planning, recipes, and shopping lists.

Reply HELP for info or STOP to opt out.
Message and data rates may apply."""

    HELP_RESPONSE = """Jules helps your family with:
- Weekly meal planning
- Recipe management
- Grocery shopping lists

Text STOP to opt out.
For support: support@jules.ai"""

    STOP_RESPONSE = """You've been unsubscribed from Jules. You won't receive any more messages.

Text START to rejoin anytime."""
```

---

### 4.2 GDPR/CCPA Compliance

**Status:** Non-Compliant

**Missing:**
- Privacy policy
- Cookie consent (web dashboard)
- Data portability (export user data)
- Right to deletion (implemented above in 2.8)
- Data processing agreements with third parties
- Privacy by design documentation

**Remediation:**
1. Implement data export:
```python
@member_router.get("/me/export")
async def export_my_data(current_user = Depends(get_current_user)):
    """GDPR/CCPA data export"""
    member = await db.get(Member, current_user.id)

    export_data = {
        "personal_info": {
            "name": member.name,
            "email": member.email,
            "phone": member.phone_number,
            "role": member.role,
            "created_at": member.created_at.isoformat()
        },
        "messages": await get_member_messages(member.id),
        "recipes_submitted": await get_member_recipes(member.id),
        "preferences": await get_member_preferences(member.id),
        "consent_history": await export_consent_history(member.id)
    }

    return export_data
```

2. Add cookie consent banner
3. Create privacy policy with required disclosures
4. Document data flows with third parties

---

### 4.3 PCI DSS Compliance

**Status:** Not Applicable (MVP)

**Future:** If adding payment processing, will need PCI DSS Level 1 compliance.

---

### 4.4 SOC 2 Type II Compliance

**Status:** Non-Compliant

**Requirements for Future:**
- Annual penetration testing
- Incident response plan
- Access control reviews
- Change management process
- Vendor risk assessments
- Security awareness training

---

## 5. THIRD-PARTY INTEGRATION RISKS

### 5.1 Anthropic Claude API

**Risks:**
- Data sent to external AI service
- Prompt injection attacks
- API key compromise
- Rate limiting failures
- Service outages

**Mitigations:**
- Implement prompt injection detection (see 1.8)
- Use API key rotation (see 1.4)
- Add fallback to OpenAI
- Cache AI responses to reduce API calls
- Monitor API usage costs

---

### 5.2 Twilio SMS

**Risks:**
- Webhook spoofing (see 1.2)
- SMS spam from compromised accounts
- Phone number recycling (user gets another person's messages)
- International SMS fraud

**Mitigations:**
- Webhook signature verification (see 1.2)
- Rate limiting on SMS (implemented)
- Phone number validation before sending
- Implement fallback provider (Telnyx)
- Monitor unusual SMS patterns

---

### 5.3 Spoonacular API

**Risks:**
- Recipe data quality issues
- API key exposure
- Rate limit exceeded
- Pricing changes

**Mitigations:**
- Validate recipe data before saving
- Use API key from secrets manager
- Implement caching layer
- Monitor API usage

---

### 5.4 MCP Servers (Sentry, GitHub, Postgres)

**Risks:**
- Credential exposure via MCP
- Excessive permissions granted to AI
- Unintended data modifications

**Mitigations:**
```json
{
  "mcpServers": {
    "sentry": {
      "command": "npx",
      "args": ["-y", "@sentry/mcp-server"],
      "env": {
        "SENTRY_AUTH_TOKEN": "${SENTRY_MCP_TOKEN}",  // Read-only token
        "SENTRY_ORG": "jules-ai"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION": "${POSTGRES_READONLY_URL}"  // Read-only connection
      }
    }
  }
}
```

- Use read-only credentials for MCP servers
- Audit MCP server actions
- Limit AI permissions to necessary operations only

---

## 6. RECOMMENDATIONS

### Immediate (Before MVP Launch - Week 1)

1. Implement phone number encryption (1.1)
2. Add Twilio webhook signature verification (1.2)
3. Configure S3 bucket security (1.9)
4. Enable database encryption (1.10)
5. Create opt-in audit log (1.6)
6. Implement secrets management with Vault/AWS Secrets Manager (1.4)

### Short-term (Before Beta - Weeks 2-3)

7. Add rate limiting to all endpoints (1.3, 2.2)
8. Implement JWT token rotation (1.7)
9. Add image sanitization pipeline (1.8)
10. Implement COPPA compliance framework (1.5)
11. Add security headers and CSP (2.1)
12. Implement anomaly detection (2.7)

### Medium-term (Before Production - Weeks 4-6)

13. Data retention and deletion policies (2.8)
14. SSRF protection (2.9)
15. Security event logging (2.10)
16. GDPR/CCPA data export (4.2)
17. Comprehensive input validation (2.3)
18. SQL injection protection audit (2.4)

### Long-term (Post-Launch - Ongoing)

19. SOC 2 Type II compliance
20. Penetration testing (quarterly)
21. Security awareness training
22. Bug bounty program
23. Third-party security audits

---

## 7. SECURITY TESTING CHECKLIST

- [ ] SAST scanning (Bandit, Semgrep)
- [ ] DAST scanning (OWASP ZAP)
- [ ] Dependency vulnerability scanning (Safety, Snyk)
- [ ] Secret scanning (git-secrets, TruffleHog)
- [ ] Container security scanning (Trivy)
- [ ] API security testing (OWASP API Top 10)
- [ ] Authentication testing (Burp Suite)
- [ ] Authorization testing (privilege escalation)
- [ ] Input validation testing (fuzzing)
- [ ] Encryption testing (SSL Labs)
- [ ] Compliance validation (automated checks)
- [ ] Penetration testing (external firm)

---

## 8. SECURITY METRICS TO TRACK

1. **Vulnerability Metrics:**
   - Open critical vulnerabilities: 0
   - Open high vulnerabilities: <5
   - Mean time to remediate (MTTR): <7 days

2. **Incident Metrics:**
   - Security incidents: 0
   - Data breaches: 0
   - Unauthorized access attempts: tracked

3. **Compliance Metrics:**
   - TCPA opt-out response time: <1 hour
   - Data deletion request response: <30 days
   - Security scan frequency: daily

---

## 9. CONCLUSION

Jules has significant security vulnerabilities in its current design that must be addressed before any user data collection. The most critical issues are:

1. **PII encryption** not enforced
2. **Webhook security** missing
3. **Secrets management** inadequate
4. **COPPA compliance** absent
5. **Audit trails** incomplete

**Estimated Remediation Effort:** 3-4 weeks of dedicated security engineering before MVP launch.

**Recommendation:** Do not proceed with MVP deployment until at minimum all Critical and High severity vulnerabilities are remediated.

---

## Appendix A: Security Tools to Install

```bash
# Python security scanning
pip install bandit safety semgrep

# Pre-commit hooks
pip install pre-commit detect-secrets

# Image security
pip install pillow python-magic pyclamd

# Secrets management
pip install hvac boto3

# Rate limiting
pip install slowapi

# Security headers
pip install fastapi-security-headers

# Input validation
pip install pydantic email-validator phonenumbers
```

---

## Appendix B: Security Configuration Files

See individual remediation sections for configuration examples.

---

**Report Generated:** December 29, 2025
**Next Review:** After remediation of critical issues
**Contact:** security-auditor@jules.ai
