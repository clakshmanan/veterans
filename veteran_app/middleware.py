from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to all responses"""
    
    def process_response(self, request, response):
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HSTS for HTTPS
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response

class RequestValidationMiddleware(MiddlewareMixin):
    """Validate requests for security"""
    
    def process_request(self, request):
        # Skip validation for admin URLs
        if request.path.startswith('/admin/'):
            return None
            
        # Block requests with suspicious patterns
        suspicious_patterns = [
            '../', '..\\', '<script', 'javascript:', 'vbscript:',
            'onload=', 'onerror=', 'eval(', 'expression('
        ]
        
        # Check query parameters and POST data
        for key, value in request.GET.items():
            if any(pattern in str(value).lower() for pattern in suspicious_patterns):
                logger.warning(f"Suspicious request blocked: {request.path} - {key}={value}")
                return HttpResponseForbidden("Invalid request")
        
        if request.method == 'POST':
            for key, value in request.POST.items():
                if any(pattern in str(value).lower() for pattern in suspicious_patterns):
                    logger.warning(f"Suspicious POST blocked: {request.path} - {key}={value}")
                    return HttpResponseForbidden("Invalid request")
        
        return None

class SessionSecurityMiddleware(MiddlewareMixin):
    """Enhanced session security"""
    
    def process_request(self, request):
        # Skip session security checks for admin URLs
        if request.path.startswith('/admin/'):
            return None
            
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Check for session hijacking
            current_ip = self.get_client_ip(request)
            session_ip = request.session.get('ip_address')
            
            # Only check IP mismatch if session IP was already set AND user has made at least one request
            # This prevents logout during initial login flow
            if session_ip and session_ip != current_ip and request.session.get('ip_verified', False):
                logger.warning(f"Session IP mismatch for user {request.user.username}: {session_ip} vs {current_ip}")
                request.session.flush()
                return None
            
            # Store IP in session and mark as verified after first request
            request.session['ip_address'] = current_ip
            request.session['ip_verified'] = True
            
            # Update last activity
            request.session['last_activity'] = request.session.get('last_activity', 0) + 1
        
        return None
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class UserStateMiddleware(MiddlewareMixin):
    """Track user state and activity"""
    
    def process_request(self, request):
        # Skip for admin URLs
        if request.path.startswith('/admin/'):
            return None
            
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Update user's last activity
            request.session['last_seen'] = request.session.get('last_seen', 0) + 1
        return None

class GlobalAnnouncementMiddleware(MiddlewareMixin):
    """Add global announcements to context"""
    
    def process_template_response(self, request, response):
        from datetime import date
        from .models import Notification, VeteranMember
        
        # Get today's birthdays
        today = date.today()
        birthdays = VeteranMember.objects.filter(
            date_of_birth__month=today.month,
            date_of_birth__day=today.day,
            approved=True
        ).select_related('rank', 'state')[:5]
        
        # Get active notifications (not expired)
        notifications = Notification.objects.filter(
            is_active=True,
            created_at__date__gte=today
        ).order_by('-created_at')[:10]
        
        response.context_data['global_birthdays'] = birthdays
        response.context_data['global_notifications'] = notifications
        
        return response