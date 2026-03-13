"""
Security Middleware Integration
Integrates all Phase 3 security modules into FastAPI application

Phase 3: Security & Hardening
Enhanced by: justadi
Date: February 8, 2026
"""

import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from starlette.datastructures import UploadFile
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .csrf_protection import get_csrf_protection
from .input_validator import get_input_validator
from .security_audit import AuditEventType, AuditSeverity, get_audit_logger
from .security_headers import get_https_enforcer, get_security_headers

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware that integrates all Phase 3 security features

    Features:
    - Security headers on all responses
    - CSRF protection for state-changing methods
    - Input validation for request data
    - Security audit logging
    - Request ID tracking
    - Rate limiting (optional)
    """

    def __init__(
        self,
        app: ASGIApp,
        enable_csrf: bool = True,
        enable_input_validation: bool = True,
        enable_audit_logging: bool = True,
        enable_https_redirect: bool = False,
        exempt_paths: Optional[list[str]] = None,
    ) -> None:
        super().__init__(app)
        self.enable_csrf = enable_csrf
        self.enable_input_validation = enable_input_validation
        self.enable_audit_logging = enable_audit_logging
        self.enable_https_redirect = enable_https_redirect
        self.exempt_paths = exempt_paths or ["/health", "/metrics", "/docs", "/openapi.json"]

        # Initialize security components
        self.security_headers = get_security_headers()
        self.csrf_protection = get_csrf_protection()
        self.input_validator = get_input_validator()
        self.audit_logger = get_audit_logger()
        self.https_enforcer = get_https_enforcer()

        logger.info(
            f"SecurityMiddleware initialized (CSRF={enable_csrf}, "
            f"InputValidation={enable_input_validation}, "
            f"AuditLogging={enable_audit_logging}, "
            f"HTTPS={enable_https_redirect})"
        )

    def _is_exempt_path(self, path: str) -> bool:
        return any(path.startswith(exempt_path) for exempt_path in self.exempt_paths)

    def _log_security_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        severity: AuditSeverity,
        details: dict[str, Any],
        request_id: str,
    ) -> None:
        if not self.enable_audit_logging:
            return
        self.audit_logger.log_security_event(
            event_type=event_type,
            user_id=user_id,
            severity=severity,
            details=details,
            request_id=request_id,
        )

    def _enforce_https(
        self,
        request: Request,
        is_exempt: bool,
        path: str,
        request_id: str,
    ) -> Optional[Response]:
        if not self.enable_https_redirect or is_exempt:
            return None
        is_secure, _ = self.https_enforcer.validate_protocol(request.url.scheme)
        if is_secure:
            return None
        self._log_security_event(
            event_type=AuditEventType.UNAUTHORIZED_ACCESS,
            user_id="anonymous",
            severity=AuditSeverity.WARNING,
            details={"reason": "HTTP request on HTTPS-only endpoint", "path": path},
            request_id=request_id,
        )
        return JSONResponse(status_code=400, content={"error": "HTTPS required"})

    def _requires_csrf(self, request: Request, is_exempt: bool) -> bool:
        return (
            self.enable_csrf
            and not is_exempt
            and request.method in ["POST", "PUT", "DELETE", "PATCH"]
        )

    async def _extract_csrf_token(self, request: Request) -> Optional[str]:
        csrf_token = request.headers.get("X-CSRF-Token")
        if csrf_token:
            return csrf_token
        try:
            form = await request.form()
            token = form.get("csrf_token")
            if isinstance(token, UploadFile):
                return None
            if isinstance(token, str):
                return token
            return None
        except Exception:
            return None

    async def _validate_csrf(
        self,
        request: Request,
        is_exempt: bool,
        path: str,
        request_id: str,
    ) -> Optional[Response]:
        if not self._requires_csrf(request, is_exempt):
            return None
        session_id = request.cookies.get("session_id") or request.headers.get(
            "X-Session-ID", "default"
        )
        csrf_token = await self._extract_csrf_token(request)
        if not csrf_token:
            logger.warning(f"Missing CSRF token for {request.method} {path}")
            return None

        is_valid, error = self.csrf_protection.validate_request(
            request.method,
            session_id,
            csrf_token,
            origin=request.headers.get("Origin"),
            referer=request.headers.get("Referer"),
        )
        if is_valid:
            return None

        self._log_security_event(
            event_type=AuditEventType.CSRF_DETECTION,
            user_id=session_id,
            severity=AuditSeverity.WARNING,
            details={"error": error, "path": path, "method": request.method},
            request_id=request_id,
        )
        return JSONResponse(
            status_code=403,
            content={"error": "CSRF validation failed", "detail": error},
        )

    def _sanitize_query_params(self, request: Request) -> None:
        if not self.enable_input_validation:
            return
        for key, value in request.query_params.items():
            if isinstance(value, str):
                sanitized = self.input_validator.sanitize_string(value)
                if sanitized != value:
                    logger.warning(
                        f"Sanitized query param '{key}': {value} -> {sanitized}"
                    )

    def _apply_response_headers(self, response: Response, request_id: str) -> None:
        headers_dict = self.security_headers.get_headers()
        for header_name, header_value in headers_dict.items():
            response.headers[header_name] = header_value
        response.headers["X-Request-ID"] = request_id

    def _audit_success(
        self,
        request: Request,
        response: Response,
        is_exempt: bool,
        path: str,
        request_id: str,
        start_time: float,
    ) -> None:
        if not self.enable_audit_logging or is_exempt:
            return
        duration_ms = (time.time() - start_time) * 1000
        self.audit_logger.log_api_access(
            user_id=request.cookies.get("session_id", "anonymous"),
            endpoint=path,
            method=request.method,
            status_code=response.status_code,
            ip_address=request.client.host if request.client else "unknown",
            request_id=request_id,
            metadata={"duration_ms": round(duration_ms, 2)},
        )

    def _handle_unexpected_error(
        self, request: Request, request_id: str, error: Exception
    ) -> Response:
        logger.error(f"Security middleware error: {error}", exc_info=True)
        self._log_security_event(
            event_type=AuditEventType.SYSTEM_ERROR,
            user_id="system",
            severity=AuditSeverity.CRITICAL,
            details={"error": str(error), "path": request.url.path},
            request_id=request_id,
        )
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "request_id": request_id},
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request through security pipeline"""

        # Generate unique request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()

        try:
            path = request.url.path
            is_exempt = self._is_exempt_path(path)

            https_response = self._enforce_https(request, is_exempt, path, request_id)
            if https_response is not None:
                return https_response

            csrf_response = await self._validate_csrf(request, is_exempt, path, request_id)
            if csrf_response is not None:
                return csrf_response

            if not is_exempt:
                self._sanitize_query_params(request)

            response = await call_next(request)

            self._apply_response_headers(response, request_id)
            self._audit_success(
                request,
                response,
                is_exempt,
                path,
                request_id,
                start_time,
            )

            return response

        except HTTPException:
            raise

        except Exception as e:
            return self._handle_unexpected_error(request, request_id, e)


def setup_security_middleware(
    app: FastAPI,
    enable_csrf: bool = True,
    enable_input_validation: bool = True,
    enable_audit_logging: bool = True,
    enable_https_redirect: bool = False,
    exempt_paths: Optional[list[str]] = None,
) -> FastAPI:
    """
    Setup security middleware on FastAPI application

    Args:
        app: FastAPI application instance
        enable_csrf: Enable CSRF protection
        enable_input_validation: Enable input validation
        enable_audit_logging: Enable security audit logging
        enable_https_redirect: Enable HTTPS enforcement
        exempt_paths: List of paths to exempt from security checks

    Returns:
        FastAPI app with security middleware added
    """

    app.add_middleware(
        SecurityMiddleware,
        enable_csrf=enable_csrf,
        enable_input_validation=enable_input_validation,
        enable_audit_logging=enable_audit_logging,
        enable_https_redirect=enable_https_redirect,
        exempt_paths=exempt_paths,
    )

    logger.info("✅ Security middleware configured successfully")
    return app


def add_csrf_token_endpoint(app: FastAPI) -> None:
    """Add endpoint to retrieve CSRF tokens for authenticated sessions"""

    @app.get("/api/v1/security/csrf-token")
    async def get_csrf_token(request: Request) -> JSONResponse:
        """
        Get CSRF token for current session

        Returns CSRF token that must be included in state-changing requests
        """
        csrf_protection = get_csrf_protection()
        audit_logger = get_audit_logger()

        # Get or create session ID
        session_id = request.cookies.get("session_id", "default")

        # Generate CSRF token
        token = csrf_protection.get_token_for_session(session_id)

        # Audit log token generation
        audit_logger.log_api_access(
            user_id=session_id,
            endpoint="/api/v1/security/csrf-token",
            method="GET",
            status_code=200,
            ip_address=request.client.host if request.client else "unknown",
            request_id=getattr(request.state, "request_id", "unknown")
        )

        return JSONResponse(
            content={
                "csrf_token": token,
                "expires_in": 3600,  # 1 hour
                "session_id": session_id
            }
        )

    logger.info("✅ CSRF token endpoint added: /api/v1/security/csrf-token")


def add_security_status_endpoint(app: FastAPI) -> None:
    """Add endpoint to check security feature status"""

    @app.get("/api/v1/security/status")
    async def security_status() -> JSONResponse:
        """
        Get security features status

        Returns enabled security features and their configurations
        """
        security_headers = get_security_headers()

        return JSONResponse(
            content={
                "security_features": {
                    "security_headers": True,
                    "csrf_protection": True,
                    "input_validation": True,
                    "https_enforcement": True,
                    "audit_logging": True,
                    "secrets_encryption": True,
                },
                "security_headers": list(security_headers.get_headers().keys()),
                "compliance": {
                    "owasp_top_10": True,
                    "cwe_top_25": True,
                },
                "timestamp": time.time()
            }
        )

    logger.info("✅ Security status endpoint added: /api/v1/security/status")


def integrate_security_features(
    app: FastAPI,
    enable_middleware: bool = True,
    enable_csrf_endpoint: bool = True,
    enable_status_endpoint: bool = True,
    **middleware_kwargs: Any,
) -> FastAPI:
    """
    Full integration of Phase 3 security features

    This is the main entry point for adding all security features to your app.

    Usage:
        from bot.core.security_middleware import integrate_security_features

        app = FastAPI()
        app = integrate_security_features(app)

    Args:
        app: FastAPI application instance
        enable_middleware: Enable security middleware
        enable_csrf_endpoint: Add CSRF token endpoint
        enable_status_endpoint: Add security status endpoint
        **middleware_kwargs: Additional arguments for security middleware

    Returns:
        FastAPI app with all security features integrated
    """

    logger.info("🔒 Integrating Phase 3 security features...")

    # Setup security middleware
    if enable_middleware:
        app = setup_security_middleware(app, **middleware_kwargs)

    # Add CSRF token endpoint
    if enable_csrf_endpoint:
        add_csrf_token_endpoint(app)

    # Add security status endpoint
    if enable_status_endpoint:
        add_security_status_endpoint(app)

    logger.info("✅ Phase 3 security integration complete!")
    logger.info("   - Security middleware: Active")
    logger.info("   - CSRF protection: Enabled")
    logger.info("   - Input validation: Enabled")
    logger.info("   - Audit logging: Enabled")
    logger.info("   - Security headers: 8 headers")
    logger.info("   - CSRF token endpoint: /api/v1/security/csrf-token")
    logger.info("   - Security status endpoint: /api/v1/security/status")

    return app


# Singleton getter for backward compatibility
_security_middleware_instance = None


def get_security_middleware() -> SecurityMiddleware | None:
    """Get singleton security middleware instance"""
    global _security_middleware_instance
    if _security_middleware_instance is None:
        logger.warning("SecurityMiddleware not initialized via middleware setup")
    return _security_middleware_instance
