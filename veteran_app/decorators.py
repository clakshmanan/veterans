from functools import wraps
from django.http import HttpResponse
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required

def rate_limit(max_requests=5, window=300):
    """Rate limiting decorator"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            key = f"rate_limit_{request.user.id}_{view_func.__name__}"
            current_requests = cache.get(key, 0)
            
            if current_requests >= max_requests:
                response = HttpResponse("Too many requests. Please try again later.", status=429)
                response['Retry-After'] = str(window)
                return response
            
            cache.set(key, current_requests + 1, window)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_permissions(*perms):
    """Require specific permissions"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not request.user.has_perms(perms):
                raise PermissionDenied("Insufficient permissions")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def validate_state_access(view_func):
    """Validate state access for state admins"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        try:
            user_state = request.user.state_profile
            if not user_state.approved:
                raise PermissionDenied("Account not approved")
            
            # Add state to kwargs for view access
            kwargs['user_state'] = user_state
            return view_func(request, *args, **kwargs)
        except:
            raise PermissionDenied("Invalid state access")
    return wrapper

def require_state_access(state_param='state_id'):
    """Decorator to validate state access for views with state_id parameter"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            from veteran_app.models import State, UserState
            
            # Get state_id from kwargs
            state_id = kwargs.get(state_param)
            if not state_id:
                raise PermissionDenied("State ID required")
            
            try:
                state = State.objects.get(id=state_id)
            except State.DoesNotExist:
                raise PermissionDenied("Invalid state")
            
            # Superuser can access any state
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check state admin access
            try:
                user_state = request.user.state_profile
                if not user_state.approved:
                    raise PermissionDenied('Your account is not approved.')
                if user_state.state != state:
                    raise PermissionDenied('You do not have permission to access this state.')
            except UserState.DoesNotExist:
                raise PermissionDenied('You do not have permission to access state data.')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator