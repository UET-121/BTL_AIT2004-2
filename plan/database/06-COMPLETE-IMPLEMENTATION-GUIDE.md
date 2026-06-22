# PostgreSQL Complete Implementation Guide

**Version:** 1.0  
**Target:** Enterprise-grade database setup for license plate recognition  
**Timeline:** 4 weeks to full production readiness

---

## Overview

```
Week 1: Infrastructure & Setup
│
├─ PostgreSQL 16 Docker setup
├─ Network & security configuration  
├─ Environment variables setup
└─ Local development validation

        ↓

Week 2: Schema & Migrations
│
├─ Implement core schema
├─ Set up Alembic migrations
├─ Add indexes & constraints
├─ Write migration tests
└─ Performance baseline

        ↓

Week 3: Performance & Monitoring
│
├─ Configure connection pooling
├─ Set up Redis caching
├─ Enable slow query logging
├─ Create monitoring views
├─ Load testing (100+ concurrent)
└─ Optimization based on results

        ↓

Week 4: Security & Operations
│
├─ Implement audit logging
├─ Configure backups (full + WAL)
├─ Set up disaster recovery
├─ Security hardening
├─ Production checklist
└─ Staging deployment
```

---

## Week 1: Infrastructure & Setup

### Step 1.1: Docker Compose Configuration

Create production-ready `docker-compose.yml`:

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    container_name: plate_recognition_db
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-plate_recognition}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: >-
        -c max_connections=100
        -c shared_buffers=256MB
        -c effective_cache_size=1GB
        -c work_mem=26MB
        -c maintenance_work_mem=64MB
        -c checkpoint_completion_target=0.9
        -c wal_buffers=16MB
        -c log_min_duration_statement=1000
        -c log_statement=ddl
    
    ports:
      - "5432:5432"
    
    volumes:
      - db_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
      - ./postgresql.conf:/etc/postgresql/postgresql.conf
    
    networks:
      - backend
    
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    
    restart: unless-stopped
    
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"

  redis:
    image: redis:7-alpine
    container_name: plate_recognition_redis
    ports:
      - "6379:6379"
    
    volumes:
      - redis_data:/data
    
    networks:
      - backend
    
    command: redis-server --appendonly yes --maxmemory 512mb
    
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    
    restart: unless-stopped

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    container_name: plate_recognition_api
    environment:
      DATABASE_URL: postgresql+asyncpg://app_user:${APP_PASSWORD}@db:5432/plate_recognition
      REDIS_URL: redis://redis:6379/0
      PYTHONUNBUFFERED: 1
      LOG_LEVEL: ${LOG_LEVEL:-info}
    
    ports:
      - "8000:8000"
    
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    
    networks:
      - backend
    
    restart: unless-stopped
    
    volumes:
      - ./apps/api/uploads:/app/uploads

volumes:
  db_data:
  redis_data:

networks:
  backend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Step 1.2: Environment Configuration

Create `.env.example`:

```bash
# Database
POSTGRES_DB=plate_recognition
POSTGRES_USER=postgres
POSTGRES_PASSWORD=ChangeMe123!@#

# Application
DATABASE_URL=postgresql+asyncpg://app_user:ChangeMe123!@#@localhost:5432/plate_recognition
REDIS_URL=redis://localhost:6379/0

# Application Settings
LOG_LEVEL=info
DEBUG=false
CORS_ORIGINS=http://localhost:3000,http://localhost

# Storage
STORAGE_TYPE=local
UPLOAD_DIR=/app/uploads
```

Copy to `.env`:
```bash
cp .env.example .env
# Edit .env with actual values
```

### Step 1.3: PostgreSQL Initialization Script

Create `scripts/init-db.sql`:

```sql
-- Initialize PostgreSQL with users and roles

-- Create replication user (for backups)
CREATE ROLE backup_user WITH LOGIN PASSWORD 'STRONG_BACKUP_PASSWORD';
ALTER ROLE backup_user REPLICATION;

-- Create application user (limited permissions)
CREATE ROLE app_user WITH LOGIN PASSWORD 'APP_PASSWORD_HERE';

-- Grant permissions to app_user
GRANT CONNECT ON DATABASE plate_recognition TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Create extensions
\c plate_recognition
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO app_user;

-- Enable logging
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();

-- Verify
\du
```

### Step 1.4: Verify Local Setup

```bash
# Start services
docker-compose up -d

# Wait for health checks
sleep 10

# Verify database is running
docker-compose exec db psql -U postgres -c "SELECT version();"

# Check connection
docker-compose exec api python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine('postgresql+asyncpg://app_user:app_pass@db:5432/plate_recognition')
async def test():
    async with engine.connect() as conn:
        result = await conn.execute('SELECT 1')
        print('✅ Connection successful:', result.fetchone())

asyncio.run(test())
"
```

---

## Week 2: Schema & Migrations

### Step 2.1: Create Database Models

```python
# apps/api/app/models/recognition.py

from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from app.shared.database import Base

class RecognitionRequest(Base):
    __tablename__ = "recognition_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    image_url = Column(String(2048), nullable=False, unique=True, index=True)
    plate_number = Column(String(20))
    status = Column(ENUM('NOT_STARTED', 'PENDING', 'COMPLETED', 'NEEDS_REVIEW', 'FAILED',
                         name='recognition_status'), 
                    nullable=False, default='NOT_STARTED', index=True)
    error_message = Column(String)
    
    # Confidence scores
    detection_confidence = Column(Numeric(5, 4))
    ocr_confidence = Column(Numeric(5, 4))
    confidence_score = Column(Numeric(5, 4))
    
    # Bounding box and region
    bounding_box = Column(JSONB)
    plate_region = Column(String(50))
    
    # Processing metadata
    needs_review = Column(Boolean, default=False, index=True)
    review_notes = Column(String)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    reviewed_at = Column(DateTime(timezone=True))
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    deleted_at = Column(DateTime(timezone=True))
    
    # Retry management
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_retry_at = Column(DateTime(timezone=True))
    
    # Performance
    processing_duration_ms = Column(Integer)
    priority = Column(Integer, default=5)
```

### Step 2.2: Create Alembic Migrations

```bash
# Initialize Alembic (if not already done)
cd apps/api
alembic revision --autogenerate -m "Initial schema: recognition_requests, users, audit_logs"
```

Review generated migration:

```python
# apps/api/migrations/versions/001_initial_schema.py

def upgrade() -> None:
    op.create_table(
        'recognition_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('image_url', sa.VARCHAR(2048), nullable=False),
        sa.Column('plate_number', sa.VARCHAR(20)),
        sa.Column('status', sa.ENUM('NOT_STARTED', 'PENDING', 'COMPLETED', 'NEEDS_REVIEW', 'FAILED'),
                  nullable=False),
        # ... all other columns
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('image_url')
    )
    op.create_index('idx_recognition_status', 'recognition_requests', ['status'])
    op.create_index('idx_recognition_created_at', 'recognition_requests', ['created_at'])
    # ... more indexes

def downgrade() -> None:
    op.drop_index('idx_recognition_created_at', table_name='recognition_requests')
    op.drop_table('recognition_requests')
```

### Step 2.3: Apply Migrations

```bash
# Test migration
cd apps/api
alembic upgrade head

# Verify schema
docker-compose exec db psql -U postgres -d plate_recognition -c "\d recognition_requests"

# Check migration history
alembic history --verbose
```

### Step 2.4: Add Seed Data (Optional)

```python
# apps/api/scripts/seed_db.py

import asyncio
from sqlalchemy import insert
from app.shared.database import async_session_factory
from app.models.recognition import RecognitionRequest
from uuid import uuid4
from datetime import datetime

async def seed_test_data():
    async with async_session_factory() as session:
        # Insert test data
        stmt = insert(RecognitionRequest).values([
            {
                'id': uuid4(),
                'image_url': f'/uploads/test_{i}.jpg',
                'plate_number': f'ABC{i}D23',
                'status': 'COMPLETED',
                'confidence_score': 0.95,
                'created_at': datetime.utcnow(),
            }
            for i in range(100)
        ])
        await session.execute(stmt)
        await session.commit()
        print("✅ Seed data inserted")

# Run: python scripts/seed_db.py
asyncio.run(seed_test_data())
```

---

## Week 3: Performance & Monitoring

### Step 3.1: Configure Connection Pooling

```python
# apps/api/app/shared/database.py

from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=settings.debug,
    connect_args={
        "timeout": 10,
        "command_timeout": 10,
    }
)
```

### Step 3.2: Set Up Redis Caching

```python
# apps/api/app/shared/cache.py

import redis.asyncio as redis
from contextlib import asynccontextmanager

class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    async def get(self, key: str):
        return await self.redis.get(key)
    
    async def set(self, key: str, value: str, ttl: int = 3600):
        await self.redis.setex(key, ttl, value)
    
    async def invalidate_pattern(self, pattern: str):
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

cache = CacheManager(settings.redis_url)
```

### Step 3.3: Enable Monitoring

```sql
-- Create monitoring views
CREATE VIEW connection_stats AS
SELECT 
    datname,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE state = 'active') as active,
    COUNT(*) FILTER (WHERE state = 'idle') as idle
FROM pg_stat_activity
WHERE datname = 'plate_recognition'
GROUP BY datname;

CREATE VIEW query_performance AS
SELECT
    query,
    calls,
    mean_time,
    max_time,
    rows
FROM pg_stat_statements
WHERE query LIKE '%recognition_requests%'
ORDER BY mean_time DESC
LIMIT 20;
```

### Step 3.4: Load Testing

```bash
# Install locust
pip install locust

# Create load test script (see 03-PERFORMANCE-OPTIMIZATION.md)
# Run load test
locust -f tests/load_test.py --host http://localhost:8000 --users 100 --spawn-rate 10 -t 5m
```

---

## Week 4: Security & Operations

### Step 4.1: Enable Audit Logging

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    entity_type VARCHAR(100),
    entity_id UUID,
    operation VARCHAR(50),
    old_values JSONB,
    new_values JSONB,
    user_id UUID,
    operation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
```

### Step 4.2: Configure Backups

```bash
# Create backup directory
mkdir -p /mnt/backups

# Schedule backup cron job
0 2 * * * /opt/scripts/backup-full-logical.sh >> /var/log/backups.log 2>&1
```

### Step 4.3: Production Checklist

```bash
#!/bin/bash
# scripts/production-readiness-check.sh

echo "=== Production Readiness Checklist ==="

checks=(
    "✅ PostgreSQL version 16 or higher"
    "✅ Connection pool configured (size: 20, overflow: 10)"
    "✅ SSL/TLS enabled for connections"
    "✅ Database users created with strong passwords"
    "✅ All migrations applied (alembic upgrade head)"
    "✅ Indexes created for all search columns"
    "✅ Audit logging enabled"
    "✅ Backup schedule configured"
    "✅ Recovery tested (DR drill completed)"
    "✅ Performance baseline established (p95 < 100ms)"
    "✅ Monitoring dashboards deployed"
    "✅ Alerting rules configured"
    "✅ Security scan completed (SQL injection, etc.)"
    "✅ Documentation updated"
    "✅ Team training completed"
)

for check in "${checks[@]}"; do
    echo "$check"
done

echo ""
echo "All checks passed! Ready for production deployment."
```

### Step 4.4: Staging Deployment

```bash
# Deploy to staging environment
docker-compose -f docker-compose.staging.yml up -d

# Run smoke tests
pytest tests/smoke/

# Run integration tests
pytest tests/integration/

# Monitor for 24 hours
watch -n 5 'docker-compose logs api | tail -20'
```

---

## Operational Procedures

### Daily Operations

```bash
# Morning check
docker-compose exec db psql -U postgres -d plate_recognition << EOF
SELECT COUNT(*) as daily_requests FROM recognition_requests WHERE DATE(created_at) = TODAY();
EOF

# Check backup status
aws s3 ls s3://plate-recognition-backups/full/ --human-readable | tail -5
```

### Weekly Tasks

- [ ] Review slow query log
- [ ] Analyze index usage
- [ ] Check connection pool saturation
- [ ] Verify backup integrity
- [ ] Review audit logs for anomalies

### Monthly Tasks

- [ ] Perform disaster recovery drill
- [ ] Analyze database growth rate
- [ ] Update statistics (ANALYZE)
- [ ] Review and optimize queries
- [ ] Security audit

---

## Rollback Procedure

If critical issues occur:

```bash
# Step 1: Immediate rollback
docker-compose down
docker volume rm plate_recognition_db_data  # WARNING: Data loss!

# Step 2: Restore from backup
docker-compose up -d db
./scripts/restore-full.sh /mnt/backups/latest_backup.sql.gz

# Step 3: Verify
docker-compose exec api pytest tests/smoke/

# Step 4: Restart application
docker-compose up -d api
```

---

## Next Steps

1. ✅ Implement Week 1 infrastructure
2. ✅ Run Week 2 schema setup
3. ✅ Complete Week 3 performance optimization
4. ✅ Execute Week 4 production hardening
5. ✅ Deploy to staging
6. ✅ 24-hour staging validation
7. ✅ Production deployment
8. ✅ Ongoing monitoring & maintenance

---

## Support & Resources

- PostgreSQL Documentation: https://www.postgresql.org/docs/16/
- SQLAlchemy Async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Alembic Migration Tool: https://alembic.sqlalchemy.org/
- Performance Tuning: https://wiki.postgresql.org/wiki/Performance_Optimization

For questions or issues, refer to the corresponding detailed guides in the `plan/database/` directory.
