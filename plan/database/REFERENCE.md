# PostgreSQL Reference — Queries & Commands

**Quick-reference cheat sheet for database operations**

---

## Table of Contents

1. [Connection & Status](#connection--status)
2. [Table & Index Inspection](#table--index-inspection)
3. [Performance Analysis](#performance-analysis)
4. [Maintenance Operations](#maintenance-operations)
5. [Troubleshooting Commands](#troubleshooting-commands)
6. [Backup & Recovery](#backup--recovery)
7. [SQLAlchemy Snippets](#sqlalchemy-snippets)

---

## Connection & Status

### Connect to Database

```bash
# From Docker
docker-compose exec db psql -U postgres -d plate_recognition

# From host (requires port forwarding)
psql -U postgres -h localhost -d plate_recognition

# With password prompt
psql -U app_user -h localhost -d plate_recognition -W
```

### Check PostgreSQL Version

```sql
SELECT version();

-- Output: PostgreSQL 16.0 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 12.2.0, 64-bit
```

### List Databases

```sql
\l
-- or SQL equivalent:
SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
FROM pg_database
ORDER BY pg_database_size(datname) DESC;
```

### Check Active Connections

```sql
SELECT 
    datname,
    usename,
    application_name,
    state,
    query_start,
    query
FROM pg_stat_activity
WHERE datname = 'plate_recognition'
ORDER BY query_start DESC;
```

### Database Stats

```sql
SELECT 
    datname,
    pg_size_pretty(pg_database_size(datname)) as size,
    (SELECT count(*) FROM pg_stat_activity WHERE datname = 'plate_recognition') as active_connections,
    last_vacuum,
    last_autovacuum,
    last_analyze
FROM pg_stat_user_tables
WHERE datname = 'plate_recognition';
```

---

## Table & Index Inspection

### List All Tables

```sql
\dt

-- SQL equivalent:
SELECT tablename FROM pg_tables WHERE schemaname = 'public';
```

### Table Structure

```sql
\d recognition_requests

-- SQL equivalent:
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'recognition_requests'
ORDER BY ordinal_position;
```

### Table Size

```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as indexes_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### List Indexes

```sql
\di

-- SQL equivalent:
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

### Index Size & Stats

```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Unused Indexes

```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as scans
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Constraints

```sql
SELECT 
    constraint_name,
    table_name,
    column_name,
    constraint_type
FROM information_schema.key_column_usage
WHERE table_name = 'recognition_requests'
ORDER BY constraint_name;
```

---

## Performance Analysis

### EXPLAIN ANALYZE (Query Plan)

```sql
EXPLAIN ANALYZE
SELECT r.id, r.plate_number, u.username
FROM recognition_requests r
LEFT JOIN users u ON r.created_by = u.id
WHERE r.created_at >= NOW() - INTERVAL '7 days'
AND r.status = 'COMPLETED'
ORDER BY r.created_at DESC
LIMIT 50;

-- Check output for:
-- - Seq Scan (bad) vs Index Scan (good)
-- - Actual Rows vs Planned Rows (should match)
-- - Total Cost (lower is better)
```

### Slow Queries

```sql
-- Requires: CREATE EXTENSION pg_stat_statements;

SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time,
    rows
FROM pg_stat_statements
WHERE query LIKE '%recognition_requests%'
ORDER BY mean_time DESC
LIMIT 20;
```

### Cache Hit Ratio

```sql
-- Overall cache hit ratio
SELECT 
    SUM(heap_blks_read) as total_heap_read,
    SUM(heap_blks_hit) as total_heap_hit,
    SUM(heap_blks_hit) / (SUM(heap_blks_hit) + SUM(heap_blks_read)) as ratio
FROM pg_stat_user_tables;

-- Per table
SELECT 
    schemaname,
    tablename,
    heap_blks_read,
    heap_blks_hit,
    ROUND(
        heap_blks_hit::float / NULLIF(heap_blks_hit + heap_blks_read, 0) * 100,
        2
    ) as cache_hit_percent
FROM pg_stat_user_tables
ORDER BY cache_hit_percent ASC;
```

### Table Row Count & Stats

```sql
SELECT 
    schemaname,
    tablename,
    n_live_tup as row_count,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
```

### Connection Pool Status

```sql
SELECT 
    datname,
    state,
    COUNT(*) as count
FROM pg_stat_activity
WHERE datname = 'plate_recognition'
GROUP BY datname, state;

-- Sample output:
-- datname | state | count
-- --------+-------+-------
-- plate_recognition | active | 2
-- plate_recognition | idle | 15
-- plate_recognition | idle in transaction | 0
```

---

## Maintenance Operations

### VACUUM (Cleanup)

```sql
-- Manual vacuum (removes dead rows)
VACUUM recognition_requests;

-- Vacuum with analyze (updates statistics)
VACUUM ANALYZE recognition_requests;

-- Full vacuum (defrags, but locks table - avoid on production)
VACUUM FULL recognition_requests;

-- Aggressive vacuum
VACUUM FULL ANALYZE recognition_requests;
```

### ANALYZE (Update Statistics)

```sql
-- Update statistics for query planner
ANALYZE recognition_requests;

-- Update all table stats
ANALYZE;
```

### REINDEX (Rebuild Indexes)

```sql
-- Rebuild specific index
REINDEX INDEX idx_recognition_created_at;

-- Rebuild concurrent (non-blocking - preferred for production)
REINDEX INDEX CONCURRENTLY idx_recognition_created_at;

-- Rebuild all table indexes
REINDEX TABLE recognition_requests;
```

### Cluster (Physical Reorganization)

```sql
-- Reorganize table based on index (locks table)
CLUSTER recognition_requests USING idx_recognition_created_at;
```

### Autovacuum Status

```sql
-- Check autovacuum settings
SHOW autovacuum;
SHOW autovacuum_naptime;
SHOW autovacuum_vacuum_threshold;
SHOW autovacuum_analyze_threshold;

-- Monitor autovacuum runs
SELECT 
    schemaname,
    relname,
    last_autovacuum,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY last_autovacuum DESC;
```

---

## Troubleshooting Commands

### Kill Idle Connections

```sql
-- Terminate idle connections older than 30 minutes
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND query_start < NOW() - INTERVAL '30 minutes'
AND datname = 'plate_recognition';
```

### Find Blocking Queries

```sql
SELECT 
    blocked.pid as blocked_pid,
    blocked.usename as blocked_user,
    blocking.pid as blocking_pid,
    blocking.usename as blocking_user,
    blocked.query as blocked_query,
    blocking.query as blocking_query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking ON blocking.pid = ANY(pg_blocking_pids(blocked.pid))
WHERE blocked.datname = 'plate_recognition';
```

### Long-Running Queries

```sql
SELECT 
    pid,
    usename,
    state,
    query_start,
    NOW() - query_start as duration,
    query
FROM pg_stat_activity
WHERE datname = 'plate_recognition'
AND query_start < NOW() - INTERVAL '5 minutes'
ORDER BY query_start ASC;
```

### Database Locks

```sql
SELECT 
    l.pid,
    l.mode,
    l.granted,
    a.query,
    a.state
FROM pg_locks l
JOIN pg_stat_activity a ON l.pid = a.pid
WHERE a.datname = 'plate_recognition'
ORDER BY l.pid, l.mode DESC;
```

### Check WAL Status

```sql
-- View WAL archiver status
SELECT * FROM pg_stat_archiver;

-- View replication status (if streaming replication enabled)
SELECT * FROM pg_stat_replication;
```

### List Extensions

```sql
-- Show installed extensions
\dx

-- SQL equivalent:
SELECT extname, extversion FROM pg_extension;
```

---

## Backup & Recovery

### Create Backup

```bash
# Full backup (logical)
pg_dump -U postgres -h localhost -d plate_recognition | gzip > backup.sql.gz

# Binary backup (faster for large DBs)
pg_basebackup -U postgres -h localhost -D /path/to/backup -Ft -z

# Backup with progress
pg_dump -U postgres -h localhost -d plate_recognition --verbose | gzip > backup.sql.gz

# Backup specific table
pg_dump -U postgres -h localhost -d plate_recognition -t recognition_requests | gzip > table_backup.sql.gz
```

### Restore Backup

```bash
# From logical backup
gunzip < backup.sql.gz | psql -U postgres -d plate_recognition

# Check backup before restoring
gunzip -t backup.sql.gz  # Verify integrity

# Restore to new database
gunzip < backup.sql.gz | psql -U postgres -d new_database
```

### List Backups (in Docker)

```bash
# List local backups
ls -lh /mnt/backups/

# List S3 backups
aws s3 ls s3://plate-recognition-backups/full/ --human-readable | head -10
```

---

## SQLAlchemy Snippets

### Async Query Examples

```python
# Import required modules
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.recognition import RecognitionRequest

# Session is provided by dependency injection
async def get_recognitions(session: AsyncSession, skip: int = 0, limit: int = 50):
    """Get paginated recognitions"""
    stmt = select(RecognitionRequest)\
        .where(RecognitionRequest.deleted_at.is_(None))\
        .order_by(desc(RecognitionRequest.created_at))\
        .offset(skip)\
        .limit(limit)
    
    result = await session.execute(stmt)
    return result.scalars().all()

# Count query
async def count_requests(session: AsyncSession):
    """Count total requests"""
    stmt = select(func.count(RecognitionRequest.id))\
        .where(RecognitionRequest.deleted_at.is_(None))
    
    result = await session.execute(stmt)
    return result.scalar()

# Aggregation
async def get_stats(session: AsyncSession):
    """Get aggregated statistics"""
    from sqlalchemy import case
    
    stmt = select(
        func.count(RecognitionRequest.id).label('total'),
        func.sum(case(
            (RecognitionRequest.status == 'COMPLETED', 1),
            else_=0
        )).label('completed'),
        func.avg(RecognitionRequest.confidence_score).label('avg_confidence')
    )
    
    result = await session.execute(stmt)
    return result.first()

# Bulk insert
async def bulk_insert(session: AsyncSession, items: list):
    """Insert multiple records"""
    session.bulk_insert_mappings(RecognitionRequest, items)
    await session.commit()
```

### Raw SQL in SQLAlchemy

```python
from sqlalchemy import text

async def custom_query(session: AsyncSession):
    """Execute raw SQL"""
    query = text("""
        SELECT r.id, r.plate_number, COUNT(*) as count
        FROM recognition_requests r
        WHERE r.created_at >= NOW() - INTERVAL '7 days'
        GROUP BY r.id, r.plate_number
        HAVING COUNT(*) > :threshold
    """)
    
    result = await session.execute(query, {"threshold": 5})
    return result.fetchall()
```

---

## Quick Diagnosis Script

```bash
#!/bin/bash
# scripts/db-diagnosis.sh

echo "=== PostgreSQL Database Diagnosis ==="

DB="plate_recognition"
USER="postgres"
HOST="db"

echo ""
echo "1. Database Size"
docker-compose exec db psql -U $USER -d $DB -c "SELECT pg_size_pretty(pg_database_size('$DB'));"

echo ""
echo "2. Table Count & Rows"
docker-compose exec db psql -U $USER -d $DB -c "
  SELECT schemaname, tablename, n_live_tup as rows
  FROM pg_stat_user_tables
  ORDER BY n_live_tup DESC LIMIT 10;
"

echo ""
echo "3. Active Connections"
docker-compose exec db psql -U $USER -d $DB -c "
  SELECT state, COUNT(*) FROM pg_stat_activity 
  WHERE datname = '$DB' GROUP BY state;
"

echo ""
echo "4. Cache Hit Ratio"
docker-compose exec db psql -U $USER -d $DB -c "
  SELECT ROUND(
    SUM(heap_blks_hit)::float / NULLIF(SUM(heap_blks_hit + heap_blks_read), 0) * 100, 
    2
  ) as cache_hit_percent
  FROM pg_stat_user_tables;
"

echo ""
echo "5. Last Backup"
ls -lh /mnt/backups/ | tail -3

echo ""
echo "=== Diagnosis Complete ==="
```

---

## Useful Links

- **PostgreSQL Documentation:** https://www.postgresql.org/docs/16/
- **SQLAlchemy Async:** https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **Alembic:** https://alembic.sqlalchemy.org/
- **pg_stat_statements:** https://www.postgresql.org/docs/current/pgstatstatements.html

---

**Last Updated:** 2026-06-21
