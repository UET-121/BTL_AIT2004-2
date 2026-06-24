# PostgreSQL Performance Optimization — Tuning & Monitoring

**Version:** 1.0  
**Target:** Enterprise-grade performance for millions of recognition requests

---

## Table of Contents

1. [Query Optimization](#query-optimization)
2. [Index Tuning](#index-tuning)
3. [Connection Pooling](#connection-pooling)
4. [Caching Strategy](#caching-strategy)
5. [PostgreSQL Configuration](#postgresql-configuration)
6. [Monitoring & Alerting](#monitoring--alerting)
7. [Load Testing](#load-testing)

---

## Query Optimization

### Common Patterns

#### Pattern 1: List Recognition Requests with Pagination

❌ **INEFFICIENT** (N+1 problem)
```python
requests = session.query(RecognitionRequest).all()
for req in requests:
    user = session.query(User).filter(User.id == req.created_by).first()
    # Database: 1 query + N queries for each user
```

✅ **OPTIMIZED** (Join + Eager Load)
```python
from sqlalchemy import joinedload

requests = session.query(RecognitionRequest) \
    .options(joinedload(RecognitionRequest.created_user)) \
    .filter(RecognitionRequest.deleted_at.is_(None)) \
    .order_by(RecognitionRequest.created_at.desc()) \
    .limit(50) \
    .all()
# Database: 1 query with JOIN
```

#### Pattern 2: Time-Range Queries (Last 30 Days)

❌ **INEFFICIENT** (Full table scan)
```sql
SELECT * FROM recognition_requests 
WHERE EXTRACT(DAYS FROM (NOW() - created_at)) <= 30;
```

✅ **OPTIMIZED** (Index-aware filter)
```sql
SELECT * FROM recognition_requests 
WHERE created_at >= NOW() - INTERVAL '30 days' 
AND deleted_at IS NULL
ORDER BY created_at DESC;
```

Using index: `idx_recognition_created_at`

#### Pattern 3: Aggregation Queries (Dashboard)

❌ **INEFFICIENT** (Multiple scans)
```python
total = session.query(func.count(RecognitionRequest.id)).scalar()
completed = session.query(func.count(RecognitionRequest.id)) \
    .filter(RecognitionRequest.status == 'COMPLETED').scalar()
needs_review = session.query(func.count(RecognitionRequest.id)) \
    .filter(RecognitionRequest.needs_review == True).scalar()
# Database: 3 separate aggregation queries
```

✅ **OPTIMIZED** (Single query with CASE)
```python
from sqlalchemy import func, case

result = session.query(
    func.count(RecognitionRequest.id).label('total'),
    func.sum(case(
        (RecognitionRequest.status == 'COMPLETED', 1),
        else_=0
    )).label('completed'),
    func.sum(case(
        (RecognitionRequest.needs_review == True, 1),
        else_=0
    )).label('needs_review'),
).scalar()
# Database: 1 query
```

#### Pattern 4: Bulk Insert (Import Historical Data)

❌ **INEFFICIENT** (Individual inserts)
```python
for data in import_data:
    request = RecognitionRequest(**data)
    session.add(request)
session.commit()
# Database: 1000+ individual INSERT statements
```

✅ **OPTIMIZED** (Bulk insert)
```python
session.bulk_insert_mappings(RecognitionRequest, import_data)
session.commit()
# Database: 1 bulk INSERT
```

Or faster with raw SQL:
```python
connection = engine.raw_connection()
cursor = connection.cursor()

cursor.copy_from(
    csv_buffer,
    'recognition_requests',
    sep=',',
    columns=['id', 'image_url', 'status', ...]
)
connection.commit()
# Fastest: PostgreSQL COPY command
```

### Query Analysis Tools

#### EXPLAIN ANALYZE

```sql
-- Shows execution plan and actual statistics
EXPLAIN ANALYZE
SELECT r.id, r.plate_number, r.status, u.username 
FROM recognition_requests r
LEFT JOIN users u ON r.created_by = u.id
WHERE r.created_at >= NOW() - INTERVAL '7 days'
AND r.status = 'COMPLETED'
ORDER BY r.created_at DESC
LIMIT 50;
```

Output interpretation:
```
Limit  (cost=0.42..1.15 rows=50)
  ->  Sort  (cost=0.42..1.15 rows=1023)
    ->  Seq Scan on recognition_requests r  (cost=0.00..0.42 rows=1023)
           Filter: ((created_at >= NOW() - '7 days'::interval)
                    AND (status = 'COMPLETED'::recognition_status))
```

❌ "Seq Scan" = Full table scan (bad for large tables)  
✅ "Index Scan" = Using index (good)  
✅ "Cost" < 1000 = Good, > 10000 = Investigate

#### SQLAlchemy Query Debug

```python
from sqlalchemy import event
import logging

# Enable SQL logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Or programmatically
@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    print(f"Query: {statement}")
    print(f"Params: {params}")
```

---

## Index Tuning

### Index Health Check

```sql
-- Unused indexes (performance drain)
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY idx_size DESC;

-- Create view for ongoing monitoring
CREATE VIEW unused_indexes AS
SELECT schemaname, tablename, indexname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE idx_scan = 0;
```

### Index Bloat Analysis

```sql
-- Indexes with >30% wasted space (should rebuild)
WITH index_bloat AS (
    SELECT 
        schemaname, 
        tablename, 
        indexname,
        pg_relation_size(indexrelid) as size,
        pg_size_pretty(pg_relation_size(indexrelid)) as size_pretty
    FROM pg_stat_user_indexes
)
SELECT * 
FROM index_bloat
ORDER BY size DESC
LIMIT 20;

-- Rebuild bloated indexes (online, non-blocking)
REINDEX INDEX CONCURRENTLY idx_recognition_created_at;
```

### Missing Indexes Detection

```sql
-- Queries reading most data (candidates for indexes)
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time,
    rows
FROM pg_stat_statements
WHERE query LIKE '%recognition_requests%'
ORDER BY total_time DESC
LIMIT 10;

-- Requires: CREATE EXTENSION pg_stat_statements;
```

---

## Connection Pooling

### SQLAlchemy Async Pool Configuration

```python
# apps/api/app/shared/database.py

from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    async_sessionmaker, 
    create_async_engine,
    AsyncConnection
)

engine = create_async_engine(
    settings.database_url,
    
    # Connection Pool Settings
    pool_size=20,              # Number of persistent connections
    max_overflow=10,           # Max overflow connections
    pool_recycle=3600,         # Recycle connections after 1 hour
    pool_pre_ping=True,        # Test connection before using
    
    # Performance Settings
    echo=settings.debug,        # Log all SQL (dev only)
    echo_pool=False,            # Log pool events
    
    # Engine Tweaks
    execution_options={
        "isolation_level": "READ_COMMITTED",  # Balance between consistency & performance
        "prepared_statement_cache_size": 500,
        "prepared_statement_name_func": lambda *args: f"pst_{hash(args[0])}",
    }
)

# Connection pool factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Usage in FastAPI dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
```

### Pool Monitoring

```sql
-- View active connections
SELECT datname, usename, state, count(*)
FROM pg_stat_activity
WHERE state IS NOT NULL
GROUP BY datname, usename, state;

-- Kill idle connections (cleanup)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle' 
AND query_start < NOW() - INTERVAL '30 minutes';

-- Monitor connection pool saturation
SELECT 
    COUNT(*) as total_connections,
    COUNT(*) FILTER (WHERE state = 'active') as active,
    COUNT(*) FILTER (WHERE state = 'idle') as idle,
    COUNT(*) FILTER (WHERE state = 'idle in transaction') as idle_txn
FROM pg_stat_activity
WHERE datname = 'plate_recognition';
```

### Connection Pool Sizing Formula

```
Optimal Pool Size = 
    (Core Count * 2) + Effective Spindle Count
    
For cloud/containerized:
    = (2-4) x Number of FastAPI Workers
    
For our setup (8-core server, 4 workers):
    = pool_size: 20
    = max_overflow: 10
    = Total capacity: 30 concurrent queries
```

---

## Caching Strategy

### Query Result Caching (Redis)

```python
# apps/api/app/services/recognition.py

import hashlib
import json
from redis.asyncio import Redis
from datetime import timedelta

async def get_recognition_with_cache(
    session: AsyncSession,
    redis: Redis,
    request_id: UUID,
    cache_ttl: int = 3600  # 1 hour
) -> RecognitionRequest:
    # Generate cache key
    cache_key = f"recognition:{request_id}"
    
    # Try cache first
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Cache miss: query database
    result = await session.execute(
        select(RecognitionRequest).filter(RecognitionRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    
    if request:
        # Cache the result
        await redis.setex(
            cache_key,
            timedelta(seconds=cache_ttl),
            json.dumps(request, default=str)
        )
    
    return request

# Cache invalidation on update
async def update_recognition(session: AsyncSession, redis: Redis, request: RecognitionRequest):
    await session.merge(request)
    await session.commit()
    
    # Invalidate cache
    await redis.delete(f"recognition:{request.id}")
    
    return request
```

### List Query Caching (Pagination)

```python
async def get_recognitions_paginated(
    session: AsyncSession,
    redis: Redis,
    page: int = 1,
    page_size: int = 50,
    cache_ttl: int = 300  # 5 minutes for lists
) -> dict:
    # Cache key includes pagination params
    cache_key = f"recognitions:list:{page}:{page_size}"
    
    # Check cache
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Query with offset/limit
    offset = (page - 1) * page_size
    
    result = await session.execute(
        select(RecognitionRequest)
        .where(RecognitionRequest.deleted_at.is_(None))
        .order_by(RecognitionRequest.created_at.desc())
        .offset(offset)
        .limit(page_size + 1)  # +1 to detect "more" without extra query
    )
    
    requests = result.scalars().all()
    has_more = len(requests) > page_size
    requests = requests[:page_size]
    
    total_result = await session.execute(
        select(func.count(RecognitionRequest.id))
        .where(RecognitionRequest.deleted_at.is_(None))
    )
    total = total_result.scalar()
    
    response = {
        'items': requests,
        'total': total,
        'page': page,
        'page_size': page_size,
        'has_more': has_more
    }
    
    # Cache response
    await redis.setex(cache_key, timedelta(seconds=cache_ttl), json.dumps(response, default=str))
    
    return response
```

### Cache Invalidation Pattern (Pub/Sub)

```python
# Invalidate cache when data changes
async def invalidate_recognition_cache(redis: Redis, request_id: UUID):
    patterns = [
        f"recognition:{request_id}",
        "recognitions:list:*",  # Invalidate all list caches
    ]
    
    for pattern in patterns:
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)
    
    # Publish invalidation event for subscribers
    await redis.publish(f"cache_invalidation", json.dumps({
        'type': 'recognition_updated',
        'request_id': str(request_id)
    }))
```

---

## PostgreSQL Configuration

### Docker Configuration (docker-compose.yml)

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: plate_recognition
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
    
    volumes:
      - db_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    
    command:
      - "postgres"
      - "-c"
      - "max_connections=100"
      - "-c"
      - "shared_buffers=256MB"
      - "-c"
      - "effective_cache_size=1GB"
      - "-c"
      - "maintenance_work_mem=64MB"
      - "-c"
      - "checkpoint_completion_target=0.9"
      - "-c"
      - "wal_buffers=16MB"
      - "-c"
      - "default_statistics_target=100"
      - "-c"
      - "random_page_cost=1.1"
      - "-c"
      - "effective_io_concurrency=200"
      - "-c"
      - "work_mem=26214kB"
      - "-c"
      - "min_wal_size=1GB"
      - "-c"
      - "max_wal_size=4GB"
      - "-c"
      - "log_min_duration_statement=1000"  # Log slow queries (>1s)
      - "-c"
      - "log_line_prefix='%t [%p] %u@%d '"
```

### Dynamic Configuration (postgresql.conf)

```ini
# postgresql.conf (for production)

# ===== Memory Settings =====
shared_buffers = 256MB           # 25% of system RAM
effective_cache_size = 1GB       # 50-75% of system RAM
work_mem = 26MB                  # shared_buffers / max_connections

# ===== Checkpoint Settings (Write Performance) =====
checkpoint_completion_target = 0.9
wal_buffers = 16MB
min_wal_size = 1GB
max_wal_size = 4GB
maintenance_work_mem = 64MB

# ===== Query Planning =====
random_page_cost = 1.1           # SSD: 1.1, HDD: 4.0
effective_io_concurrency = 200   # SSD capable
default_statistics_target = 100  # More stats for better plans

# ===== Logging (Monitoring) =====
log_min_duration_statement = 1000    # Log queries > 1 second
log_line_prefix = '%t [%p] %u@%d '
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_statement = 'ddl'               # Log schema changes

# ===== Vacuum & Analyze =====
autovacuum = on
autovacuum_naptime = 10s
autovacuum_vacuum_threshold = 50
autovacuum_analyze_threshold = 50
autovacuum_vacuum_cost_delay = 20ms
```

---

## Monitoring & Alerting

### PostgreSQL Health Dashboard

```bash
# Install monitoring extension
docker-compose exec db psql -U postgres -d plate_recognition -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements"

# Create monitoring views
docker-compose exec db psql -U postgres -d plate_recognition << 'EOF'

CREATE VIEW db_health_check AS
SELECT 
    'Database Size' as metric, 
    pg_size_pretty(pg_database_size('plate_recognition')) as value
UNION ALL
SELECT 
    'Active Connections', 
    COUNT(*)::text 
FROM pg_stat_activity
WHERE state = 'active'
UNION ALL
SELECT 
    'Idle Connections',
    COUNT(*)::text
FROM pg_stat_activity
WHERE state = 'idle'
UNION ALL
SELECT 
    'Cache Hit Ratio (%)',
    ROUND(
        SUM(CASE WHEN blks_hit > 0 THEN blks_hit ELSE 0 END)::numeric 
        / SUM(CASE WHEN blks_hit + blks_read > 0 THEN blks_hit + blks_read ELSE 1 END) * 100, 
        2
    )::text
FROM pg_stat_user_tables
UNION ALL
SELECT
    'Slow Queries (>1s)',
    COUNT(*)::text
FROM pg_stat_statements
WHERE mean_time > 1000;

EOF
```

### Python Monitoring Client

```python
# apps/api/app/shared/monitoring.py

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

class DatabaseMonitor:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_connection_stats(self) -> dict:
        """Current connection status"""
        result = await self.session.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE state = 'active') as active,
                COUNT(*) FILTER (WHERE state = 'idle') as idle
            FROM pg_stat_activity
            WHERE datname = 'plate_recognition'
        """))
        row = result.first()
        return dict(row._mapping) if row else {}
    
    async def get_slow_queries(self, threshold_ms: int = 1000) -> list:
        """Queries slower than threshold"""
        result = await self.session.execute(text(f"""
            SELECT query, calls, mean_time, max_time
            FROM pg_stat_statements
            WHERE mean_time > {threshold_ms}
            ORDER BY mean_time DESC
            LIMIT 10
        """))
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def get_cache_hit_ratio(self) -> float:
        """Overall cache effectiveness (0-100%)"""
        result = await self.session.execute(text("""
            SELECT 
                SUM(blks_hit)::float / 
                NULLIF(SUM(blks_hit + blks_read), 0) * 100 as ratio
            FROM pg_stat_user_tables
        """))
        row = result.first()
        return row[0] if row and row[0] else 0.0
    
    async def get_table_stats(self, table_name: str) -> dict:
        """Row count and size for specific table"""
        result = await self.session.execute(text(f"""
            SELECT 
                n_live_tup as live_rows,
                pg_size_pretty(pg_total_relation_size('{table_name}')) as size
            FROM pg_stat_user_tables
            WHERE relname = '{table_name}'
        """))
        row = result.first()
        return dict(row._mapping) if row else {}

# Usage in FastAPI
async def health_check_extended(db: AsyncSession) -> dict:
    monitor = DatabaseMonitor(db)
    
    return {
        "status": "ok",
        "database": {
            "connections": await monitor.get_connection_stats(),
            "cache_hit_ratio": await monitor.get_cache_hit_ratio(),
            "recognition_requests": await monitor.get_table_stats('recognition_requests'),
        },
        "slow_queries": await monitor.get_slow_queries()
    }
```

### Alerting Rules (Prometheus/Grafana)

```yaml
# prometheus-rules.yml

groups:
  - name: postgresql
    rules:
      # Alert: Too many connections
      - alert: PostgresSQLTooManyConnections
        expr: pg_stat_activity_count > 80
        for: 5m
        annotations:
          summary: "PostgreSQL has {{ $value }} connections (threshold: 80)"
      
      # Alert: Cache hit ratio low
      - alert: PostgresCacheLowHitRatio
        expr: pg_cache_hit_ratio < 90
        for: 10m
        annotations:
          summary: "Cache hit ratio is {{ $value }}% (threshold: 90%)"
      
      # Alert: Slow query detected
      - alert: PostgresSlowQuery
        expr: pg_stat_statements_mean_time_seconds > 1
        for: 5m
        annotations:
          summary: "Slow query detected: {{ $value }}s average"
      
      # Alert: Database size growing
      - alert: PostgresDatabaseGrowth
        expr: rate(pg_database_size_bytes[1h]) > 1e8  # 100MB/hour
        for: 10m
        annotations:
          summary: "Database growing at {{ $value }} bytes/hour"
```

---

## Load Testing

### Locust Test Script

```python
# tests/load_test.py

from locust import HttpUser, task, between
import random
from uuid import uuid4

class RecognitionAPIUser(HttpUser):
    wait_time = between(1, 5)  # Wait 1-5 seconds between requests
    
    def on_start(self):
        """Setup: Create test file"""
        with open('test_image.jpg', 'rb') as f:
            self.test_image = f.read()
    
    @task(3)
    def upload_recognition(self):
        """Upload image for recognition (70% of traffic)"""
        files = {'file': ('test.jpg', self.test_image)}
        self.client.post("/api/v1/recognition", files=files)
    
    @task(1)
    def get_recognition(self):
        """Get recognition result (20% of traffic)"""
        request_id = str(uuid4())
        self.client.get(f"/api/v1/recognition/{request_id}")
    
    @task(1)
    def list_recognitions(self):
        """List recognitions (10% of traffic)"""
        page = random.randint(1, 100)
        self.client.get(f"/api/v1/recognition?page={page}&page_size=50")

# Run: locust -f tests/load_test.py --host http://localhost:8000
```

### Load Test Execution

```bash
# Start load test with 100 users, 10 hatch rate
locust -f tests/load_test.py \
    --host http://localhost:8000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --headless

# Monitor during test
docker-compose exec db psql -U postgres -d plate_recognition << 'EOF'
WATCH 'SELECT COUNT(*) as active_connections FROM pg_stat_activity WHERE state = "active"'
EOF
```

---

## Performance Checklist

- [ ] All frequently-queried columns indexed
- [ ] Join predicates have indexes
- [ ] Cache hit ratio > 90%
- [ ] Average query time < 100ms
- [ ] Slow query log reviewed weekly
- [ ] Unused indexes removed
- [ ] Connection pool sized correctly
- [ ] Autovacuum running regularly
- [ ] Vacuum analyze stats updated
- [ ] Load test passed (100+ concurrent users)

Next: See [`04-SECURITY-BEST-PRACTICES.md`](04-SECURITY-BEST-PRACTICES.md)
