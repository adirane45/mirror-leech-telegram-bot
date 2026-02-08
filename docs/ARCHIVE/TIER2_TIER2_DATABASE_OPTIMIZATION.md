# Database Query Optimization Guide
**Mirror Leech Telegram Bot - Database Optimization**

## Overview
This guide focuses on optimizing database query performance based on CodeScene analysis and Phase 4 learnings.

---

## 1. Query Optimization Principles

### Use Query Optimizer (implemented in Phase 4)
```python
from bot.core.query_optimizer import QueryOptimizer

optimizer = QueryOptimizer.get_instance()
await optimizer.enable()

# Analyze queries before execution
result = await optimizer.analyze_query("SELECT * FROM users WHERE status='active'")
print(result.recommendations)
# Output: ["Consider caching SELECT query results", "Consider index on WHERE clause columns"]
```

### N+1 Query Detection
The Query Optimizer detects N+1 patterns:

**❌ Bad - N+1 queries:**
```python
users = await db.find("users", {"status": "active"})
for user in users:
    downloads = await db.find("downloads", {"user_id": user["_id"]})  # N queries!
    user["downloads"] = downloads
```

**✅ Good - Single batch query:**
```python
users = await db.find("users", {"status": "active"})
user_ids = [u["_id"] for u in users]

# Single query for all downloads
downloads = await db.find("downloads", {"user_id": {"$in": user_ids}})

# Map downloads to users
for user in users:
    user["downloads"] = [d for d in downloads if d["user_id"] == user["_id"]]
```

---

## 2. Index Strategy

### Critical Indexes
Based on CodeScene hotspot analysis, create these indexes:

**MongoDB**:
```javascript
// User lookups
db.users.createIndex({ "user_id": 1 })
db.users.createIndex({ "status": 1 })
db.users.createIndex({ "created_at": -1 })

// Download tracking
db.downloads.createIndex({ "user_id": 1, "status": 1 })
db.downloads.createIndex({ "created_at": -1 })
db.downloads.createIndex({ "link_hash": 1 }, { unique: true })

// Task queries
db.tasks.createIndex({ "user_id": 1, "status": 1 })
db.tasks.createIndex({ "gid": 1 }, { unique: true })
db.tasks.createIndex({ "updated_at": -1 })
```

**Redis**:
```bash
# Cache frequently accessed data
# Query optimizer will suggest caching opportunities
```

### Composite Indexes
For queries with multiple WHERE conditions:

```javascript
// Composite index for common query pattern
db.downloads.createIndex({ 
    "user_id": 1,      // Equality filter
    "status": 1,       // Equality filter
    "created_at": -1   // Sort column
})
```

---

## 3. Query Patterns - Best Practices

### Projection (Only select needed fields)
**❌ Slow:**
```python
user = await db.find_one("users", {"_id": user_id})
# Returns all 50 fields, only need name and status
```

**✅ Fast:**
```python
user = await db.find_one(
    "users", 
    {"_id": user_id},
    projection={"name": 1, "status": 1}  # Only 2 fields
)
```

### Batch Operations
**❌ Slow - Multiple round trips:**
```python
for user_id in user_ids:
    await db.update_one("users", {"_id": user_id}, {"active": True})
```

**✅ Fast - Single batch operation:**
```python
await db.update_many(
    "users",
    {"_id": {"$in": user_ids}},
    {"$set": {"active": True}}
)
```

### Connection Pooling (Phase 4)
Use the Connection Pool Manager automatically:

```python
from bot.core.connection_pool_manager import ConnectionPoolManager

pool_mgr = ConnectionPoolManager.get_instance()
await pool_mgr.enable()

# Connections are reused from pool - much faster
conn = await pool_mgr.acquire_connection("mongodb")
```

---

## 4. Caching Strategy

### Cache Manager (Phase 4)
```python
from bot.core.cache_manager import CacheManager

cache = CacheManager.get_instance()
await cache.enable(max_size_mb=200)

# Cache expensive queries
user = await cache.get("user:123")
if not user:
    # Query database
    user = await db.find_one("users", {"_id": ObjectId("123")})
    # Cache for 5 minutes
    await cache.set("user:123", user, ttl=300)
```

### Cache Invalidation Patterns
```python
# When user is updated, invalidate related caches
await cache.invalidate_pattern("user:123:*")  # All patterns for user
await cache.invalidate_pattern("downloads:user:123:*")
```

---

## 5. Query Analysis - CodeScene Findings

### Files Needing Query Review
Based on CodeScene analysis, these files have high query complexity:

1. **`bot/helper/common.py`** (1116 complexity)
   - Check for N+1 patterns in download processing
   - Consider query caching for status lookups
   - Batch user updates

2. **`bot/modules/mirror_leech.py`** (365 complexity)
   - Mirror downloads may have multiple status queries
   - Use connection pooling for bulk operations
   - Cache mirror metadata

3. **`bot/modules/ytdlp.py`** (422 complexity)
   - YT-DLP operations may query download records
   - Batch task creation with bulk insert

### Optimization Checklist
- [ ] Profile slow queries with Query Optimizer
- [ ] Add missing indexes (see MongoDB section above)
- [ ] Replace N+1 patterns with batch queries
- [ ] Enable connection pooling (Phase 4)
- [ ] Enable caching for SELECT queries (Phase 4)
- [ ] Use projection to reduce data transfer
- [ ] Batch similar operations together

---

## 6. Monitoring Query Performance

### Enable Query Logging
```python
import logging
logging.getLogger('pymongo').setLevel(logging.DEBUG)
logging.getLogger('redis').setLevel(logging.DEBUG)
```

### Track Query Metrics
```python
from bot.core.metrics import metrics

# Metrics are automatically collected
slow_queries = metrics.get_slow_queries(threshold_ms=1000)
for query in slow_queries:
    print(f"⚠️  Slow: {query['query']} ({query['duration_ms']}ms)")
```

### Prometheus Metrics
Monitor these key metrics:

```
mltb_query_duration_seconds{query_type="SELECT"}
mltb_query_optimizer_n_plus_one_detected_total
mltb_cache_hit_rate{operation="database_query"}
mltb_connection_pool_wait_time_seconds
```

---

## 7. Performance Targets

### Query Performance Goals
| Metric | Baseline | Target | Status |
|--------|----------|--------|--------|
| Avg SELECT time | TBD | <50ms | 📊 Measure |
| INSERT batch time | TBD | <200ms | 📊 Measure |
| Cache hit rate | TBD | >70% | 📊 Measure |
| Connection pool wait | TBD | <10ms | 📊 Measure |
| N+1 queries detected | 0 | 0 | ✅ Prevent |

---

## 8. Troubleshooting Guide

### Symptom: Slow Download Processing
**Check:**
1. Run Query Optimizer: `await optimizer.analyze_query(...)`
2. Check MongoDB indexes: `db.downloads.getIndexes()`
3. Look for N+1 patterns in download loops
4. Verify connection pool utilization

**Fix:**
- Add missing indexes
- Batch download status updates
- Use connection pooling

### Symptom: High Cache Evictions
**Check:**
1. Cache statistics: `cache.statistics.l1_evictions`
2. Cache hit rate: `cache.statistics.hit_rate`

**Fix:**
- Increase L1 cache size: `await cache.enable(max_size_mb=500)`
- Review cached data freshness
- Implement cache warming

### Symptom: Pool Exhaustion Warnings
**Check:**
1. Connection pool utilization: `pool.statistics.utilization_percent`
2. Active connections: `pool.statistics.active_connections`

**Fix:**
- Increase pool max size
- Check for connection leaks (not releasing)
- Profile for long-running transactions

---

## 9. Implementation Checklist

### Phase 1: Measurement (This Session)
- [x] Run performance baseline
- [x] Document current query patterns
- [x] Identify slow queries

### Phase 2: Optimization (Next Session)
- [ ] Create recommended indexes
- [ ] Fix N+1 patterns
- [ ] Enable query caching
- [ ] Verify improvements with benchmarks

### Phase 3: Monitoring (Ongoing)
- [ ] Set up Prometheus metrics
- [ ] Create Grafana dashboards
- [ ] Define alert thresholds

---

## 10. Resources

- **Phase 4 Query Optimizer:** `bot/core/query_optimizer.py`
- **Phase 4 Cache Manager:** `bot/core/cache_manager.py`
- **Phase 4 Connection Pool:** `bot/core/connection_pool_manager.py`
- **Performance Monitor:** `scripts/measure_performance_baseline.py`
- **CodeScene Report:** `CODESCENE_ANALYSIS_REPORT.md`

---

*Last updated: February 6, 2026*  
*Tier 2.2 - Database Query Optimization*
