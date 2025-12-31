"""
Security validators for file uploads and input validation
"""
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import os
import re


# File Upload Validators
def validate_file_extension(value):
    """Validate file extensions for document uploads"""
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
    if ext not in valid_extensions:
        raise ValidationError(
            f'Unsupported file extension "{ext}". Allowed: {", ".join(valid_extensions)}'
        )


def validate_image_extension(value):
    """Validate image file extensions"""
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png']
    if ext not in valid_extensions:
        raise ValidationError(
            f'Only image files allowed. Supported: {", ".join(valid_extensions)}'
        )


def validate_file_size(value):
    """Validate file size (max 5MB)"""
    filesize = value.size
    max_size = 5242880  # 5MB in bytes
    if filesize > max_size:
        raise ValidationError(f'File size cannot exceed 5MB. Current size: {filesize / 1048576:.2f}MB')


def validate_resume_extension(value):
    """Validate resume file extensions"""
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.pdf', '.doc', '.docx']
    if ext not in valid_extensions:
        raise ValidationError(
            f'Invalid resume format. Allowed: {", ".join(valid_extensions)}'
        )


# Phone Number Validator
validate_phone_number = RegexValidator(
    regex=r'^(\+91|91)?[6-9]\d{9}$',
    message='Enter a valid 10-digit Indian mobile number starting with 6-9',
    code='invalid_phone'
)


# Service Number Validator
validate_service_number = RegexValidator(
    regex=r'^\d+-[A-Za-z]$',
    message='Service number must be in format: digits-hyphen-letter (e.g., 12345-A)',
    code='invalid_service_number'
)


# Alphanumeric with limited special chars
def validate_reference_number(value):
    """Validate reference numbers (alphanumeric with hyphens and underscores only)"""
    if not re.match(r'^[A-Za-z0-9_-]+$', value):
        raise ValidationError(
            'Reference number can only contain letters, numbers, hyphens, and underscores.'
        )


# Name Validator (no special characters except space, hyphen, period)
def validate_name(value):
    """Validate person names"""
    if not re.match(r'^[A-Za-z\s\.\-]+$', value):
        raise ValidationError(
            'Name can only contain letters, spaces, hyphens, and periods.'
        )


# Prevent HTML/Script injection in text fields
def validate_no_html(value):
    """Prevent HTML tags in text input"""
    if re.search(r'<[^>]+>', value):
        raise ValidationError('HTML tags are not allowed in this field.')


# Prevent SQL injection patterns
def validate_no_sql_injection(value):
    """Basic SQL injection pattern detection"""
    sql_patterns = [
        r'(\bUNION\b.*\bSELECT\b)',
        r'(\bDROP\b.*\bTABLE\b)',
        r'(\bINSERT\b.*\bINTO\b)',
        r'(\bDELETE\b.*\bFROM\b)',
        r'(--)',
        r'(;.*\bDROP\b)',
        r'(\bOR\b.*=.*)',
        r'(\'.*\bOR\b.*\')',
    ]
    for pattern in sql_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError('Invalid input detected.')


# Prevent XSS patterns
def validate_no_xss(value):
    """Basic XSS pattern detection"""
    xss_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'onerror\s*=',
        r'onload\s*=',
        r'onclick\s*=',
        r'<iframe[^>]*>',
        r'eval\s*\(',
        r'expression\s*\(',
    ]
    for pattern in xss_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError('Potentially unsafe content detected.')
