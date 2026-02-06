# API Documentation

Complete API reference for Enhanced MLTB v3.1.0

---

## Table of Contents

- [GraphQL API](#graphql-api)
- [REST Endpoints](#rest-endpoints)
- [WebSocket API](#websocket-api)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

---

## GraphQL API

### Overview

The GraphQL API provides a powerful, flexible interface to query and manipulate bot data.

**Base URL:** `http://localhost:8060/graphql`

**GraphQL Playground:** Available at GET `/graphql` (interactive UI)

### Authentication

Currently no authentication required for local access. For production, implement token-based auth:

```http
POST /graphql
Authorization: Bearer your_token_here
Content-Type: application/json
```

---

## GraphQL Schema

### Queries

#### System Status

```graphql
query {
  status {
    version
    uptime
    activeTasks
    totalDownloads
    totalUploads
    memoryUsage
    cpuUsage
    timestamp
  }
}
```

**Response:**
```json
{
  "data": {
    "status": {
      "version": "3.1.0",
      "uptime": "5 days, 3 hours",
      "activeTasks": 2,
      "totalDownloads": 150,
      "totalUploads": 145,
      "memoryUsage": "45%",
      "cpuUsage": "23%",
      "timestamp": "2026-02-06T10:30:00"
    }
  }
}
```

#### Logger Statistics

```graphql
query {
  loggerStats {
    totalLogs
    errorCount
    warningCount
    infoCount
    criticalCount
    recentErrors
    logFileSize
  }
}
```

**Response:**
```json
{
  "data": {
    "loggerStats": {
      "totalLogs": 15234,
      "errorCount": 45,
      "warningCount": 123,
      "infoCount": 14998,
      "criticalCount": 2,
      "recentErrors": [
        "Connection timeout at 10:25:00",
        "Failed to upload file at 09:15:30"
      ],
      "logFileSize": "12.5 MB"
    }
  }
}
```

#### Alert Summary

```graphql
query {
  alertSummary {
    totalAlerts
    criticalAlerts
    warningAlerts
    infoAlerts
    recentAlerts {
      level
      message
      timestamp
    }
    subscribers
  }
}
```

#### Backup List

```graphql
query {
  backups {
    filename
    size
    timestamp
    description
    status
  }
}
```

**Response:**
```json
{
  "data": {
    "backups": [
      {
        "filename": "backup_20260206_023000.tar.gz",
        "size": "45.2 MB",
        "timestamp": "2026-02-06T02:30:00",
        "description": "Automated daily backup",
        "status": "completed"
      },
      {
        "filename": "backup_20260205_023000.tar.gz",
        "size": "42.8 MB",
        "timestamp": "2026-02-05T02:30:00",
        "description": "Automated daily backup",
        "status": "completed"
      }
    ]
  }
}
```

#### Plugin List

```graphql
query {
  plugins {
    name
    version
    enabled
    description
    author
    hooks
  }
}
```

#### Task Status

```graphql
query {
  taskStatus(taskId: "task_123456") {
    id
    type
    status
    progress
    speed
    eta
    size
    filename
    startTime
  }
}
```

#### Download Statistics

```graphql
query {
  downloadStats {
    todayDownloads
    todayUploads
    totalBandwidth
    averageSpeed
    topDownloaders {
      userId
      username
      downloadCount
      totalSize
    }
  }
}
```

---

### Mutations

#### Create Backup

```graphql
mutation {
  createBackup(
    description: "Manual backup before update"
    backupName: "pre_update_backup"
  ) {
    success
    message
    filename
  }
}
```

**Response:**
```json
{
  "data": {
    "createBackup": {
      "success": true,
      "message": "Backup created successfully",
      "filename": "pre_update_backup_20260206_103000.tar.gz"
    }
  }
}
```

#### Trigger Alert

```graphql
mutation {
  triggerAlert(
    level: "warning"
    message: "High memory usage detected"
  ) {
    success
    message
  }
}
```

#### Enable/Disable Plugin

```graphql
mutation {
  togglePlugin(pluginName: "custom_notifier", enabled: true) {
    success
    message
  }
}
```

#### Clear Cache

```graphql
mutation {
  clearCache {
    success
    message
    clearedItems
  }
}
```

#### Restart Service

```graphql
mutation {
  restartService(service: "celery_worker") {
    success
    message
  }
}
```

---

### Subscriptions

#### Task Progress Updates

```graphql
subscription {
  taskProgress(taskId: "task_123456") {
    taskId
    progress
    speed
    eta
    status
  }
}
```

#### System Metrics Stream

```graphql
subscription {
  systemMetrics {
    timestamp
    cpuUsage
    memoryUsage
    diskUsage
    networkIn
    networkOut
  }
}
```

---

## REST Endpoints

### Dashboard Endpoints

#### GET `/`
Homepage - serves the web dashboard

**Response:** HTML dashboard interface

#### GET `/health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "version": "3.1.0",
  "timestamp": "2026-02-06T10:30:00Z"
}
```

#### GET `/metrics`
Prometheus metrics endpoint

**Response:** Prometheus-formatted metrics
```
# HELP bot_downloads_total Total number of downloads
# TYPE bot_downloads_total counter
bot_downloads_total 150

# HELP bot_active_tasks Number of active tasks
# TYPE bot_active_tasks gauge
bot_active_tasks 2
```

---

### Statistics Endpoints

#### GET `/api/stats`
Get bot statistics

**Response:**
```json
{
  "version": "3.1.0",
  "uptime": "5d 3h 25m",
  "activeTasks": 2,
  "totalDownloads": 150,
  "totalUploads": 145,
  "totalUsers": 25,
  "diskUsage": "45%",
  "memoryUsage": "52%"
}
```

#### GET `/api/tasks`
List all tasks

**Query Parameters:**
- `status` - Filter by status (active, completed, failed)
- `limit` - Maximum results (default: 50)
- `offset` - Pagination offset

**Response:**
```json
{
  "tasks": [
    {
      "id": "task_123456",
      "type": "download",
      "status": "active",
      "progress": 45.5,
      "filename": "movie.mkv",
      "size": "2.5 GB",
      "speed": "5.2 MB/s",
      "eta": "8m 30s"
    }
  ],
  "total": 150,
  "page": 1
}
```

#### GET `/api/tasks/:taskId`
Get specific task details

**Response:**
```json
{
  "id": "task_123456",
  "type": "download",
  "url": "https://example.com/file.zip",
  "status": "active",
  "progress": 45.5,
  "filename": "file.zip",
  "size": "1.2 GB",
  "downloaded": "550 MB",
  "speed": "3.5 MB/s",
  "eta": "3m 15s",
  "startTime": "2026-02-06T10:15:00Z",
  "user": {
    "id": 123456789,
    "username": "user123"
  }
}
```

---

### Download Endpoints

#### POST `/api/download`
Start a new download

**Request:**
```json
{
  "url": "https://example.com/file.zip",
  "userId": 123456789,
  "destination": "gdrive",
  "folderId": "abc123xyz"
}
```

**Response:**
```json
{
  "success": true,
  "taskId": "task_789012",
  "message": "Download started successfully"
}
```

#### DELETE `/api/tasks/:taskId`
Cancel a task

**Response:**
```json
{
  "success": true,
  "message": "Task cancelled successfully"
}
```

---

### User Endpoints

#### GET `/api/users`
List authorized users

**Response:**
```json
{
  "users": [
    {
      "id": 123456789,
      "username": "user123",
      "totalDownloads": 45,
      "totalUploads": 43,
      "lastActive": "2026-02-06T10:20:00Z"
    }
  ]
}
```

#### GET `/api/users/:userId/stats`
Get user statistics

**Response:**
```json
{
  "userId": 123456789,
  "username": "user123",
  "downloads": {
    "total": 45,
    "successful": 43,
    "failed": 2
  },
  "totalSize": "125.5 GB",
  "joinedDate": "2026-01-01T00:00:00Z",
  "lastActive": "2026-02-06T10:20:00Z"
}
```

---

### Configuration Endpoints

#### GET `/api/config`
Get current configuration (sensitive fields hidden)

**Response:**
```json
{
  "downloadDir": "/app/downloads",
  "maxConcurrentDownloads": 5,
  "maxSplitSize": "2 GB",
  "enabledPhases": {
    "phase1": true,
    "phase2": true,
    "phase3": true
  },
  "features": {
    "graphqlApi": true,
    "pluginSystem": true,
    "advancedDashboard": true
  }
}
```

#### PATCH `/api/config`
Update configuration (requires authentication)

**Request:**
```json
{
  "maxConcurrentDownloads": 10,
  "autoDeleteDuration": 120
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration updated",
  "updated": ["maxConcurrentDownloads", "autoDeleteDuration"]
}
```

---

### Plugin Endpoints

#### GET `/api/plugins`
List all plugins

**Response:**
```json
{
  "plugins": [
    {
      "name": "custom_notifier",
      "version": "1.0.0",
      "enabled": true,
      "description": "Custom notification plugin",
      "author": "Developer"
    }
  ]
}
```

#### POST `/api/plugins/:name/toggle`
Enable/disable a plugin

**Request:**
```json
{
  "enabled": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Plugin enabled successfully"
}
```

---

## WebSocket API

### Connection

**Endpoint:** `ws://localhost:8060/ws`

### Events

#### Subscribe to Task Updates

**Send:**
```json
{
  "type": "subscribe",
  "channel": "task_updates",
  "taskId": "task_123456"
}
```

**Receive:**
```json
{
  "type": "task_update",
  "taskId": "task_123456",
  "data": {
    "progress": 50.5,
    "speed": "4.2 MB/s",
    "eta": "5m 30s"
  }
}
```

#### Subscribe to System Metrics

**Send:**
```json
{
  "type": "subscribe",
  "channel": "system_metrics"
}
```

**Receive:**
```json
{
  "type": "metrics",
  "data": {
    "timestamp": "2026-02-06T10:30:00Z",
    "cpuUsage": 23.5,
    "memoryUsage": 52.1,
    "activeTasks": 2
  }
}
```

---

## Authentication

### Token-Based Authentication

For production deployments, implement token-based auth:

**Request Header:**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Generate Token

```bash
# Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add to `.env.production`:
```bash
API_TOKEN=your_generated_token_here
```

---

## Rate Limiting

### Default Limits

- GraphQL: 100 requests/minute
- REST API: 60 requests/minute
- WebSocket: 1000 messages/minute

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1612345678
```

### Rate Limit Exceeded Response

```json
{
  "error": "Rate limit exceeded",
  "retryAfter": 45
}
```

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Invalid task ID provided",
    "details": {
      "field": "taskId",
      "value": "invalid_id"
    }
  }
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INVALID_INPUT` | Invalid request parameters | 400 |
| `UNAUTHORIZED` | Authentication required | 401 |
| `FORBIDDEN` | Insufficient permissions | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `RATE_LIMITED` | Rate limit exceeded | 429 |
| `INTERNAL_ERROR` | Server error | 500 |

---

## Examples

### cURL Examples

#### GraphQL Query
```bash
curl -X POST http://localhost:8060/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ status { version uptime activeTasks } }"}'
```

#### Get Statistics
```bash
curl http://localhost:8060/api/stats
```

#### Start Download
```bash
curl -X POST http://localhost:8060/api/download \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/file.zip",
    "userId": 123456789,
    "destination": "gdrive"
  }'
```

### Python Examples

#### Using requests library

```python
import requests
import json

# GraphQL Query
def get_status():
    query = """
    query {
      status {
        version
        uptime
        activeTasks
      }
    }
    """
    
    response = requests.post(
        "http://localhost:8060/graphql",
        json={"query": query}
    )
    
    return response.json()

# REST API
def start_download(url, user_id):
    data = {
        "url": url,
        "userId": user_id,
        "destination": "gdrive"
    }
    
    response = requests.post(
        "http://localhost:8060/api/download",
        json=data
    )
    
    return response.json()

# Usage
status = get_status()
print(f"Bot version: {status['data']['status']['version']}")

task = start_download("https://example.com/file.zip", 123456789)
print(f"Task ID: {task['taskId']}")
```

### JavaScript Examples

#### Using fetch API

```javascript
// GraphQL Query
async function getStatus() {
  const query = `
    query {
      status {
        version
        uptime
        activeTasks
      }
    }
  `;
  
  const response = await fetch('http://localhost:8060/graphql', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  });
  
  return await response.json();
}

// REST API
async function startDownload(url, userId) {
  const response = await fetch('http://localhost:8060/api/download', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      url,
      userId,
      destination: 'gdrive',
    }),
  });
  
  return await response.json();
}

// Usage
const status = await getStatus();
console.log(`Bot version: ${status.data.status.version}`);

const task = await startDownload('https://example.com/file.zip', 123456789);
console.log(`Task ID: ${task.taskId}`);
```

### WebSocket Example

```javascript
const ws = new WebSocket('ws://localhost:8060/ws');

ws.onopen = () => {
  // Subscribe to task updates
  ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'task_updates',
    taskId: 'task_123456'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Task update:', data);
};
```

---

## API Client Libraries

### Official Clients

Coming soon:
- Python SDK
- JavaScript/Node.js SDK
- Go SDK

### Community Clients

Check the repository for community-contributed clients.

---

## API Versioning

Current API version: **v1**

**Base URLs:**
- v1: `http://localhost:8060/api/v1/`
- GraphQL: `http://localhost:8060/graphql` (versionless)

Future versions will be available at `/api/v2/`, etc.

---

## Next Steps

- [Features Guide](FEATURES.md) - Complete feature reference
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [Configuration Guide](CONFIGURATION.md) - API configuration
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues

---

**API documentation complete! Start building integrations.** 🚀
