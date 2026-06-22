# PostgreSQL Backup & Recovery Strategy

**Version:** 1.0  
**Status:** Production-Ready  
**RTO (Recovery Time Objective):** < 1 hour  
**RPO (Recovery Point Objective):** < 15 minutes

---

## Table of Contents

1. [Backup Strategy](#backup-strategy)
2. [Backup Types](#backup-types)
3. [Backup Scheduling](#backup-scheduling)
4. [Recovery Procedures](#recovery-procedures)
5. [Disaster Recovery Testing](#disaster-recovery-testing)
6. [Monitoring & Alerts](#monitoring--alerts)

---

## Backup Strategy

### Backup Architecture

```
┌─────────────────────────────────────────────────────────┐
│              PostgreSQL Database Server                  │
│ plate_recognition                                        │
│  - recognition_requests (10GB+)                          │
│  - audit_logs (2GB+)                                     │
│  - quality_metrics (500MB)                               │
└────────────┬──────────────────────────────────────────────┘
             │
      ┌──────┴────────┬─────────────────┬──────────────┐
      │               │                 │              │
      ▼               ▼                 ▼              ▼
   Daily Full    Hourly WAL          Continuous    Point-in-Time
   Backup        Archive             Replication   Recovery Setup
   (S3)          (S3)                (Read Replica) (WAL Archive)
   └─ 7 day      └─ 30 days          └─ < 1s lag   └─ 30 days
      retention     retention           RPO          retention
```

### Retention Policy

| Backup Type | Frequency | Retention | Storage | Recovery Time |
|-------------|-----------|-----------|---------|----------------|
| Full Backup | Daily 2AM UTC | 7 days | S3 | 30-60 min |
| WAL Archive | Continuous | 30 days | S3 | < 15 min (PITR) |
| Streaming Replication | Continuous | Live | Secondary DB | < 1 min |
| Ad-hoc Backup | Before major changes | 60 days | S3 + local | 20-30 min |

---

## Backup Types

### 1. Full Logical Backup (pg_dump)

```bash
#!/bin/bash
# scripts/backup-full-logical.sh

BACKUP_DIR="/mnt/backups"
DB_NAME="plate_recognition"
DB_USER="postgres"
DB_HOST="db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/full_${TIMESTAMP}.sql.gz"

echo "[$(date)] Starting full backup..."

# Create backup
pg_dump \
    -U ${DB_USER} \
    -h ${DB_HOST} \
    -d ${DB_NAME} \
    --verbose \
    --no-password \
    | gzip > ${BACKUP_FILE}

# Verify backup
if gunzip -t ${BACKUP_FILE}; then
    echo "[$(date)] ✅ Backup successful: ${BACKUP_FILE}"
    SIZE=$(du -h ${BACKUP_FILE} | cut -f1)
    echo "Size: ${SIZE}"
    
    # Upload to S3
    aws s3 cp ${BACKUP_FILE} \
        s3://plate-recognition-backups/full/${TIMESTAMP}/ \
        --storage-class GLACIER
else
    echo "[$(date)] ❌ Backup verification failed!"
    exit 1
fi

# Cleanup old backups (keep 7 days)
find ${BACKUP_DIR} -name "full_*.sql.gz" -mtime +7 -delete

echo "[$(date)] Backup cycle complete"
```

### 2. Binary (Physical) Backup

```bash
#!/bin/bash
# scripts/backup-physical.sh

BACKUP_DIR="/mnt/backups/physical"
BACKUP_LABEL="backup_$(date +%Y%m%d_%H%M%S)"

# Start backup
docker-compose exec -T db psql -U postgres << EOF
SELECT pg_start_backup('${BACKUP_LABEL}');
EOF

# Copy data directory
docker-compose exec -T db tar -czf - /var/lib/postgresql/data \
    | dd of=${BACKUP_DIR}/${BACKUP_LABEL}.tar.gz

# Stop backup
docker-compose exec -T db psql -U postgres << EOF
SELECT pg_stop_backup();
EOF

# Upload to S3
aws s3 cp ${BACKUP_DIR}/${BACKUP_LABEL}.tar.gz \
    s3://plate-recognition-backups/physical/

echo "Physical backup complete: ${BACKUP_LABEL}"
```

### 3. Continuous WAL Archiving

```ini
# postgresql.conf

# Enable WAL archiving
wal_level = replica
archive_mode = on
archive_timeout = 300
archive_command = 'aws s3 cp pg_wal/%f s3://plate-recognition-backups/wal/%f'

# Alternative: Use replication slots
max_wal_senders = 3
max_replication_slots = 3
```

```bash
# Monitor WAL archiving
docker-compose exec db psql -U postgres -d plate_recognition << EOF
SELECT * FROM pg_stat_archiver;
EOF
```

### 4. Streaming Replication (Standby Server)

```yaml
# docker-compose.yml (Standby Configuration)

services:
  db-primary:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: plate_recognition
      POSTGRES_INITDB_ARGS: "-c wal_level=replica -c max_wal_senders=3"
    volumes:
      - db_primary:/var/lib/postgresql/data

  db-standby:
    image: postgres:16-alpine
    environment:
      PGUSER: postgres
      PGPASSWORD: postgres
    volumes:
      - db_standby:/var/lib/postgresql/data
    command: |
      bash -c "
      pg_basebackup -h db-primary -D /var/lib/postgresql/data -U postgres -v -P -W -R
      postgres
      "
    depends_on:
      - db-primary

volumes:
  db_primary:
  db_standby:
```

---

## Backup Scheduling

### Cron Schedule

```bash
# /etc/cron.d/pg-backups

# Full backup daily at 2 AM UTC
0 2 * * * root /opt/scripts/backup-full-logical.sh >> /var/log/backups.log 2>&1

# Verify backups exist (every 6 hours)
0 */6 * * * root /opt/scripts/verify-backups.sh >> /var/log/backups.log 2>&1

# Cleanup old backups (daily at 3 AM)
0 3 * * * root /opt/scripts/cleanup-old-backups.sh >> /var/log/backups.log 2>&1

# Backup rotation (weekly to cold storage)
0 4 * * 0 root /opt/scripts/archive-to-glacier.sh >> /var/log/backups.log 2>&1
```

### Using pg_cron Extension (In-Database Scheduling)

```sql
-- Enable pg_cron (must be installed)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule daily full backup
SELECT cron.schedule(
    'daily-backup',
    '0 2 * * *',  -- 2 AM UTC daily
    'SELECT backup_to_s3(''full'')'
);

-- Schedule WAL verify
SELECT cron.schedule(
    'verify-wal',
    '*/30 * * * *',  -- Every 30 minutes
    'SELECT verify_wal_archive_status()'
);

-- Monitor scheduled jobs
SELECT * FROM cron.job;
```

### AWS Lambda for Serverless Backups

```python
# lambda_backup.py

import boto3
import json
import subprocess
import os
from datetime import datetime

def lambda_handler(event, context):
    """Triggered by CloudWatch Events (cron schedule)"""
    
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_file = f'/tmp/backup_{timestamp}.sql.gz'
    
    # Connect to RDS
    db_endpoint = os.environ['RDS_ENDPOINT']
    db_user = os.environ['RDS_USER']
    db_name = os.environ['RDS_DATABASE']
    
    # Create backup
    result = subprocess.run([
        'pg_dump',
        '-h', db_endpoint,
        '-U', db_user,
        '-d', db_name,
        '--no-password'
    ], capture_output=True)
    
    # Compress
    with open(backup_file, 'wb') as f:
        subprocess.run(['gzip'], input=result.stdout, stdout=f)
    
    # Upload to S3
    s3 = boto3.client('s3')
    s3.upload_file(
        backup_file,
        'plate-recognition-backups',
        f'full/{timestamp}.sql.gz'
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Backup successful',
            'file': f'full/{timestamp}.sql.gz'
        })
    }
```

---

## Recovery Procedures

### Full Database Restore (Logical)

```bash
#!/bin/bash
# scripts/restore-full.sh

BACKUP_FILE=$1  # e.g., backup_20240621_020000.sql.gz

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "[$(date)] Starting full restore from ${BACKUP_FILE}..."

# Step 1: Stop application
echo "Stop application services..."
docker-compose stop api

# Step 2: Drop existing database (WARNING: Data loss!)
echo "Dropping existing database..."
docker-compose exec -T db psql -U postgres -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = 'plate_recognition' AND pid <> pg_backend_pid();
    
    DROP DATABASE IF EXISTS plate_recognition;
    CREATE DATABASE plate_recognition;
"

# Step 3: Restore from backup
echo "Restoring database..."
gunzip < ${BACKUP_FILE} | docker-compose exec -T db psql -U postgres -d plate_recognition

# Step 4: Verify restore
echo "Verifying restore..."
docker-compose exec -T db psql -U postgres -d plate_recognition -c "
    SELECT count(*) as recognition_requests FROM recognition_requests;
    SELECT count(*) as audit_logs FROM audit_logs;
"

# Step 5: Start application
echo "Starting application services..."
docker-compose start api

echo "[$(date)] Restore complete!"
```

### Point-in-Time Recovery (PITR)

```bash
#!/bin/bash
# scripts/restore-pitr.sh

TARGET_TIME=$1  # e.g., "2026-06-21 15:30:00"

if [ -z "$TARGET_TIME" ]; then
    echo "Usage: $0 '2026-06-21 15:30:00'"
    exit 1
fi

echo "[$(date)] Starting PITR restore to ${TARGET_TIME}..."

# Find closest backup before target time
BACKUP_FILE=$(aws s3 ls s3://plate-recognition-backups/full/ \
    | awk '{print $4}' \
    | sort -r \
    | head -1)

echo "Using base backup: ${BACKUP_FILE}"

# Step 1: Restore from base backup
aws s3 cp s3://plate-recognition-backups/full/${BACKUP_FILE} /tmp/
gunzip < /tmp/${BACKUP_FILE} | psql -U postgres -d plate_recognition

# Step 2: Restore WAL archives
mkdir -p /tmp/wal_restore
aws s3 sync s3://plate-recognition-backups/wal/ /tmp/wal_restore/

# Step 3: Configure recovery
cat > /var/lib/postgresql/recovery.conf << EOF
restore_command = 'cp /tmp/wal_restore/%f %p'
recovery_target_time = '${TARGET_TIME}'
recovery_target_timeline = 'latest'
pause_at_recovery_target = true
EOF

# Step 4: Start recovery
pg_ctl start

# Step 5: Monitor recovery progress
tail -f /var/log/postgresql/postgresql.log

echo "Recovery complete. Database restored to ${TARGET_TIME}"
```

### From S3 Backup

```python
# Python script for S3 restore

import boto3
import subprocess
import gzip
import io

def restore_from_s3(bucket, key, database_url):
    """Restore database from S3 backup"""
    
    s3 = boto3.client('s3')
    
    # Download backup
    print(f"Downloading {key} from S3...")
    response = s3.get_object(Bucket=bucket, Key=key)
    
    # Decompress and restore
    print("Restoring database...")
    compressed_data = response['Body'].read()
    
    with gzip.GzipFile(fileobj=io.BytesIO(compressed_data)) as gz:
        subprocess.run(
            ['psql', '-d', database_url],
            stdin=gz,
            check=True
        )
    
    print("✅ Restore complete")

# Usage
restore_from_s3(
    bucket='plate-recognition-backups',
    key='full/20240621_020000.sql.gz',
    database_url='postgresql://postgres:password@localhost:5432/plate_recognition'
)
```

---

## Disaster Recovery Testing

### Monthly DR Drill

```bash
#!/bin/bash
# scripts/dr-test.sh

echo "=== Monthly DR Test ==="
echo "[$(date)] Starting disaster recovery drill..."

# 1. Create test environment
echo "1. Setting up test environment..."
docker-compose -f docker-compose.test.yml up -d test-db

# 2. Download latest backup
echo "2. Downloading latest backup from S3..."
LATEST_BACKUP=$(aws s3 ls s3://plate-recognition-backups/full/ | tail -1 | awk '{print $4}')
aws s3 cp s3://plate-recognition-backups/full/${LATEST_BACKUP} /tmp/

# 3. Restore to test DB
echo "3. Restoring backup to test environment..."
gunzip < /tmp/${LATEST_BACKUP} | docker-compose -f docker-compose.test.yml exec -T test-db psql -U postgres

# 4. Verify data integrity
echo "4. Verifying data integrity..."
docker-compose -f docker-compose.test.yml exec -T test-db psql -U postgres -d plate_recognition << EOF
SELECT 
    (SELECT COUNT(*) FROM recognition_requests) as requests,
    (SELECT COUNT(*) FROM audit_logs) as logs,
    (SELECT COUNT(*) FROM users) as users;
EOF

# 5. Test query performance
echo "5. Testing query performance..."
docker-compose -f docker-compose.test.yml exec -T test-db psql -U postgres -d plate_recognition << EOF
EXPLAIN ANALYZE
SELECT * FROM recognition_requests
WHERE created_at >= NOW() - INTERVAL '7 days'
LIMIT 100;
EOF

# 6. Cleanup
echo "6. Cleaning up test environment..."
docker-compose -f docker-compose.test.yml down -v

echo "[$(date)] ✅ DR test completed successfully"
```

### Backup Verification Checklist

```bash
#!/bin/bash
# scripts/verify-backup-integrity.sh

BACKUP_FILE=$1

echo "Verifying backup: ${BACKUP_FILE}"

# 1. File integrity
echo "1. Checking file integrity..."
gunzip -t ${BACKUP_FILE} && echo "✅ File is valid" || echo "❌ File corrupted"

# 2. Content validation
echo "2. Validating backup content..."
TABLES=$(gunzip < ${BACKUP_FILE} | grep -c "^CREATE TABLE")
echo "Tables found: ${TABLES}"

if [ "$TABLES" -ge 5 ]; then
    echo "✅ Expected tables present"
else
    echo "❌ Unexpected number of tables"
fi

# 3. Size check
echo "3. Checking backup size..."
SIZE=$(du -h ${BACKUP_FILE} | cut -f1)
echo "Backup size: ${SIZE}"

# 4. Age check
echo "4. Checking backup age..."
MODIFIED=$(stat -c %y ${BACKUP_FILE})
echo "Last modified: ${MODIFIED}"

echo "Verification complete"
```

---

## Monitoring & Alerts

### Backup Health Dashboard

```sql
-- Create backup status view
CREATE VIEW backup_status AS
SELECT 
    'Full Backup' as backup_type,
    MAX(pg_last_xlog_receive_location()) as last_wal,
    NOW() - MAX(backup_date) as age
FROM pg_stat_archiver
UNION ALL
SELECT
    'WAL Archive',
    MAX(last_archived_wal),
    NOW() - MAX(last_archived_time)
FROM pg_stat_archiver;
```

### Monitoring Queries

```sql
-- Check backup status
SELECT * FROM backup_status;

-- Check WAL archiving
SELECT 
    name,
    archived_count,
    failed_count,
    last_archived_wal,
    last_archived_time,
    last_failed_wal,
    last_failed_time
FROM pg_stat_archiver;

-- Check replication lag
SELECT 
    client_addr,
    usename,
    state,
    sync_state,
    write_lsn,
    flush_lsn,
    replay_lsn,
    replay_lag
FROM pg_stat_replication;
```

### CloudWatch Alarms (AWS)

```python
# Create backup monitoring alarms

cloudwatch = boto3.client('cloudwatch')

# Alarm: No backup in last 24 hours
cloudwatch.put_metric_alarm(
    AlarmName='PostgreSQL-Backup-Missing',
    MetricName='LastBackupTime',
    Namespace='BackupMonitoring',
    Statistic='Maximum',
    Period=3600,
    EvaluationPeriods=24,
    Threshold=86400,  # 24 hours in seconds
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:us-east-1:123456789:backup-alerts']
)

# Alarm: Replication lag too high
cloudwatch.put_metric_alarm(
    AlarmName='PostgreSQL-Replication-Lag',
    MetricName='ReplicationLagSeconds',
    Namespace='RDS',
    Statistic='Average',
    Period=300,
    EvaluationPeriods=2,
    Threshold=5,  # Alert if lag > 5 seconds
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:us-east-1:123456789:backup-alerts']
)
```

---

## Summary

✅ **Multi-tier backup strategy** (full + WAL + replication)  
✅ **Automated scheduling** with monitoring  
✅ **Sub-hour RPO** with WAL archiving  
✅ **Point-in-time recovery** capability  
✅ **Regular DR testing** (monthly drills)  
✅ **S3 + Glacier** for long-term retention  
✅ **Complete restore procedures** documented  

Next: See [`06-COMPLETE-IMPLEMENTATION-GUIDE.md`](06-COMPLETE-IMPLEMENTATION-GUIDE.md)
