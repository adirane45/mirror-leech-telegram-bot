# Long Function Extraction Guide

## Overview

Long functions (100+ lines) are difficult to understand, test, and maintain. This guide shows techniques to break them into smaller, more focused functions.

**Identified Long Functions**: 33 functions ranging from 100-475 lines

---

## Key Principles

### 1. Extract Until You Drop

Break functions down until each one fits on a single screen (40-50 lines max).

### 2. Function Naming

Use descriptive names that explain **intent**, not implementation:
```python
# ❌ Bad - describes implementation
def process_1(data):
    emails = [user.email for user in data]
    return emails

# ✅ Good - describes intent
def extract_user_emails(users):
    return [user.email for user in users]
```

### 3. One Level of Abstraction

All statements in a function should be at the same level of abstraction:
```python
# ❌ Bad - mixed abstraction levels
async def handle_download(url):
    # Low-level: HTTP client operations
    response = await client.get(url)
    data = await response.json()
    
    # High-level: business logic
    save_download(data)
    notify_user()

# ✅ Good - consistent abstraction
async def handle_download(url):
    # High-level business logic
    file_data = await fetch_file_from_url(url)
    await save_and_notify(file_data)

async def fetch_file_from_url(url):
    # Low-level implementation
    response = await client.get(url)
    return await response.json()
```

---

## Technique 1: Extract Guard Clauses

### Problem
```python
# 50+ lines of nested business logic
async def process_user_request(user_id, request_data):
    if user_id not in cache:
        if request_data:
            if validate(request_data):
                # 40 lines of actual logic
                result = await database.save(request_data)
                # more logic...
            else:
                return error("Invalid data")
        else:
            return error("Empty request")
    else:
        return error("User not found")
```

### Solution: Extract Early Returns
```python
async def process_user_request(user_id, request_data):
    # Validate preconditions first
    if user_id in cache:
        raise UserCacheError(f"User {user_id} not in cache")
    
    if not request_data:
        raise EmptyRequestError("Request data required")
    
    if not validate(request_data):
        raise InvalidDataError("Request validation failed")
    
    # Now the actual business logic is clear
    return await execute_user_request(request_data)

async def execute_user_request(request_data):
    # 40 lines of focused logic
    pass
```

**Benefits**:
- Fails fast with clear errors
- Reduces nesting
- Main logic is now visible
- Easier to test edge cases

---

## Technique 2: Extract Method Objects (Strategy Pattern)

### Problem

Long functions with multiple branches:
```python
# 298-line function handling different settings changes
async def edit_bot_settings(self, message):
    # Parse which setting to change (80 lines)
    setting_type = extract_setting_type(message)
    
    # Handle 10+ different setting types (200+ lines)
    if setting_type == "bandwidth":
        # 25 lines of bandwidth logic
    elif setting_type == "download_dir":
        # 25 lines of directory logic
    elif setting_type == "api_key":
        # 25 lines of API key logic
    # ... 7 more elif branches
```

### Solution: Strategy Pattern
```python
class SettingStrategy(ABC):
    @abstractmethod
    async def validate(self, value): pass
    
    @abstractmethod
    async def apply(self, user_id, value): pass

class BandwidthLimitStrategy(SettingStrategy):
    async def validate(self, value):
        return 0 < value <= 100  # percentage
    
    async def apply(self, user_id, value):
        await config.set_user_bandwidth(user_id, value)

class DownloadDirectoryStrategy(SettingStrategy):
    async def validate(self, value):
        return os.path.isdir(value)
    
    async def apply(self, user_id, value):
        await config.set_user_download_dir(user_id, value)

# Strategies registry
SETTING_STRATEGIES = {
    "bandwidth": BandwidthLimitStrategy(),
    "download_dir": DownloadDirectoryStrategy(),
    "api_key": ApiKeyStrategy(),
    # ... more strategies
}

# Now the main function is simple
async def edit_bot_settings(self, message):
    setting_type = await self._parse_setting_type(message)
    new_value = await self._extract_setting_value(message)
    
    strategy = SETTING_STRATEGIES[setting_type]
    
    if not await strategy.validate(new_value):
        return await self._send_error(message, "Invalid setting value")
    
    await strategy.apply(message.from_user.id, new_value)
    return await self._send_success(message, setting_type)
```

---

## Technique 3: Extract Data Structures (Parameter Objects)

### Problem
```python
# 150-line function with 12+ parameters and complex logic
async def create_download(self, user_id, url, filename, category,
                         quality, format, auth_token, proxy_url,
                         notification_email, retry_count, timeout,
                         headers_dict):
    # Pass all 12 parameters to various helper functions
    validate_url(url, auth_token, headers_dict)
    prepare_destination(filename, category)
    configure_quality(quality, format)
    # ...
```

### Solution: Create Parameter Object
```python
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class DownloadRequest:
    user_id: int
    url: str
    filename: str
    category: str
    quality: str
    format: str
    auth_token: str
    proxy_url: Optional[str] = None
    notification_email: Optional[str] = None
    retry_count: int = 3
    timeout: int = 300
    headers: Dict[str, str] = None

async def create_download(self, request: DownloadRequest):
    # Much cleaner signature
    if not self._validate_request(request):
        raise InvalidDownloadRequest()
    
    await self._prepare_download(request)
    return await downloader.start(request)
```

**Benefits**:
- Fewer parameters passed around
- Easier to add new options
- Request validation in one place
- Can serialize/deserialize for logging

---

## Technique 4: Extract Complex Conditions

### Problem
```python
# Complex boolean logic buried in function
async def should_process_file(file):
    if (file.size > 1024*1024 and 
        (file.extension in SUPPORTED_FORMATS or file.is_archive) and
        not any(blocked in file.name for blocked in BLOCKED_KEYWORDS) and
        (file.created_date > datetime.now() - timedelta(days=30) or 
         file.owner_id in TRUSTED_USERS)):
        return True
    return False
```

### Solution: Extract to Boolean Methods
```python
async def should_process_file(file):
    return (
        self._is_file_large_enough(file) and
        self._is_supported_format(file) and
        self._is_not_blocked(file) and
        self._is_recent_or_trusted(file)
    )

def _is_file_large_enough(self, file):
    return file.size > 1024 * 1024

def _is_supported_format(self, file):
    return file.extension in SUPPORTED_FORMATS or file.is_archive

def _is_not_blocked(self, file):
    return not any(word in file.name for word in BLOCKED_KEYWORDS)

def _is_recent_or_trusted(self, file):
    is_recent = file.created_date > datetime.now() - timedelta(days=30)
    is_trusted = file.owner_id in TRUSTED_USERS
    return is_recent or is_trusted
```

---

## Technique 5: Extract Loops into Functional Methods

### Problem
```python
# Imperative loop with mixed concerns
def process_downloads(downloads):
    results = []
    for download in downloads:
        # Filtering logic mixed with processing
        if download.status == "pending":
            try:
                # Processing logic
                file_data = download.get_file_data()
                processed = file_data.upper()
                metadata = extract_metadata(processed)
                # Result building
                results.append({
                    "id": download.id,
                    "processed": processed,
                    "metadata": metadata
                })
            except Exception as e:
                logger.error(f"Failed: {e}")
    return results
```

### Solution: Functional Approach  
```python
def process_downloads(downloads):
    return (
        downloads
        .filter(lambda d: d.status == "pending")
        .map(lambda d: process_single_download(d))
        .filter(lambda r: r is not None)
    )

def process_single_download(download):
    try:
        file_data = download.get_file_data()
        processed = file_data.upper()
        metadata = extract_metadata(processed)
        return {
            "id": download.id,
            "processed": processed,
            "metadata": metadata
        }
    except Exception as e:
        logger.error(f"Failed processing {download.id}: {e}")
        return None
```

Or using Python's built-in functions:
```python
def process_downloads(downloads):
    pending = filter(lambda d: d.status == "pending", downloads)
    processed = map(process_single_download, pending)
    return list(filter(None, processed))
```

---

## Technique 6: Extract Related Code into Classes

### Problem

Long procedural function that operates on related data:
```python
# 180-line function handling dashboard rendering
async def dashboard(self, message):
    # Fetch data (30 lines)
    user = await db.get_user(message.user_id)
    stats = await get_user_stats(user.id)
    downloads = await get_user_downloads(user.id)
    uploads = await get_user_uploads(user.id)
    
    # Format data (80 lines)
    total_size = sum(d.size for d in downloads)
    completion = (sum(d.progress for d in downloads) / len(downloads)) * 100
    # ... more formatting
    
    # Generate HTML (60 lines)
    html = "<html>..."
    for download in downloads:
        html += f"<tr>{download.name}...</tr>"
    # ... more HTML generation
    
    return html
```

### Solution: Extract to Dashboard Class
```python
class DashboardRenderer:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.data = None
        self.formatted = None
    
    async def render(self) -> str:
        await self._fetch_data()
        self._format_data()
        return self._generate_html()
    
    async def _fetch_data(self):
        self.data = {
            "user": await db.get_user(self.user_id),
            "stats": await get_user_stats(self.user_id),
            "downloads": await get_user_downloads(self.user_id),
            "uploads": await get_user_uploads(self.user_id)
        }
    
    def _format_data(self):
        self.formatted = {
            "total_size": sum(d.size for d in self.data["downloads"]),
            "completion": self._calculate_completion(),
            # ... more formatting
        }
    
    def _generate_html(self) -> str:
        builder = HtmlBuilder()
        builder.add_header("User Dashboard")
        builder.add_user_info(self.data["user"])
        builder.add_stats_section(self.formatted)
        return builder.build()

# Usage
async def dashboard(self, message):
    renderer = DashboardRenderer(message.user_id)
    return await renderer.render()
```

---

## Refactoring Checklist for Each Long Function

- [ ] **Understand**: Map function logic and identify sections
- [ ] **Test**: Write tests for current behavior  
- [ ] **Identify Extractions**: Find logical sections to extract
- [ ] **Extract 1**: Extract first method, test
- [ ] **Extract 2**: Extract second method, test
- [ ] **Repeat**: Continue until function is reasonable length  
- [ ] **Integrate**: Update callers to use new functions
- [ ] **Verify**: Re-run full test suite
- [ ] **Document**: Update function/class docstrings
- [ ] **Review**: Code review with team

---

## Tools & Commands

```bash
# List functions by line count
python3 scripts/analyze_complexity.py | grep "Long function"

# Check specific file for long functions
python3 -c "
import ast
import sys

with open(sys.argv[1]) as f:
    tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            lines = node.end_lineno - node.lineno
            if lines > 100:
                print(f'{node.name}: {lines} lines')
" bot/modules/mirror_leech.py

# Run tests after refactoring
pytest tests/ -v

# Check coverage of refactored code
pytest tests/ --cov=bot/modules --cov-report=term-missing
```

---

## Before/After Example: `edit_bot_settings()`

### BEFORE (298 lines)
```python
async def edit_bot_settings(self, message):
    # 298 lines of mixed concerns:
    # - Parse message
    # - Route to handler
    # - Validate input
    # - Update database
    # - Send response
    # All in one function!
```

### AFTER (40 lines)
```python
async def edit_bot_settings(self, message):
    """Edit a single bot setting"""
    try:
        setting = await self._parse_setting(message)
        await self._validate_and_apply(setting)
        await self._send_confirmation(message, setting)
    except SettingError as e:
        await self._send_error(message, e)

async def _parse_setting(self, message):
    """Extract setting and value from message"""
    pass

async def _validate_and_apply(self, setting):
    """Validate and update database"""
    pass

async def _send_confirmation(self, message, setting):
    """Send success response"""
    pass
```

---

## Expected Timeline & Effort

| Number | Type | Expected Effort |
|--------|------|-----------------|
| 33 | Long functions | ~66 hours (2 hours each) |
| | | ~4 weeks (full-time) |
| | | ~8 weeks (part-time) |

**Priority Order**:
1. Most-changed files (hotspots) first
2. Test coverage weak areas
3. Complex business logic
4. Utility functions last
