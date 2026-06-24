# PostgreSQL Migration Management — Alembic Guide

**Version:** 1.0  
**Tool:** Alembic (SQLAlchemy migration tool)  
**Status:** Standard Operating Procedure

---

## Table of Contents

1. [Migration Lifecycle](#migration-lifecycle)
2. [Creating Migrations](#creating-migrations)
3. [Running Migrations](#running-migrations)
4. [Rollback Strategy](#rollback-strategy)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)
7. [CI/CD Integration](#cicd-integration)

---

## Migration Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ Developer Creates Feature                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
        ┌─────────────────────────┐
        │ Generate Migration File │
        │ (auto or manual)        │
        └─────────┬───────────────┘
                  │
                  ▼
        ┌─────────────────────────┐
        │ Review Migration Code   │
        │ Test on local DB        │
        └─────────┬───────────────┘
                  │
                  ▼
        ┌─────────────────────────┐
        │ Commit & PR Review      │
        └─────────┬───────────────┘
                  │
                  ▼
        ┌─────────────────────────┐
        │ Merge to main           │
        └─────────┬───────────────┘
                  │
                  ▼
        ┌─────────────────────────┐
        │ CI/CD: Test on staging  │
        │ - Fresh DB setup        │
        │ - Run all migrations    │
        │ - Run test suite        │
        └─────────┬───────────────┘
                  │
                  ▼
        ┌─────────────────────────┐
        │ Deploy to Production    │
        │ - Pre-deployment backup │
        │ - Run migration         │
        │ - Post-migration checks │
        │ - Rollback if needed    │
        └─────────┬───────────────┘
                  │
                  ▼
        ┌─────────────────────────┐
        │ Monitor & Alert         │
        └─────────────────────────┘
```

---

## Creating Migrations

### Method 1: Auto-Detection (Recommended for Schema Changes)

Alembic compares current models to database state:

```bash
# cd apps/api
alembic revision --autogenerate -m "Add confidence_score to recognition_requests"
```

This generates:

```sql
# migrations/versions/0002_add_confidence.py

def upgrade() -> None:
    op.add_column('recognition_requests', 
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=True))
    op.create_index('idx_recognition_confidence', 'recognition_requests', ['confidence_score'])

def downgrade() -> None:
    op.drop_index('idx_recognition_confidence', table_name='recognition_requests')
    op.drop_column('recognition_requests', 'confidence_score')
```

### Method 2: Manual Migration (For Complex Logic)

```bash
alembic revision -m "Backfill plate_numbers from OCR cache"
```

Creates empty template:

```python
# migrations/versions/0003_backfill_plate.py

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Step 1: Backfill existing data
    connection = op.get_bind()
    connection.execute(
        sa.text("""
            UPDATE recognition_requests
            SET plate_number = (
                SELECT new_values->>'plate_number' 
                FROM audit_logs 
                WHERE entity_id = recognition_requests.id 
                AND operation = 'UPDATE'
                ORDER BY operation_timestamp DESC
                LIMIT 1
            )
            WHERE plate_number IS NULL
        """)
    )
    
    # Step 2: Add constraint if all rows filled
    op.alter_column('recognition_requests', 'plate_number',
        existing_type=sa.VARCHAR(20),
        nullable=False)

def downgrade() -> None:
    op.alter_column('recognition_requests', 'plate_number',
        existing_type=sa.VARCHAR(20),
        nullable=True)
```

### Migration File Structure

```python
"""Add authentication to users table

Revision ID: abc12345def
Revises: prev123456789
Create Date: 2026-06-21 10:30:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = 'abc12345def'
down_revision: Union[str, None] = 'prev123456789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Forward migration: Add columns and constraints"""
    pass

def downgrade() -> None:
    """Rollback migration: Reverse changes"""
    pass
```

---

## Running Migrations

### Local Development

```bash
# Show current database version
alembic current

# Show all available versions
alembic history --verbose

# Apply next migration
alembic upgrade +1

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade rev:abc12345def

# Rollback to initial state
alembic downgrade base

# Dry run (show SQL without executing)
alembic upgrade head --sql
```

### Docker Compose

```bash
# Inside container
docker-compose exec api alembic upgrade head

# Or from host
docker-compose exec -T api alembic upgrade head
```

### Staging/Production

```bash
# Step 1: Backup database
pg_dump -U postgres -h db -d plate_recognition > backup_$(date +%Y%m%d_%H%M%S).sql

# Step 2: Test migration in dry run
docker-compose exec api alembic upgrade head --sql > /tmp/migration.sql

# Step 3: Apply migration with monitoring
docker-compose exec api alembic upgrade head

# Step 4: Verify
docker-compose exec api alembic current
```

---

## Rollback Strategy

### Automatic Rollback (CI/CD Failure)

```yaml
# .github/workflows/deploy.yml (pseudocode)
deploy:
  steps:
    - name: Backup Database
      run: pg_dump ... > backup.sql
    
    - name: Run Migrations
      run: alembic upgrade head
      continue-on-error: true
      id: migration
    
    - name: Run Tests
      run: pytest
      if: steps.migration.outcome == 'success'
    
    - name: Rollback on Test Failure
      if: failure()
      run: |
        alembic downgrade -1
        echo "Migration rolled back due to test failure"
    
    - name: Restore from Backup
      if: failure()
      run: psql < backup.sql
```

### Manual Rollback

```bash
# Check migration history
alembic history

# Rollback to specific point
alembic downgrade 'rev:abc12345def'

# Verify rollback
alembic current
```

### Zero-Downtime Rollback Strategy

For production deployments:

1. **Before deployment**: Create backup of DB
2. **Deploy code** that handles both old and new schema
3. **Run migration** with monitoring
4. **If issues arise**:
   - Stop application
   - Restore DB from backup
   - Rollback application to previous version
   - Restart and verify

---

## Best Practices

### 1. Migration Naming

❌ BAD
```bash
alembic revision --autogenerate -m "update"
alembic revision --autogenerate -m "fix"
```

✅ GOOD
```bash
alembic revision --autogenerate -m "Add confidence_score to recognition_requests"
alembic revision --autogenerate -m "Create index on status for filtering"
alembic revision --autogenerate -m "Add foreign key from requests to users"
```

### 2. One Logical Change Per Migration

❌ BAD
```python
def upgrade():
    # Add 5 new columns
    # Drop 3 old columns
    # Create 10 indexes
    # Backfill data
    # Change constraints
```

✅ GOOD
```bash
# Migration 1: Add new columns
alembic revision -m "Add new_column_1, new_column_2, new_column_3"

# Migration 2: Backfill data
alembic revision -m "Backfill new_column_* from legacy data"

# Migration 3: Add constraints
alembic revision -m "Add NOT NULL constraint to new columns"

# Migration 4: Drop old columns
alembic revision -m "Drop old_column_1, old_column_2, old_column_3"
```

### 3. Test Migrations Locally First

```bash
# Setup fresh local DB
docker-compose down -v
docker-compose up -d db

# Wait for DB to start
sleep 5

# Run all migrations
alembic upgrade head

# Verify schema
docker-compose exec db psql -U postgres -d plate_recognition -c "\d recognition_requests"

# Run tests
pytest tests/

# Test rollback
alembic downgrade -1
alembic upgrade head
```

### 4. Handling Long-Running Migrations

For operations that lock tables:

```python
def upgrade() -> None:
    # Option 1: Use concurrent index creation (doesn't lock writes)
    op.create_index(
        'idx_recognition_plate',
        'recognition_requests',
        ['plate_number'],
        postgresql_concurrently=True
    )
    
    # Option 2: Add columns with defaults efficiently
    op.add_column(
        'recognition_requests',
        sa.Column('new_col', sa.String, server_default='default_value')
    )
    
    # Option 3: Create new table, migrate data, swap
    # (for major schema reorganizations)
```

### 5. Data Integrity During Migrations

```python
def upgrade() -> None:
    # ✅ Wrap in transaction
    with op.batch_alter_table("recognition_requests") as batch_op:
        batch_op.add_column(sa.Column('new_field', sa.String))
        batch_op.create_index('idx_new_field', ['new_field'])
    
    # ✅ Verify constraint before applying
    connection = op.get_bind()
    result = connection.execute(sa.text(
        "SELECT COUNT(*) FROM recognition_requests WHERE new_field IS NULL"
    ))
    if result.scalar() > 0:
        raise Exception("Data integrity check failed")
```

---

## Troubleshooting

### Problem: "Can't locate revision identified by '...'"

```bash
# Cause: Migration history is out of sync
# Solution: Verify migration files exist in versions/

ls -la apps/api/migrations/versions/

# Rebuild revision history
alembic heads
alembic branches
```

### Problem: "FAILED: target database is not up to date"

```bash
# Cause: Pending migrations not applied
# Solution: Check current state and apply migrations

alembic current    # Shows where we are
alembic heads      # Shows where we should be
alembic upgrade head
```

### Problem: "IntegrityError during migration"

```python
# Cause: Data constraint violated
# Solution: Check data before migration

# In migration file:
def upgrade() -> None:
    connection = op.get_bind()
    
    # Debug query
    result = connection.execute(sa.text(
        "SELECT COUNT(DISTINCT user_id) FROM recognition_requests WHERE user_id IS NULL"
    ))
    print(f"Null user_ids: {result.scalar()}")
    
    if result.scalar() > 0:
        raise Exception("Cannot add NOT NULL constraint; existing NULLs detected")
```

### Problem: "Deadlock during concurrent migrations"

```bash
# Cause: Multiple migrations running on same table
# Solution: Serialize migrations

# Run explicitly
alembic upgrade head --step
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/database-migration-test.yml

name: Database Migration Tests

on:
  pull_request:
    paths:
      - 'apps/api/migrations/**'
      - 'apps/api/app/models/**'
      - 'apps/api/requirements.txt'

jobs:
  test-migrations:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_plate_recognition
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd apps/api
          pip install -r requirements.txt
      
      - name: Test forward migration
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test_plate_recognition
        run: |
          cd apps/api
          alembic upgrade head
          alembic current
      
      - name: Test backward migration
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test_plate_recognition
        run: |
          cd apps/api
          alembic downgrade -1
          alembic upgrade +1
      
      - name: Verify schema
        run: |
          cd apps/api
          psql -U postgres -h localhost -d test_plate_recognition -c "\d"
```

### Pre-Deployment Checklist

```bash
#!/bin/bash
# scripts/pre-deploy-db-check.sh

set -e

echo "=== Pre-Deployment Database Check ==="

# 1. Check pending migrations
echo "1. Checking for pending migrations..."
cd apps/api
PENDING=$(alembic heads)
CURRENT=$(alembic current)
if [ "$PENDING" != "$CURRENT" ]; then
    echo "❌ Pending migrations detected!"
    alembic history
    exit 1
fi
echo "✅ No pending migrations"

# 2. Test migration forward/backward
echo "2. Testing migration rollback safety..."
alembic downgrade -1
alembic upgrade +1
echo "✅ Rollback tested successfully"

# 3. Verify database integrity
echo "3. Verifying database constraints..."
psql -U postgres -d plate_recognition -c "SELECT * FROM information_schema.table_constraints WHERE constraint_type = 'FOREIGN KEY';" | wc -l
echo "✅ Foreign keys intact"

echo "=== All checks passed ==="
```

---

## Summary

✅ **Automated migrations** via Alembic  
✅ **Clear versioning** with descriptive names  
✅ **Safe rollback** mechanism  
✅ **CI/CD integration** for testing  
✅ **Data integrity** checks  
✅ **Zero-downtime** deployment strategy  

Next: See [`03-PERFORMANCE-OPTIMIZATION.md`](03-PERFORMANCE-OPTIMIZATION.md)
