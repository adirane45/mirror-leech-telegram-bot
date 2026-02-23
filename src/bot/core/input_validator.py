"""
Input Validation Framework for Phase 3
Comprehensive input validation for security and data integrity
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Type
from urllib.parse import urlparse
from pathlib import Path

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Base validation error"""
    pass


class ValidationRule:
    """Base validation rule"""
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate value
        
        Returns:
            (is_valid, error_message)
        """
        raise NotImplementedError


class StringValidator(ValidationRule):
    """Validates string inputs"""
    
    def __init__(
        self,
        min_length: int = 0,
        max_length: int = 1000,
        pattern: Optional[str] = None,
        allow_special_chars: bool = False,
    ):
        """
        Initialize string validator
        
        Args:
            min_length: Minimum string length
            max_length: Maximum string length
            pattern: Regex pattern to match
            allow_special_chars: Whether to allow special characters
        """
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.allow_special_chars = allow_special_chars
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate string"""
        if not isinstance(value, str):
            return False, f"Expected string, got {type(value).__name__}"
        
        if len(value) < self.min_length:
            return False, f"String too short (min: {self.min_length})"
        
        if len(value) > self.max_length:
            return False, f"String too long (max: {self.max_length})"
        
        if not self.allow_special_chars:
            if not re.match(r"^[a-zA-Z0-9\s\-_.@]*$", value):
                return False, "Special characters not allowed"
        
        if self.pattern:
            if not re.match(self.pattern, value):
                return False, f"Invalid format"
        
        return True, None


class IntegerValidator(ValidationRule):
    """Validates integer inputs"""
    
    def __init__(self, min_value: Optional[int] = None, max_value: Optional[int] = None):
        """
        Initialize integer validator
        
        Args:
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        """
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate integer"""
        if not isinstance(value, int) or isinstance(value, bool):
            return False, f"Expected integer, got {type(value).__name__}"
        
        if self.min_value is not None and value < self.min_value:
            return False, f"Value below minimum ({self.min_value})"
        
        if self.max_value is not None and value > self.max_value:
            return False, f"Value above maximum ({self.max_value})"
        
        return True, None


class EmailValidator(ValidationRule):
    """Validates email addresses"""
    
    # RFC 5322 simplified pattern
    EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate email"""
        if not isinstance(value, str):
            return False, "Email must be string"
        
        if len(value) > 254:  # RFC 5321
            return False, "Email too long"
        
        if not re.match(self.EMAIL_PATTERN, value):
            return False, "Invalid email format"
        
        return True, None


class URLValidator(ValidationRule):
    """Validates URLs"""
    
    def __init__(self, allowed_schemes: Optional[List[str]] = None):
        """
        Initialize URL validator
        
        Args:
            allowed_schemes: List of allowed schemes (http, https, etc.)
        """
        self.allowed_schemes = allowed_schemes or ["http", "https"]
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate URL"""
        if not isinstance(value, str):
            return False, "URL must be string"
        
        try:
            parsed = urlparse(value)
            
            if not parsed.scheme:
                return False, "URL missing scheme"
            
            if parsed.scheme not in self.allowed_schemes:
                return False, f"Scheme '{parsed.scheme}' not allowed"
            
            if not parsed.netloc:
                return False, "URL missing domain"
            
            return True, None
        
        except Exception as e:
            return False, f"Invalid URL: {str(e)}"


class FileValidator(ValidationRule):
    """Validates file uploads"""
    
    def __init__(
        self,
        max_size: int = 10 * 1024 * 1024,  # 10MB default
        allowed_extensions: Optional[List[str]] = None,
        allowed_mimetypes: Optional[List[str]] = None,
    ):
        """
        Initialize file validator
        
        Args:
            max_size: Maximum file size in bytes
            allowed_extensions: List of allowed file extensions
            allowed_mimetypes: List of allowed MIME types
        """
        self.max_size = max_size
        self.allowed_extensions = allowed_extensions or [
            "jpg", "jpeg", "png", "pdf", "txt", "zip", "gz"
        ]
        self.allowed_mimetypes = allowed_mimetypes or [
            "image/jpeg", "image/png", "application/pdf", "text/plain"
        ]
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate file
        
        Args:
            value: File object or dict with 'filename', 'size', 'mimetype'
        """
        if isinstance(value, dict):
            filename = value.get("filename", "")
            size = value.get("size", 0)
            mimetype = value.get("mimetype", "")
        else:
            return False, "File validation requires dict with filename, size, mimetype"
        
        # Check filename
        if not filename:
            return False, "Filename required"
        
        # Check file extension
        ext = Path(filename).suffix.lstrip(".").lower()
        if ext not in self.allowed_extensions:
            return False, f"Extension '.{ext}' not allowed"
        
        # Check file size
        if size > self.max_size:
            return False, f"File exceeds maximum size ({self.max_size} bytes)"
        
        if size == 0:
            return False, "File is empty"
        
        # Validate extension is not suspicious
        if ".." in filename or "/" in filename or "\\" in filename:
            return False, "Invalid filename"
        
        return True, None


class InputValidator:
    """
    Main input validator for comprehensive validation
    
    Validates:
    - Strings (length, pattern, characters)
    - Numbers (range, type)
    - Emails
    - URLs
    - Files
    - Custom rules
    """
    
    def __init__(self):
        """Initialize input validator"""
        self.validators = {
            "string": StringValidator,
            "integer": IntegerValidator,
            "email": EmailValidator,
            "url": URLValidator,
            "file": FileValidator,
        }
        
        logger.info("InputValidator initialized")
    
    def validate_field(
        self,
        value: Any,
        field_type: str,
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a single field
        
        Args:
            value: Value to validate
            field_type: Type of field (string, integer, email, url, file)
            **kwargs: Additional arguments for validator
            
        Returns:
            (is_valid, error_message)
        """
        if field_type not in self.validators:
            return False, f"Unknown field type: {field_type}"
        
        validator_class = self.validators[field_type]
        validator = validator_class(**kwargs)
        
        return validator.validate(value)
    
    def validate_schema(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Dict[str, Any]],
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Validate data against schema
        
        Args:
            data: Data to validate
            schema: Validation schema
            
        Returns:
            (is_valid, errors_dict)
            
        Example:
            schema = {
                "username": {"type": "string", "min_length": 3, "max_length": 20},
                "email": {"type": "email"},
                "age": {"type": "integer", "min_value": 0, "max_value": 150},
            }
            
            is_valid, errors = validator.validate_schema(data, schema)
        """
        errors = {}
        
        for field_name, field_schema in schema.items():
            if field_name not in data:
                if field_schema.get("required", True):
                    errors[field_name] = "Field required"
                continue
            
            field_type = field_schema.get("type", "string")
            field_value = data[field_name]
            
            # Remove 'type' and 'required' from kwargs
            validator_kwargs = {
                k: v for k, v in field_schema.items()
                if k not in ["type", "required"]
            }
            
            is_valid, error = self.validate_field(field_value, field_type, **validator_kwargs)
            
            if not is_valid:
                errors[field_name] = error
        
        return len(errors) == 0, errors
    
    def sanitize_string(self, value: str, remove_special: bool = True) -> str:
        """
        Sanitize string input
        
        Args:
            value: String to sanitize
            remove_special: Whether to remove special characters
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return ""
        
        # Remove null bytes
        sanitized = value.replace("\x00", "")
        
        # Remove control characters
        sanitized = "".join(
            char for char in sanitized
            if ord(char) >= 32 or char in "\t\n\r"
        )
        
        if remove_special:
            # Keep only alphanumeric, spaces, and common punctuation
            sanitized = re.sub(r"[^a-zA-Z0-9\s\-_.@]", "", sanitized)
        
        return sanitized.strip()
    
    def sanitize_html(self, value: str) -> str:
        """
        Sanitize HTML input (basic)
        
        Args:
            value: HTML to sanitize
            
        Returns:
            Sanitized HTML
        """
        if not isinstance(value, str):
            return ""
        
        # Remove script tags
        sanitized = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove event handlers
        sanitized = re.sub(r"\s*on\w+\s*=\s*['\"]?[^'\"]*['\"]?", "", sanitized)
        
        # Remove javascript: protocol
        sanitized = re.sub(r"javascript:", "", sanitized, flags=re.IGNORECASE)
        
        return sanitized


# Singleton instance
_input_validator_instance: Optional[InputValidator] = None


def get_input_validator() -> InputValidator:
    """Get or create InputValidator singleton"""
    global _input_validator_instance
    if _input_validator_instance is None:
        _input_validator_instance = InputValidator()
    return _input_validator_instance
