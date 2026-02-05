"""
Phase 3 Configuration - GraphQL API, Plugin System, Advanced Dashboard
Safe Innovation Path - Phase 3 Enhancement Options

Enhanced by: justadi
Date: February 5, 2026
"""

# ============================================================================
# GRAPHQL API CONFIGURATION
# ============================================================================

# Enable GraphQL API
ENABLE_GRAPHQL_API = False

# GraphQL endpoint
GRAPHQL_ENDPOINT = "/graphql"

# GraphQL schema introspection (disable in production)
GRAPHQL_INTROSPECTION = True

# GraphQL debug mode (disable in production)
GRAPHQL_DEBUG = False

# GraphQL maximum query depth
GRAPHQL_MAX_DEPTH = 10

# GraphQL operation timeout (seconds)
GRAPHQL_TIMEOUT = 30

# ============================================================================
# PLUGIN SYSTEM CONFIGURATION
# ============================================================================

# Enable plugin system
ENABLE_PLUGIN_SYSTEM = False

# Directory where plugins are stored
PLUGINS_DIR = "plugins"

# Auto-load plugins on startup
AUTO_LOAD_PLUGINS = True

# Plugin sandboxing (restrict plugin access)
PLUGIN_SANDBOX = True

# Allowed plugin capabilities
PLUGIN_ALLOWED_CAPABILITIES = [
    "backup",      # Create backups
    "alert",       # Send alerts
    "monitor",     # Monitor system
    "task",        # Create tasks
    "custom",      # Custom functionality
]

# Maximum plugin execution time (seconds)
PLUGIN_TIMEOUT = 300

# Plugin memory limit (MB) - 0 = unlimited
PLUGIN_MEMORY_LIMIT = 0

# ============================================================================
# ADVANCED DASHBOARD CONFIGURATION
# ============================================================================

# Enable advanced monitoring dashboard
ENABLE_ADVANCED_DASHBOARD = False

# Dashboard endpoint
DASHBOARD_ENDPOINT = "/api/v3/dashboard"

# Dashboard refresh interval (seconds)
DASHBOARD_REFRESH = 5

# WebSocket live metrics
ENABLE_LIVE_METRICS = True

# Dashboard authentication required
DASHBOARD_AUTH = False

# Dashboard access token (if auth enabled)
DASHBOARD_TOKEN = None

# Maximum WebSocket connections
MAX_DASHBOARD_CONNECTIONS = 100

# ============================================================================
# PERFORMANCE OPTIMIZATION CONFIGURATION
# ============================================================================

# Enable query optimization
ENABLE_QUERY_OPTIMIZATION = True

# Cache query results
QUERY_CACHE_ENABLED = True

# Query cache TTL (seconds)
QUERY_CACHE_TTL = 300

# Index hot queries for faster execution
INDEX_HOT_QUERIES = True

# Connection pooling
CONNECTION_POOLING = True

# Connection pool size
CONNECTION_POOL_SIZE = 10

# ============================================================================
# ADVANCED MONITORING CONFIGURATION
# ============================================================================

# Enable advanced metrics collection
ENABLE_ADVANCED_METRICS = True

# Metrics collection interval (seconds)
METRICS_INTERVAL = 60

# Metrics retention (days)
METRICS_RETENTION = 7

# Prometheus export interval (seconds)
PROMETHEUS_EXPORT_INTERVAL = 15

# Custom metrics tracking
TRACK_CUSTOM_METRICS = True

# ============================================================================
# PERFORMANCE THRESHOLDS (Phase 3)
# ============================================================================

# GraphQL query complexity thresholds
GRAPHQL_COMPLEXITY_THRESHOLDS = {
    "query_timeout": 30,           # seconds
    "max_query_depth": 10,
    "max_query_fields": 100,
    "mutation_timeout": 60,        # seconds
}

# Plugin execution thresholds
PLUGIN_THRESHOLDS = {
    "execution_timeout": 300,      # seconds
    "memory_limit_mb": 256,
    "cpu_limit_percent": 50,
    "max_concurrent": 5,
}

# Dashboard performance thresholds
DASHBOARD_THRESHOLDS = {
    "metrics_update_interval": 5,  # seconds
    "max_historical_points": 1000,
    "data_compression": True,
}

# ============================================================================
# SECURITY CONFIGURATION (Phase 3)
# ============================================================================

# GraphQL security
GRAPHQL_SECURITY = {
    "allow_introspection": True,
    "rate_limit_queries": True,
    "max_queries_per_minute": 100,
    "block_deeply_nested_queries": True,
    "require_authentication": False,
}

# Plugin security
PLUGIN_SECURITY = {
    "sandboxed_execution": True,
    "restrict_imports": True,
    "allowed_imports": [
        "asyncio",
        "json",
        "datetime",
        "pathlib",
    ],
    "require_signing": False,
    "verify_checksum": True,
}

# Dashboard security
DASHBOARD_SECURITY = {
    "require_https": False,
    "cors_enabled": False,
    "cors_origins": [],
    "rate_limit": True,
    "max_requests_per_second": 10,
}

# ============================================================================
# API VERSIONING
# ============================================================================

# Current API version
API_VERSION = "3.0.0"

# Supported API versions
SUPPORTED_API_VERSIONS = ["1.0", "2.0", "3.0"]

# API v1 endpoint (deprecated)
API_V1_ENDPOINT = "/api/v1"

# API v2 endpoint
API_V2_ENDPOINT = "/api/v2"

# API v3 endpoint (current)
API_V3_ENDPOINT = "/api/v3"

# Deprecation warning for old APIs
WARN_DEPRECATED_APIS = True

# ============================================================================
# MONITORING INTEGRATION
# ============================================================================

# Send metrics to external service
SEND_METRICS_EXTERNALLY = False

# External metrics endpoint
EXTERNAL_METRICS_URL = None

# Metrics batch size
METRICS_BATCH_SIZE = 100

# Metrics batch interval (seconds)
METRICS_BATCH_INTERVAL = 30

# ============================================================================
# CACHE CONFIGURATION
# ============================================================================

# Enable query result caching
CACHE_ENABLED = True

# Cache backend (redis, memory)
CACHE_BACKEND = "redis"

# Cache key prefix
CACHE_KEY_PREFIX = "mltb_cache_"

# Automatic cache invalidation
AUTO_INVALIDATE_CACHE = True

# Cache invalidation rules
CACHE_INVALIDATION_RULES = {
    "alerts": 300,         # 5 minutes
    "backups": 600,        # 10 minutes
    "metrics": 60,         # 1 minute
    "logs": 120,           # 2 minutes
}
