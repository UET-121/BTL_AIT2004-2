# PostgreSQL Schema Design — Comprehensive Guide

**Version:** 1.0  
**Last Updated:** 2026-06-21  
**Status:** Active  
**Project:** License Plate Recognition (BTL_AIT2004-2)

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Core Tables](#core-tables)
3. [Indexing Strategy](#indexing-strategy)
4. [Constraints & Integrity](#constraints--integrity)
5. [Partitioning Strategy](#partitioning-strategy)
6. [Schema Versioning](#schema-versioning)
7. [Naming Conventions](#naming-conventions)

---

## Design Philosophy

### Principles

1. **Normalized Design (3NF)**: Eliminate data redundancy while maintaining query performance
2. **ACID Compliance**: Ensure data integrity through transactions
3. **Audit Trail**: Track all changes for compliance and debugging
4. **Horizontal Scalability**: Design for future partitioning and sharding
5. **Performance First**: Denormalize strategically for read-heavy workloads

### Design Patterns Used

| Pattern | Purpose | Usage |
|---------|---------|-------|
| **Soft Delete** | Preserve historical data | `deleted_at` timestamp on mutable records |
| **Audit Trail** | Track changes | `created_by`, `updated_by`, `created_at`, `updated_at` |
| **Type Enumeration** | Constrain values | `ENUM` types for status, roles |
| **JSON Columns** | Flexible attributes | Semi-structured metadata |
| **Temporal Queries** | Time-series analysis | Indexed `created_at` for time-range queries |

---

## Core Tables

### 1. **recognition_requests** (Primary Table)

Stores all license plate recognition requests and their lifecycle.

```sql
CREATE TABLE recognition_requests (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core Business Data
    image_url VARCHAR(2048) NOT NULL UNIQUE,
    plate_number VARCHAR(20),
    status recognition_status NOT NULL DEFAULT 'NOT_STARTED'::recognition_status,
    error_message TEXT,

    -- Detection & Confidence Metrics
    detection_confidence NUMERIC(5, 4) CHECK (detection_confidence >= 0 AND detection_confidence <= 1),
    ocr_confidence NUMERIC(5, 4) CHECK (ocr_confidence >= 0 AND ocr_confidence <= 1),
    confidence_score NUMERIC(5, 4) CHECK (confidence_score >= 0 AND confidence_score <= 1),

    -- Bounding Box (JSONB for flexibility)
    bounding_box JSONB,
    plate_region VARCHAR(50),

    -- Processing Metadata
    needs_review BOOLEAN DEFAULT false,
    review_notes TEXT,
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE,

    -- Audit & Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    updated_by UUID REFERENCES users(id) ON DELETE RESTRICT,
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Workflow Management
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
    max_retries INTEGER DEFAULT 3,
    last_retry_at TIMESTAMP WITH TIME ZONE,

    -- Performance Hints
    processing_duration_ms INTEGER,
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10)
);

-- Indexes
CREATE INDEX idx_recognition_status ON recognition_requests(status) 
    WHERE deleted_at IS NULL;
CREATE INDEX idx_recognition_created_at ON recognition_requests(created_at DESC) 
    WHERE deleted_at IS NULL;
CREATE INDEX idx_recognition_plate_number ON recognition_requests(plate_number) 
    WHERE deleted_at IS NULL AND plate_number IS NOT NULL;
CREATE INDEX idx_recognition_created_by ON recognition_requests(created_by);
CREATE INDEX idx_recognition_needs_review ON recognition_requests(needs_review) 
    WHERE needs_review = true AND deleted_at IS NULL;
CREATE INDEX idx_recognition_user_date ON recognition_requests(created_by, created_at DESC);

-- BRIN Index for time-series queries (efficient for large tables)
CREATE INDEX idx_recognition_created_at_brin ON recognition_requests USING BRIN (created_at);

-- Partial index for active requests (commonly queried)
CREATE INDEX idx_recognition_active ON recognition_requests(id) 
    WHERE status NOT IN ('COMPLETED', 'FAILED') AND deleted_at IS NULL;
```

**Columns Explanation:**

| Column | Type | Purpose |
|--------|------|---------|
| `id` | UUID | Distributed system compatible primary key |
| `image_url` | VARCHAR | S3/Local storage reference; UNIQUE prevents duplicates |
| `status` | ENUM | Lifecycle state; indexed for filtering |
| `bounding_box` | JSONB | Flexible JSON for x,y,width,height; queryable |
| `confidence_score` | NUMERIC(5,4) | Detection result; CHECK ensures 0-1 range |
| `deleted_at` | TIMESTAMP | Soft delete flag; allows recovery |
| `retry_count` | INTEGER | Track failed retries for circuit breaker logic |
| `created_by`, `updated_by` | UUID | Foreign key to users table (audit trail) |

---

### 2. **recognition_details** (Historical Record)

Stores complete ONNX model outputs and intermediate results for debugging.

```sql
CREATE TABLE recognition_details (
    id BIGSERIAL PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES recognition_requests(id) ON DELETE CASCADE,

    -- Model Inference Outputs
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    inference_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    inference_duration_ms INTEGER,

    -- Raw Model Output (JSONB)
    detection_output JSONB NOT NULL,
    ocr_output JSONB NOT NULL,
    preprocessing_metadata JSONB,

    -- Processing Pipeline Steps
    pipeline_stage VARCHAR(50),
    stage_duration_ms INTEGER,

    -- Error Tracking
    error_occurred BOOLEAN DEFAULT false,
    error_log TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_details_request_id ON recognition_details(request_id);
CREATE INDEX idx_details_inference_timestamp ON recognition_details(inference_timestamp DESC);
CREATE INDEX idx_details_model_version ON recognition_details(model_version);
```

---

### 3. **users** (User Management)

Stores API users, reviewers, and system administrators.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic Info
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),

    -- Roles & Permissions
    role user_role NOT NULL DEFAULT 'viewer'::user_role,
    permissions JSONB DEFAULT '{}',

    -- Account Status
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP WITH TIME ZONE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active) WHERE is_active = true;
```

---

### 4. **audit_logs** (Compliance & Debugging)

Immutable audit trail for all important operations.

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,

    -- Operation Details
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    operation VARCHAR(50) NOT NULL, -- INSERT, UPDATE, DELETE, REVIEW
    operation_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Before/After State (JSONB for flexibility)
    old_values JSONB,
    new_values JSONB,

    -- User Info
    user_id UUID,
    user_ip VARCHAR(45),
    user_agent TEXT,

    -- Additional Context
    reason TEXT,
    metadata JSONB
);

-- Indexes for audit queries
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(operation_timestamp DESC);
CREATE INDEX idx_audit_user_id ON audit_logs(user_id);

-- Immutable table (UNLOGGED for performance if audit is replicated separately)
ALTER TABLE audit_logs SET (fillfactor = 100);
```

---

### 5. **quality_metrics** (Analytics Table)

Time-series data for monitoring and reporting.

```sql
CREATE TABLE quality_metrics (
    id BIGSERIAL PRIMARY KEY,

    -- Time Bucket (daily aggregation)
    metric_date DATE NOT NULL,
    metric_hour TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Aggregate Metrics
    total_requests INTEGER NOT NULL,
    successful_recognitions INTEGER NOT NULL,
    failed_requests INTEGER NOT NULL,
    requests_needing_review INTEGER NOT NULL,

    -- Confidence Distribution
    avg_confidence_score NUMERIC(5, 4),
    median_confidence_score NUMERIC(5, 4),
    min_confidence_score NUMERIC(5, 4),
    max_confidence_score NUMERIC(5, 4),

    -- Performance
    avg_processing_time_ms INTEGER,
    p95_processing_time_ms INTEGER,
    p99_processing_time_ms INTEGER,

    -- Model Performance
    model_version VARCHAR(50),
    accuracy_rate NUMERIC(5, 4),

    -- Created
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for time-series queries
CREATE INDEX idx_quality_metric_date ON quality_metrics(metric_date DESC);
CREATE INDEX idx_quality_metric_hour ON quality_metrics(metric_hour DESC);
CREATE UNIQUE INDEX idx_quality_metric_hour_unique ON quality_metrics(metric_hour, model_version);
```

---

## Indexing Strategy

### Index Classification

```sql
-- ===== 1. PRIMARY KEY INDEXES (Automatic)
-- Already created by PRIMARY KEY constraints

-- ===== 2. FOREIGN KEY INDEXES (Recommended)
-- Speeds up JOINs and CASCADE operations
CREATE INDEX idx_fk_recognition_created_by ON recognition_requests(created_by);
CREATE INDEX idx_fk_recognition_details_request ON recognition_details(request_id);

-- ===== 3. SEARCH INDEXES (Filtering)
-- Heavy filtering on status, created_at, plate_number
-- Covered above

-- ===== 4. SORT INDEXES (ORDER BY)
-- Already covered with DESC for time-series

-- ===== 5. FULL-TEXT SEARCH (Plate Numbers)
-- For fuzzy plate matching
ALTER TABLE recognition_requests ADD COLUMN plate_number_tsv tsvector;

CREATE INDEX idx_recognition_plate_tsv ON recognition_requests USING GIN(plate_number_tsv)
    WHERE plate_number_tsv IS NOT NULL;

-- Update trigger (see triggers section)
```

### Index Performance Guidelines

| Scenario | Index Type | Benefits |
|----------|-----------|----------|
| Range queries (dates) | B-Tree | O(log N) lookup |
| Time-series (large tables) | BRIN | Compressed, fast for ordered data |
| JSON queries | GIN | Efficient nested object search |
| Full-text search | GIN + tsvector | Fast text matching |
| Multi-column filtering | Composite | Single index for common queries |

---

## Constraints & Integrity

### ENUM Types

```sql
-- Status Lifecycle
CREATE TYPE recognition_status AS ENUM (
    'NOT_STARTED',
    'PENDING',
    'COMPLETED',
    'NEEDS_REVIEW',
    'FAILED'
);

-- User Roles
CREATE TYPE user_role AS ENUM (
    'admin',
    'reviewer',
    'viewer',
    'api_user'
);
```

### Constraints Applied

```sql
-- ===== Check Constraints (Data Validation)
-- Confidence scores must be 0-1
ALTER TABLE recognition_requests
    ADD CONSTRAINT check_confidence_valid 
    CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1));

-- Processing duration must be positive
ALTER TABLE recognition_details
    ADD CONSTRAINT check_processing_duration 
    CHECK (inference_duration_ms > 0);

-- ===== Unique Constraints (Natural Keys)
ALTER TABLE recognition_requests
    ADD CONSTRAINT unique_image_url 
    UNIQUE (image_url) WHERE deleted_at IS NULL;

ALTER TABLE users
    ADD CONSTRAINT unique_username 
    UNIQUE (username) WHERE deleted_at IS NULL;

-- ===== NOT NULL Constraints
-- Already defined in table creation

-- ===== Foreign Key Constraints (Referential Integrity)
-- Already defined above with CASCADE/RESTRICT/SET NULL options
```

---

## Partitioning Strategy

### Time-Based Partitioning (for large tables)

When `recognition_requests` exceeds 10M rows, partition by month:

```sql
-- ===== Step 1: Create Partitioned Table (future-proof)
-- For now, this is the design; implement when needed

-- Convert existing table to partitioned (major migration):
-- ALTER TABLE recognition_requests PARTITION BY RANGE (YEAR(created_at), MONTH(created_at));

-- Example for future: Split by month
-- CREATE TABLE recognition_requests_2024_06 PARTITION OF recognition_requests
--     FOR VALUES FROM (2024, 6) TO (2024, 7);

-- ===== Step 2: Maintain Partitions with Trigger
-- Auto-create new partitions monthly via scheduled job

-- ===== Benefits
-- - Faster queries on time ranges (partition pruning)
-- - Parallel VACUUM/ANALYZE per partition
-- - Drop old data via partition detach (no expensive DELETE)
-- - Improved index performance (smaller per-partition indexes)
```

### Partitioning Decision Tree

```
Does the table have > 10M rows?
├─ NO  → Skip partitioning; use indexes
├─ YES → Is it time-series data?
    ├─ YES → Partition by DATE (monthly/daily)
    ├─ NO  → Is it hierarchical (org/user)?
        ├─ YES → Partition by LIST (org_id)
        ├─ NO  → No partitioning; use aggressive pruning
```

**For this project:**
- `recognition_requests`: Partition by `created_at` (RANGE) if >100M rows
- `quality_metrics`: Time-series; good candidate for monthly partitions
- `audit_logs`: Append-only; excellent for monthly partitioning + archival

---

## Schema Versioning

### Migration Tracking

All schema changes tracked via Alembic migrations (see `/apps/api/migrations/`).

### Rollback Strategy

```bash
# Forward migration
alembic upgrade head

# Rollback to previous version
alembic downgrade -1

# List all versions
alembic history --verbose
```

### Schema Evolution Rules

1. **Always add columns as NULLABLE** initially
2. **Backfill data** in a separate migration
3. **Then add NOT NULL constraint** if needed
4. **Never drop columns** without 2-sprint notice
5. **Rename via VIEW** if renaming is critical

Example:

```sql
-- Migration 1: Add nullable column
ALTER TABLE recognition_requests ADD COLUMN plate_region_new VARCHAR(50);

-- Migration 2: Backfill data
UPDATE recognition_requests SET plate_region_new = plate_region;

-- Migration 3: Add constraint + drop old column
ALTER TABLE recognition_requests 
    ALTER COLUMN plate_region_new SET NOT NULL,
    DROP COLUMN plate_region;
ALTER TABLE recognition_requests RENAME COLUMN plate_region_new TO plate_region;
```

---

## Naming Conventions

### Table & Column Naming

| Object | Pattern | Example |
|--------|---------|---------|
| **Tables** | `snake_case`, plural | `recognition_requests`, `audit_logs` |
| **Columns** | `snake_case`, singular | `plate_number`, `confidence_score` |
| **Primary Keys** | `id` | `id UUID PRIMARY KEY` |
| **Foreign Keys** | `{table}_id` | `user_id`, `request_id` |
| **Indexes** | `idx_{table}_{column}` | `idx_recognition_status` |
| **Unique Indexes** | `unq_{table}_{column}` | `unq_users_email` |
| **Check Constraints** | `check_{table}_{rule}` | `check_confidence_valid` |
| **ENUM Types** | `{entity}_status`, `{entity}_role` | `recognition_status`, `user_role` |

### Reserved Words Avoidance

❌ Avoid: `user`, `order`, `group`, `status`, `type`  
✅ Use: `users`, `orders`, `groups`, `status` (is OK as column), `record_type`

---

## Summary

This schema design provides:

✅ **Normalization** - Eliminates data redundancy  
✅ **Performance** - Strategic indexes for common queries  
✅ **Audit Trail** - Full compliance tracking  
✅ **Scalability** - Partitioning-ready for millions of rows  
✅ **Integrity** - ACID guarantees + constraints  
✅ **Maintainability** - Clear naming and structure  

Next steps:
- See [`02-MIGRATION-MANAGEMENT.md`](02-MIGRATION-MANAGEMENT.md) for schema versioning
- See [`03-PERFORMANCE-OPTIMIZATION.md`](03-PERFORMANCE-OPTIMIZATION.md) for tuning
