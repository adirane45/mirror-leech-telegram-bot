#!/bin/bash
# MongoDB Index Creation Script - TIER 2 Database Optimization
# Creates critical indexes for performance optimization

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MONGO_CONTAINER="mltb-mongodb"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📊 TIER 2 Task 2.1 - Creating MongoDB Indexes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if MongoDB container is running
if ! docker ps | grep -q $MONGO_CONTAINER; then
    echo "❌ MongoDB container not running. Starting..."
    docker compose up -d mongodb
    sleep 5
fi

echo "📝 Creating critical indexes..."
echo ""

# Create indexes in background
docker compose exec -T mongodb mongosh << 'EOF'

// Use the default database
db = db.getSiblingDB("mirror_leech")

console.log("🔧 Creating user collection indexes...")
db.users.createIndex({ "user_id": 1 })
db.users.createIndex({ "status": 1 })
db.users.createIndex({ "created_at": -1 })
console.log("  ✅ User indexes created")

console.log("🔧 Creating download collection indexes...")
db.downloads.createIndex({ "user_id": 1, "status": 1 })
db.downloads.createIndex({ "created_at": -1 })
db.downloads.createIndex({ "link_hash": 1 }, { unique: true })
console.log("  ✅ Download indexes created")

console.log("🔧 Creating task collection indexes...")
db.tasks.createIndex({ "user_id": 1, "status": 1 })
db.tasks.createIndex({ "gid": 1 }, { unique: true })
db.tasks.createIndex({ "updated_at": -1 })
console.log("  ✅ Task indexes created")

console.log("")
console.log("📊 Verifying indexes...")

// Display created indexes
db.users.getIndexes().forEach(idx => {
  console.log("  users index: " + JSON.stringify(idx.key))
})

db.downloads.getIndexes().forEach(idx => {
  console.log("  downloads index: " + JSON.stringify(idx.key))
})

db.tasks.getIndexes().forEach(idx => {
  console.log("  tasks index: " + JSON.stringify(idx.key))
})

console.log("")
console.log("✅ All indexes created successfully!")
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ MongoDB Index Creation Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next: Enable Phase 4 optimization components"
echo "  - Query Optimizer (detects N+1 patterns)"
echo "  - Cache Manager (multi-tier caching)"
echo "  - Connection Pool Manager (connection reuse)"
