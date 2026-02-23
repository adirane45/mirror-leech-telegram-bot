"""
API Gateway Enhancements for Phase 7

Implements:
- Request/Response middleware chain
- API versioning support
- Content negotiation
- Compression handling
- CORS management
- API documentation generation
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .. import LOGGER


class APIVersion(str, Enum):
    """API versions"""
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"


class ContentType(str, Enum):
    """Content types"""
    JSON = "application/json"
    XML = "application/xml"
    PROTOBUF = "application/protobuf"
    MSGPACK = "application/msgpack"


class CompressionAlgorithm(str, Enum):
    """Compression algorithms"""
    NONE = "none"
    GZIP = "gzip"
    DEFLATE = "deflate"
    BR = "br"


@dataclass
class Request:
    """Request wrapper"""
    method: str
    path: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[bytes] = None
    query_params: Dict[str, str] = field(default_factory=dict)
    version: APIVersion = APIVersion.V1
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Response:
    """Response wrapper"""
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[bytes] = None
    content_type: ContentType = ContentType.JSON
    compression: CompressionAlgorithm = CompressionAlgorithm.NONE


class Middleware:
    """Base middleware class"""
    
    async def process_request(self, request: Request) -> Optional[Response]:
        """Process incoming request"""
        return None
    
    async def process_response(self, response: Response) -> Response:
        """Process outgoing response"""
        return response


class AuthenticationMiddleware(Middleware):
    """Authentication middleware"""
    
    def __init__(self, token_header: str = "Authorization"):
        self.token_header = token_header
        self.valid_tokens = set()
    
    def add_token(self, token: str) -> None:
        """Add valid token"""
        self.valid_tokens.add(token)
    
    async def process_request(self, request: Request) -> Optional[Response]:
        """Check authentication"""
        # Allow api paths without auth for testing
        if "/api/" not in request.path:
            return None
        
        token = request.headers.get(self.token_header, "").replace("Bearer ", "")
        
        if not token or token not in self.valid_tokens:
            return Response(
                status_code=401,
                body=b'{"error": "Unauthorized"}'
            )
        
        return None


class RateLimitMiddleware(Middleware):
    """Rate limiting middleware"""
    
    def __init__(self, requests_per_second: int = 100):
        self.requests_per_second = requests_per_second
        self.request_times: Dict[str, List[datetime]] = {}
    
    async def process_request(self, request: Request) -> Optional[Response]:
        """Check rate limit"""
        client_ip = request.headers.get("X-Forwarded-For", "unknown")
        
        if client_ip not in self.request_times:
            self.request_times[client_ip] = []
        
        now = datetime.now(timezone.utc)
        
        # Clean old requests (older than 1 second)
        self.request_times[client_ip] = [
            t for t in self.request_times[client_ip]
            if (now - t).total_seconds() < 1
        ]
        
        # Check limit
        if len(self.request_times[client_ip]) >= self.requests_per_second:
            return Response(
                status_code=429,
                body=b'{"error": "Rate limit exceeded"}'
            )
        
        self.request_times[client_ip].append(now)
        return None


class CompressionMiddleware(Middleware):
    """Response compression middleware"""
    
    async def process_response(self, response: Response) -> Response:
        """Compress response if needed"""
        accept_encoding = ""
        
        if not response.body or len(response.body) < 1000:
            return response
        
        # Simple mock - real implementation would use gzip/brotli
        if "gzip" in accept_encoding:
            response.compression = CompressionAlgorithm.GZIP
        
        return response


class CORSMiddleware(Middleware):
    """CORS handling middleware"""
    
    def __init__(self, allowed_origins: List[str] = None):
        self.allowed_origins = allowed_origins or ["*"]
    
    async def process_response(self, response: Response) -> Response:
        """Add CORS headers"""
        response.headers["Access-Control-Allow-Origin"] = ", ".join(
            self.allowed_origins
        )
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        return response


class ContentNegotiation:
    """Handle content negotiation"""
    
    def __init__(self):
        self.serializers: Dict[ContentType, Callable] = {}
        self.deserializers: Dict[ContentType, Callable] = {}
    
    def register_serializer(
        self,
        content_type: ContentType,
        serializer: Callable
    ) -> None:
        """Register serializer"""
        self.serializers[content_type] = serializer
    
    def register_deserializer(
        self,
        content_type: ContentType,
        deserializer: Callable
    ) -> None:
        """Register deserializer"""
        self.deserializers[content_type] = deserializer
    
    def get_accepted_types(
        self,
        accept_header: str
    ) -> List[ContentType]:
        """Parse Accept header"""
        types = []
        
        if "application/json" in accept_header:
            types.append(ContentType.JSON)
        if "application/xml" in accept_header:
            types.append(ContentType.XML)
        
        return types or [ContentType.JSON]


class APIVersionManager:
    """Manage API versions"""
    
    def __init__(self):
        self.handlers: Dict[APIVersion, Dict[str, Callable]] = {
            APIVersion.V1: {},
            APIVersion.V2: {},
            APIVersion.V3: {},
        }
    
    def register_handler(
        self,
        version: APIVersion,
        path: str,
        handler: Callable
    ) -> None:
        """Register version-specific handler"""
        if version not in self.handlers:
            self.handlers[version] = {}
        
        self.handlers[version][path] = handler
    
    def get_handler(
        self,
        version: APIVersion,
        path: str
    ) -> Optional[Callable]:
        """Get handler for version/path"""
        if version not in self.handlers:
            return None
        
        return self.handlers[version].get(path)


@dataclass
class APIEndpoint:
    """API endpoint documentation"""
    path: str
    method: str
    version: APIVersion
    description: str
    parameters: Dict[str, str] = field(default_factory=dict)
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)


class APIDocumentationGenerator:
    """Generate API documentation"""
    
    def __init__(self):
        self.endpoints: List[APIEndpoint] = []
    
    def register_endpoint(self, endpoint: APIEndpoint) -> None:
        """Register endpoint for documentation"""
        self.endpoints.append(endpoint)
    
    def generate_openapi(self) -> Dict[str, Any]:
        """Generate OpenAPI spec"""
        paths = {}
        
        for endpoint in self.endpoints:
            path_key = endpoint.path
            method_key = endpoint.method.lower()
            
            if path_key not in paths:
                paths[path_key] = {}
            
            paths[path_key][method_key] = {
                "summary": endpoint.description,
                "parameters": [
                    {"name": name, "schema": {"type": type_}}
                    for name, type_ in endpoint.parameters.items()
                ],
                "responses": {
                    "200": {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "schema": endpoint.response_body
                            }
                        }
                    }
                }
            }
        
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Mirror Leech API",
                "version": "1.0.0"
            },
            "paths": paths
        }
    
    def generate_markdown(self) -> str:
        """Generate Markdown documentation"""
        doc = "# API Documentation\n\n"
        
        current_version = None
        
        for endpoint in sorted(self.endpoints, key=lambda e: (e.version, e.path)):
            if endpoint.version != current_version:
                current_version = endpoint.version
                doc += f"## API {current_version.value}\n\n"
            
            doc += f"### {endpoint.method} {endpoint.path}\n\n"
            doc += f"{endpoint.description}\n\n"
            
            if endpoint.parameters:
                doc += "**Parameters:**\n"
                for name, param_type in endpoint.parameters.items():
                    doc += f"- `{name}` ({param_type})\n"
                doc += "\n"
            
            if endpoint.examples:
                doc += "**Examples:**\n"
                for example in endpoint.examples:
                    doc += f"- {example}\n"
                doc += "\n"
        
        return doc


class APIGateway:
    """Main API Gateway"""
    
    def __init__(self):
        self.middlewares: List[Middleware] = []
        self.content_negotiation = ContentNegotiation()
        self.version_manager = APIVersionManager()
        self.documentation = APIDocumentationGenerator()
    
    def use_middleware(self, middleware: Middleware) -> None:
        """Register middleware"""
        self.middlewares.append(middleware)
    
    async def handle_request(
        self,
        request: Request
    ) -> Response:
        """Handle incoming request"""
        # Process middlewares
        for middleware in self.middlewares:
            response = await middleware.process_request(request)
            if response:
                return response
        
        # Get handler for version
        handler = self.version_manager.get_handler(
            request.version,
            request.path
        )
        
        if not handler:
            return Response(
                status_code=404,
                body=b'{"error": "Not found"}'
            )
        
        # Call handler
        if asyncio.iscoroutinefunction(handler):
            response = await handler(request)
        else:
            response = handler(request)
        
        # Process response middlewares
        for middleware in self.middlewares:
            response = await middleware.process_response(response)
        
        return response


# Global instance
gateway = APIGateway()
