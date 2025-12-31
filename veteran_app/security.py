"""
Security helper functions for authorization checks
"""
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def check_state_access(user, state):
    """Check if user has access to a specific state"""
    if user.is_superuser:
        return True
    
    if hasattr(user, 'state_profile'):
        return user.state_profile.state == state
    
    return False


def check_veteran_access(user, veteran_member):
    """Check if user has access to a specific veteran member"""
    if user.is_superuser:
        return True
    
    # State admin can access veterans in their state
    if hasattr(user, 'state_profile'):
        return user.state_profile.state == veteran_member.state
    
    # Veteran can access their own profile
    if hasattr(user, 'veteran_profile'):
        return user.veteran_profile.veteran_member == veteran_member
    
    return False


def require_state_access(view_func):
    """Decorator to check state access"""
    @wraps(view_func)
    def wrapper(request, state_id, *args, **kwargs):
        from .models import State
        from django.shortcuts import get_object_or_404
        
        state = get_object_or_404(State, pk=state_id)
        
        if not check_state_access(request.user, state):
            messages.error(request, "You don't have permission to access this state.")
            return redirect('index')
        
        return view_func(request, state_id, *args, **kwargs)
    
    return wrapper


def require_veteran_access(view_func):
    """Decorator to check veteran member access"""
    @wraps(view_func)
    def wrapper(request, member_id, *args, **kwargs):
        from .models import VeteranMember
        from django.shortcuts import get_object_or_404
        
        member = get_object_or_404(VeteranMember, pk=member_id)
        
        if not check_veteran_access(request.user, member):
            messages.error(request, "You don't have permission to access this member.")
            return redirect('index')
        
        return view_func(request, member_id, *args, **kwargs)
    
    return wrapper


def require_own_transaction_access(view_func):
    """Decorator to check transaction ownership"""
    @wraps(view_func)
    def wrapper(request, transaction_id, *args, **kwargs):
        from .models import Transaction
        from django.shortcuts import get_object_or_404
        from django.http import JsonResponse
        
        transaction = get_object_or_404(Transaction, pk=transaction_id)
        
        # Superuser has full access
        if request.user.is_superuser:
            return view_func(request, transaction_id, *args, **kwargs)
        
        # Veteran can only access their own transactions
        if hasattr(request.user, 'veteran_profile'):
            if transaction.veteran == request.user.veteran_profile.veteran_member:
                return view_func(request, transaction_id, *args, **kwargs)
        
        # State admin can access transactions in their state
        if hasattr(request.user, 'state_profile'):
            if transaction.veteran and transaction.veteran.state == request.user.state_profile.state:
                return view_func(request, transaction_id, *args, **kwargs)
        
        # Unauthorized
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Unauthorized access'}, status=403)
        else:
            messages.error(request, "You don't have permission to access this transaction.")
            return redirect('index')
    
    return wrapper


def log_security_event(user, action, resource, details=''):
    """Log security-related events"""
    import logging
    logger = logging.getLogger('veteran_app.security')
    
    log_message = f"User: {user.username} | Action: {action} | Resource: {resource}"
    if details:
        log_message += f" | Details: {details}"
    
    logger.warning(log_message)


def check_file_security(uploaded_file):
    """Additional file security checks"""
    import os
    
    # Check file size
    max_size = 5 * 1024 * 1024  # 5MB
    if uploaded_file.size > max_size:
        return False, "File size exceeds 5MB limit"
    
    # Check file extension
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
    
    if ext not in allowed_extensions:
        return False, f"File type {ext} not allowed"
    
    # Check for double extensions (e.g., file.php.jpg)
    name_parts = uploaded_file.name.split('.')
    if len(name_parts) > 2:
        return False, "Multiple file extensions not allowed"
    
    return True, "File is safe"
