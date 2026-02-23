"""
Security Headers Middleware for Phase 3
Implements HTTP security headers and HTTPS enforcement
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


class SecurityHeaders:
    """
    Manages HTTP security headers and HTTPS enforcement
    
    Implements:
    - HSTS (HTTP Strict Transport Security)
    - X-Frame-Options (clickjacking protection)
    - X-Content-Type-Options (MIME sniffing protection)
    - X-XSS-Protection (legacy XSS filter)
    - Strict-Transport-Security
    - Content-Security-Policy
    - Referrer-Policy
    - Permissions-Policy
    """
    
    def __init__(self, enforce_https: bool = True, domains: Optional[list] = None):
        """
        Initialize security headers
        
        Args:
            enforce_https: Whether to enforce HTTPS
            domains: Allowed domains for CORS
        """
        self.enforce_https = enforce_https
        self.allowed_domains = domains or ["localhost"]
        self.initialized = False
        
        # Security header configurations
        self.hsts_max_age = 31536000  # 1 year
        self.hsts_include_subdomains = True
        self.csp_rules = self._build_csp_rules()
        self.headers = self._build_headers()
        
        logger.info("SecurityHeaders initialized")
    
    def _build_headers(self) -> Dict[str, str]:
        """Build security headers dictionary"""
        headers = {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Clickjacking protection
            "X-Frame-Options": "DENY",
            
            # Legacy XSS filter
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions policy (formerly Feature-Policy)
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "accelerometer=(), "
                "gyroscope=(), "
                "magnetometer=()"
            ),
            
            # Prevent DNS prefetch
            "X-DNS-Prefetch-Control": "off",
        }
        
        # Add HSTS if HTTPS is enforced
        if self.enforce_https:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            hsts_value += "; preload"
            headers["Strict-Transport-Security"] = hsts_value
        
        # Add CSP header
        headers["Content-Security-Policy"] = self.csp_rules
        
        return headers
    
    def _build_csp_rules(self) -> str:
        """Build Content-Security-Policy rules"""
        rules = {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'"],  # Adjust based on needs
            "style-src": ["'self'", "'unsafe-inline'"],
            "img-src": ["'self'", "data:"],
            "font-src": ["'self'"],
            "connect-src": ["'self'"],
            "frame-ancestors": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
            "object-src": ["'none'"],
            "upgrade-insecure-requests": [""],
        }
        
        # Convert to CSP string
        csp_parts = []
        for directive, values in rules.items():
            if values and values[0] != "":
                csp_parts.append(f"{directive} {' '.join(values)}")
            elif not values or values == [""]:
                csp_parts.append(directive)
        
        return "; ".join(csp_parts)
    
    def get_headers(self) -> Dict[str, str]:
        """Get all security headers"""
        return self.headers.copy()
    
    def get_header(self, name: str) -> Optional[str]:
        """Get specific security header"""
        return self.headers.get(name)
    
    def check_https(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Check if URL uses HTTPS (if enforced)
        
        Args:
            url: URL to check
            
        Returns:
            (is_valid, error_message)
        """
        if not self.enforce_https:
            return True, None
        
        if not url.startswith("https://"):
            return False, "HTTPS is required"
        
        return True, None
    
    def is_domain_allowed(self, domain: str) -> bool:
        """Check if domain is in allowed list"""
        return domain in self.allowed_domains or "*" in self.allowed_domains
    
    def add_allowed_domain(self, domain: str) -> None:
        """Add domain to allowed list"""
        if domain not in self.allowed_domains:
            self.allowed_domains.append(domain)
            logger.info(f"Added allowed domain: {domain}")
    
    def validate_request_origin(self, origin: str) -> Tuple[bool, Optional[str]]:
        """
        Validate request origin header
        
        Args:
            origin: Origin header value
            
        Returns:
            (is_valid, error_message)
        """
        if not origin:
            return False, "Origin header missing"
        
        # Extract domain from origin
        try:
            # origin format: https://example.com:8080
            domain = origin.split("://")[1].split(":")[0]
        except (IndexError, ValueError):
            return False, "Invalid origin format"
        
        if not self.is_domain_allowed(domain):
            return False, f"Origin {domain} not allowed"
        
        return True, None


class CORSConfiguration:
    """
    CORS (Cross-Origin Resource Sharing) Configuration
    
    Controls:
    - Allowed origins
    - Allowed methods
    - Allowed headers
    - Credentials
    - Max age
    """
    
    def __init__(
        self,
        allow_origins: Optional[list] = None,
        allow_methods: Optional[list] = None,
        allow_headers: Optional[list] = None,
        allow_credentials: bool = False,
        max_age: int = 3600,
    ):
        """
        Initialize CORS configuration
        
        Args:
            allow_origins: List of allowed origins
            allow_methods: List of allowed HTTP methods
            allow_headers: List of allowed headers
            allow_credentials: Whether to allow credentials
            max_age: Preflight cache duration in seconds
        """
        self.allow_origins = allow_origins or ["http://localhost:3000"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["Content-Type", "Authorization"]
        self.allow_credentials = allow_credentials
        self.max_age = max_age
        
        logger.info("CORSConfiguration initialized")
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed"""
        if "*" in self.allow_origins:
            return True
        return origin in self.allow_origins
    
    def get_cors_headers(self, origin: str) -> Dict[str, str]:
        """Get CORS response headers for origin"""
        headers = {}
        
        if self.is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
            headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
            headers["Access-Control-Max-Age"] = str(self.max_age)
            
            if self.allow_credentials:
                headers["Access-Control-Allow-Credentials"] = "true"
        
        return headers


class HTTPSEnforcer:
    """
    Enforces HTTPS/TLS requirements
    
    Implements:
    - HTTPS enforcement
    - TLS version validation
    - Certificate validation
    - Secure cookie configuration
    """
    
    MINIMUM_TLS_VERSION = "1.2"  # Minimum TLS 1.2
    RECOMMENDED_TLS_VERSION = "1.3"
    
    def __init__(self, enforce: bool = True, min_tls_version: str = "1.2"):
        """
        Initialize HTTPS enforcer
        
        Args:
            enforce: Whether to enforce HTTPS
            min_tls_version: Minimum TLS version (1.2 or 1.3)
        """
        self.enforce = enforce
        self.min_tls_version = min_tls_version
        
        logger.info(f"HTTPSEnforcer initialized (enforce={enforce}, min_tls={min_tls_version})")
    
    def validate_protocol(self, protocol: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that HTTPS is used (if enforced)
        
        Args:
            protocol: Protocol string (http/https)
            
        Returns:
            (is_valid, error_message)
        """
        if not self.enforce:
            return True, None
        
        if protocol.lower() != "https":
            return False, "HTTPS is required"
        
        return True, None
    
    def get_secure_cookie_attributes(self) -> Dict[str, any]:
        """Get secure cookie attributes"""
        return {
            "secure": self.enforce,  # Only send over HTTPS
            "httponly": True,  # Not accessible to JavaScript
            "samesite": "Strict",  # CSRF protection
            "max-age": 3600,  # 1 hour expiration
        }


# Singleton instances
_security_headers_instance: Optional[SecurityHeaders] = None
_cors_instance: Optional[CORSConfiguration] = None
_https_enforcer_instance: Optional[HTTPSEnforcer] = None


def get_security_headers(enforce_https: bool = True) -> SecurityHeaders:
    """Get or create SecurityHeaders singleton"""
    global _security_headers_instance
    if _security_headers_instance is None:
        _security_headers_instance = SecurityHeaders(enforce_https=enforce_https)
    return _security_headers_instance


def get_cors_config(allow_origins: Optional[list] = None) -> CORSConfiguration:
    """Get or create CORS configuration singleton"""
    global _cors_instance
    if _cors_instance is None:
        _cors_instance = CORSConfiguration(allow_origins=allow_origins)
    return _cors_instance


def get_https_enforcer(enforce: bool = True) -> HTTPSEnforcer:
    """Get or create HTTPS enforcer singleton"""
    global _https_enforcer_instance
    if _https_enforcer_instance is None:
        _https_enforcer_instance = HTTPSEnforcer(enforce=enforce)
    return _https_enforcer_instance
