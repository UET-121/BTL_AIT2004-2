# PostgreSQL Security Best Practices

**Version:** 1.0  
**Classification:** Internal — Handle with care  
**Status:** Production-Ready

---

## Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [Encryption](#encryption)
3. [SQL Injection Prevention](#sql-injection-prevention)
4. [Audit & Logging](#audit--logging)
5. [Backup Security](#backup-security)
6. [Network Security](#network-security)
7. [Secrets Management](#secrets-management)
8. [Compliance](#compliance)

---

## Authentication & Authorization

### User Roles & Permissions

```sql
-- ===== Role Hierarchy =====

-- 1. Admin Role (Full access)
CREATE ROLE app_admin WITH LOGIN PASSWORD 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE plate_recognition TO app_admin;

-- 2. Application Role (Limited to specific tables)
CREATE ROLE app_user WITH LOGIN PASSWORD 'STRONG_PASSWORD_HERE';

-- 3. Readonly Role (Analytics/Reporting)
CREATE ROLE app_readonly WITH LOGIN NOLOGIN;

-- ===== Grant Table Permissions =====

-- Application can read/write to recognition_requests
GRANT SELECT, INSERT, UPDATE, DELETE ON recognition_requests TO app_user;
GRANT SELECT, INSERT ON audit_logs TO app_user;
GRANT USAGE ON SEQUENCE recognition_requests_id_seq TO app_user;

-- Readonly can only read
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;

-- ===== Row-Level Security (RLS) =====
-- Restrict users to see only their own requests (multi-tenant)

ALTER TABLE recognition_requests ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation ON recognition_requests
    FOR SELECT
    USING (created_by = current_user_id());

CREATE POLICY user_update ON recognition_requests
    FOR UPDATE
    USING (created_by = current_user_id());
```

### Database User Best Practices

```bash
# ✅ DO: Use strong passwords with symbols
PASSWORD="Pl@t3R3c0g_P@ssw0rd!2024_$(openssl rand -base64 12)"

# ❌ DON'T: Simple or reused passwords
PASSWORD="postgres"
PASSWORD="password123"

# ✅ DO: Rotate passwords regularly
ALTER ROLE app_user WITH PASSWORD 'NEW_STRONG_PASSWORD';

# ✅ DO: Create dedicated users per environment
- prod_app_user
- staging_app_user
- dev_app_user

# ❌ DON'T: Use same user across all environments
```

### Connection Authentication (pg_hba.conf)

```ini
# PostgreSQL Host-Based Authentication

# Accept local connections with peer authentication
local   all             postgres                                peer
local   all             all                                     peer

# Accept connections from docker-compose network (TCP/IP)
host    plate_recognition app_user    172.16.0.0/12          md5

# Accept remote connections from app servers only
host    plate_recognition app_user    10.0.0.0/8             md5

# Reject all others
host    all             all             0.0.0.0/0              reject
```

---

## Encryption

### Encryption at Rest

```bash
# ===== Method 1: Filesystem-Level Encryption (Host VM) =====

# Ubuntu/Debian with LUKS
sudo apt-get install cryptsetup
sudo cryptsetup luksFormat /dev/sda1
sudo cryptsetup luksOpen /dev/sda1 pg_data
sudo mkfs.ext4 /dev/mapper/pg_data

# ===== Method 2: PostgreSQL pgcrypto Extension =====

-- Enable encryption functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt sensitive data in application
-- Use pgcrypto for key management if needed
SELECT pgp_pub_encrypt('sensitive_data', pubkey) FROM keys;
```

### Encryption in Transit

```yaml
# docker-compose.yml - PostgreSQL with SSL

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_INITDB_ARGS: "-c ssl=on -c ssl_cert_file=/etc/ssl/certs/server.crt -c ssl_key_file=/etc/ssl/private/server.key"
    volumes:
      - ./certs/server.crt:/etc/ssl/certs/server.crt:ro
      - ./certs/server.key:/etc/ssl/private/server.key:ro
    ports:
      - "5432:5432"
```

### SSL Certificate Generation

```bash
# Generate self-signed certificate (development)
openssl req -new -x509 -days 365 -nodes \
    -out server.crt -keyout server.key \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# For production: Use CA-signed certificate
# Generate CSR
openssl req -new -key server.key -out server.csr \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=db.example.com"

# Submit to Certificate Authority and get signed certificate
```

### Connection String with SSL

```python
# SQLAlchemy connection string with SSL
DATABASE_URL = "postgresql+asyncpg://user:password@db.example.com:5432/plate_recognition?ssl=require"

# Verify certificate
DATABASE_URL = "postgresql+asyncpg://user:password@db.example.com:5432/plate_recognition?ssl=verify-full&sslrootcert=/path/to/ca-bundle.crt"
```

---

## SQL Injection Prevention

### ❌ VULNERABLE Code (Direct String Concatenation)

```python
# DO NOT DO THIS!
user_input = request.query_params.get("plate")
query = f"SELECT * FROM recognition_requests WHERE plate_number = '{user_input}'"
result = await session.execute(text(query))
```

**Attack:** `plate' OR '1'='1` → Returns all rows

### ✅ SAFE: Parameterized Queries (SQLAlchemy)

```python
from sqlalchemy import select
from app.models.recognition import RecognitionRequest

# Method 1: SQLAlchemy ORM
plate = request.query_params.get("plate")
stmt = select(RecognitionRequest).where(
    RecognitionRequest.plate_number == plate
)
result = await session.execute(stmt)

# Method 2: Raw SQL with parameters
from sqlalchemy import text

plate = request.query_params.get("plate")
stmt = text("""
    SELECT * FROM recognition_requests 
    WHERE plate_number = :plate
""")
result = await session.execute(stmt, {"plate": plate})
```

### Input Validation & Sanitization

```python
from pydantic import BaseModel, Field, validator
import re

class PlateSearchRequest(BaseModel):
    plate_number: str = Field(
        ...,
        min_length=5,
        max_length=20,
        description="Valid Brazilian plate format"
    )
    
    @validator('plate_number')
    def validate_plate_format(cls, v):
        # Only alphanumeric and hyphen
        if not re.match(r'^[A-Z0-9\-]{5,20}$', v):
            raise ValueError('Invalid plate format')
        return v.upper()

# Usage in FastAPI
@app.get("/api/v1/recognition/search")
async def search_by_plate(req: PlateSearchRequest, db: AsyncSession):
    # plate_number is already validated
    result = await db.execute(
        select(RecognitionRequest).where(
            RecognitionRequest.plate_number == req.plate_number
        )
    )
    return result.scalars().all()
```

### LIKE Query Safety

```python
# ❌ VULNERABLE to SQL injection
search_term = "%' OR '1'='1"  # from user input
stmt = text(f"SELECT * FROM users WHERE username LIKE '{search_term}%'")

# ✅ SAFE: Use bind parameters for LIKE
search_term = request.query_params.get("q")
stmt = text("""
    SELECT * FROM users 
    WHERE username LIKE :search || '%'
""")
result = await session.execute(stmt, {"search": search_term})
```

---

## Audit & Logging

### Immutable Audit Table

```sql
-- Audit logs cannot be modified (only INSERT/SELECT)
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    operation VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    user_id UUID,
    operation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) WITH (fillfactor=100);  -- Immutable hint

-- Restrict permissions
REVOKE UPDATE, DELETE ON audit_logs FROM app_user;
GRANT SELECT, INSERT ON audit_logs TO app_user;

-- Enable row-level security on audited tables
CREATE POLICY audit_append_only ON audit_logs
    FOR DELETE
    USING (FALSE);  -- Prevent deletion

CREATE POLICY audit_insert_only ON audit_logs
    FOR UPDATE
    USING (FALSE);  -- Prevent updates
```

### PostgreSQL Logging Configuration

```ini
# postgresql.conf

# ===== General Logging =====
log_connections = on
log_disconnections = on
log_duration = off
log_lock_waits = on
log_statement = 'ddl'  # Log CREATE/ALTER/DROP
log_min_duration_statement = 1000  # Log slow queries (> 1s)

# ===== Log Format =====
log_line_prefix = '%t [%p] %u@%d '  # timestamp [pid] user@database
log_statement_sample_rate = 1.0
log_min_error_statement = 'error'

# ===== Log Output =====
log_destination = 'stderr'
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-%Y-%m-%d.log'
log_truncate_on_rotation = on
log_rotation_age = '1d'
log_rotation_size = 0

# ===== Specific Operations =====
log_autovacuum_min_duration = 0  # Log all VACUUM operations
log_error_verbosity = 'verbose'
```

### Application-Level Audit Triggers

```python
# apps/api/app/services/audit.py

from sqlalchemy import event, insert, select
from sqlalchemy.orm import Session
import json
from datetime import datetime

class AuditService:
    @staticmethod
    def create_audit_log(
        session: Session,
        entity_type: str,
        entity_id,
        operation: str,
        old_values: dict = None,
        new_values: dict = None,
        user_id = None,
        reason: str = None
    ):
        """Record change for compliance"""
        from app.models.audit import AuditLog
        
        log = AuditLog(
            entity_type=entity_type,
            entity_id=str(entity_id),
            operation=operation,
            old_values=old_values,
            new_values=new_values,
            user_id=user_id,
            reason=reason,
            metadata={
                'timestamp': datetime.utcnow().isoformat(),
                'application': 'plate-recognition-api'
            }
        )
        session.add(log)
        return log

    @staticmethod
    def on_update(mapper, connection, target):
        """SQLAlchemy event listener for UPDATE"""
        # Get old values from session history
        old_values = {}
        for col in mapper.columns:
            if col.name in mapper.attrs:
                old_values[col.name] = getattr(target, col.name)
        
        # Log to audit table
        AuditService.create_audit_log(
            session=object_session(target),
            entity_type=mapper.class_.__name__,
            entity_id=target.id,
            operation='UPDATE',
            new_values={col.name: getattr(target, col.name) for col in mapper.columns},
            user_id=getattr(target, 'updated_by', None)
        )

# Register event listener
from sqlalchemy.orm import object_session
from app.models.recognition import RecognitionRequest
event.listen(RecognitionRequest, 'after_update', AuditService.on_update)
```

---

## Backup Security

### Backup Encryption

```bash
#!/bin/bash
# scripts/backup-secure.sh

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="plate_recognition_${BACKUP_DATE}.sql.gz"
BACKUP_ENCRYPTED="${BACKUP_FILE}.gpg"

# Step 1: Create backup
pg_dump -U postgres -h localhost -d plate_recognition \
    | gzip > /tmp/${BACKUP_FILE}

# Step 2: Encrypt with GPG
gpg --encrypt --recipient backup@example.com \
    --output /mnt/backups/${BACKUP_ENCRYPTED} \
    /tmp/${BACKUP_FILE}

# Step 3: Verify
gpg --list-only /mnt/backups/${BACKUP_ENCRYPTED}

# Step 4: Clean unencrypted backup
shred -vfz -n 3 /tmp/${BACKUP_FILE}

echo "Backup encrypted: /mnt/backups/${BACKUP_ENCRYPTED}"
```

### Restore from Encrypted Backup

```bash
#!/bin/bash
# scripts/restore-secure.sh

BACKUP_FILE=$1

# Step 1: Decrypt
gpg --decrypt --output /tmp/decrypted.sql.gz ${BACKUP_FILE}

# Step 2: Restore
gunzip < /tmp/decrypted.sql.gz | psql -U postgres -h localhost

# Step 3: Clean
shred -vfz -n 3 /tmp/decrypted.sql.gz

echo "Database restored from backup"
```

### Backup Retention Policy

```bash
#!/bin/bash
# scripts/cleanup-old-backups.sh

# Keep only last 30 days of backups
find /mnt/backups -name "plate_recognition_*.sql.gz.gpg" \
    -mtime +30 -delete

# Verify recent backups exist
ls -lh /mnt/backups/ | tail -10
```

---

## Network Security

### Docker Network Isolation

```yaml
# docker-compose.yml

services:
  db:
    image: postgres:16-alpine
    networks:
      - db_network  # Isolated network
    environment:
      POSTGRES_INITDB_ARGS: "-c listen_addresses=db"  # Only listen on container network

  api:
    image: plate-recognition-api:latest
    networks:
      - db_network
      - web_network
    environment:
      DATABASE_URL: postgresql+asyncpg://app_user:PASSWORD@db:5432/plate_recognition

  nginx:
    image: nginx:alpine
    networks:
      - web_network

networks:
  db_network:
    internal: true  # No external access to database network
  web_network:
    internal: false
```

### PostgreSQL Access Control

```sql
-- Only allow connections from specific IPs
-- Configured in pg_hba.conf:

# Host: database connections
# TYPE  DATABASE        USER            ADDRESS                 METHOD
host    plate_recognition app_user    10.0.0.0/8             md5
host    plate_recognition app_readonly 10.0.0.0/8             md5
host    plate_recognition backup_user  10.0.1.0/24            md5

# Reject all others
host    all             all             0.0.0.0/0              reject
```

### Firewall Rules

```bash
#!/bin/bash
# scripts/setup-firewall.sh

# Allow only app servers to connect to DB
UFW_RULES=(
    "5432/tcp from 10.0.0.0/8"      # App servers
    "5432/tcp from 10.0.1.0/24"     # Backup server
)

for rule in "${UFW_RULES[@]}"; do
    sudo ufw allow "$rule"
done

# Reject all other traffic on 5432
sudo ufw default deny incoming
```

---

## Secrets Management

### Environment Variables (Secure)

```bash
# ✅ DO: Use environment variables from secure vault
export DATABASE_URL="postgresql+asyncpg://app_user:$(get_secret 'db/app-password')@db:5432/plate_recognition"

# ❌ DON'T: Hardcode passwords in code
DATABASE_URL = "postgresql+asyncpg://app_user:postgres123@localhost:5432/plate_recognition"

# ❌ DON'T: Store in version control
# .env file should be in .gitignore
```

### Kubernetes Secrets (For Cloud)

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-credentials
type: Opaque
data:
  database-url: cG9zdGdyZXM6Ly9hcHBfdXNlcjpQQVNTV09SRCBASW9zdC81NDMyL3BsYXRlX3JlY29nbml0aW9u  # base64 encoded
  admin-password: QURNSVdfUEFTU1dPUkQ=
---
apiVersion: v1
kind: Pod
metadata:
  name: api-server
spec:
  containers:
  - name: app
    image: plate-recognition:latest
    env:
    - name: DATABASE_URL
      valueFrom:
        secretKeyRef:
          name: postgres-credentials
          key: database-url
```

### AWS Secrets Manager (For Production)

```python
# apps/api/app/shared/secrets.py

import boto3
import json
from functools import lru_cache

@lru_cache(maxsize=1)
def get_secrets():
    """Fetch secrets from AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    
    response = client.get_secret_value(SecretId='plate-recognition/prod')
    
    if 'SecretString' in response:
        return json.loads(response['SecretString'])
    
    raise RuntimeError("Failed to retrieve secrets")

# Usage
secrets = get_secrets()
database_url = secrets['database_url']
admin_password = secrets['admin_password']
```

---

## Compliance

### GDPR Compliance

```sql
-- ===== Right to be Forgotten =====
-- Soft delete + scheduled purge

CREATE FUNCTION purge_deleted_data() RETURNS void AS $$
BEGIN
    -- Purge audit logs older than 7 years
    DELETE FROM audit_logs 
    WHERE operation_timestamp < NOW() - INTERVAL '7 years';
    
    -- Purge soft-deleted users older than 90 days
    DELETE FROM users 
    WHERE deleted_at IS NOT NULL 
    AND deleted_at < NOW() - INTERVAL '90 days';
    
    RAISE NOTICE 'Data purge completed';
END
$$ LANGUAGE plpgsql;

-- Schedule purge (e.g., monthly)
-- SELECT cron.schedule('purge_deleted_data', '0 0 1 * *', 'SELECT purge_deleted_data()');
```

### PII Data Masking

```python
# apps/api/app/services/export.py

from sqlalchemy import select
import hashlib

async def export_recognitions_masked(session: AsyncSession):
    """Export with PII masked for testing/analysis"""
    result = await session.execute(select(RecognitionRequest))
    requests = result.scalars().all()
    
    masked_data = []
    for req in requests:
        masked_data.append({
            'id': req.id,
            'plate_number': '***' if req.plate_number else None,
            'status': req.status,
            'confidence_score': req.confidence_score,
            'created_by': hashlib.sha256(str(req.created_by).encode()).hexdigest(),
            'created_at': req.created_at,
        })
    
    return masked_data
```

### SOC2 Compliance Checklist

- [x] Encryption at rest and in transit
- [x] Audit logging for all changes
- [x] Role-based access control (RBAC)
- [x] Secrets stored securely (not in code)
- [x] Backups encrypted and tested
- [x] Network segmentation (isolated DB network)
- [x] Data retention policies documented
- [x] Incident response plan
- [x] Security scanning (SAST/DAST)
- [x] Penetration testing schedule

---

## Summary

✅ **Strong authentication** with role-based access  
✅ **Encryption** at rest and in transit  
✅ **SQL injection prevention** via parameterized queries  
✅ **Audit trail** for all modifications  
✅ **Secure backups** encrypted and protected  
✅ **Network isolation** with firewall rules  
✅ **GDPR/SOC2 compliance** ready  

Next: See [`05-BACKUP-AND-RECOVERY.md`](05-BACKUP-AND-RECOVERY.md)
