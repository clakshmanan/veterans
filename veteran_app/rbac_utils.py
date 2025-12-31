from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from functools import wraps
from .models import Role, Permission, UserRole, RoleAuditLog

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_rbac_action(action, user, target_user=None, role=None, permission=None, details=None, request=None):
    """Log RBAC actions for audit trail"""
    ip_address = get_client_ip(request) if request else None
    RoleAuditLog.objects.create(
        action=action,
        user=user,
        target_user=target_user,
        role=role,
        permission=permission,
        details=details or {},
        ip_address=ip_address
    )

def has_permission(user, permission_codename):
    """Check if user has specific permission through their roles"""
    if user.is_superuser:
        return True
    
    # Get all active roles for the user
    user_roles = UserRole.objects.filter(
        user=user, 
        is_active=True, 
        role__is_active=True
    ).select_related('role')
    
    # Check if any role has the required permission
    for user_role in user_roles:
        if user_role.role.permissions.filter(
            codename=permission_codename, 
            is_active=True
        ).exists():
            return True
    
    return False

def has_role(user, role_name):
    """Check if user has specific role"""
    if user.is_superuser:
        return True
    
    return UserRole.objects.filter(
        user=user,
        role__name=role_name,
        is_active=True,
        role__is_active=True
    ).exists()

def get_user_permissions(user):
    """Get all permissions for a user"""
    if user.is_superuser:
        return Permission.objects.filter(is_active=True)
    
    user_roles = UserRole.objects.filter(
        user=user,
        is_active=True,
        role__is_active=True
    ).select_related('role')
    
    permission_ids = []
    for user_role in user_roles:
        permission_ids.extend(
            user_role.role.permissions.filter(is_active=True).values_list('id', flat=True)
        )
    
    return Permission.objects.filter(id__in=permission_ids)

def get_user_roles(user):
    """Get all active roles for a user"""
    if user.is_superuser:
        return Role.objects.filter(is_active=True)
    
    return Role.objects.filter(
        role_assignments__user=user,
        role_assignments__is_active=True,
        is_active=True
    )

def assign_role(user, role, assigned_by, notes='', request=None):
    """Assign role to user"""
    user_role, created = UserRole.objects.get_or_create(
        user=user,
        role=role,
        defaults={
            'assigned_by': assigned_by,
            'notes': notes,
            'is_active': True
        }
    )
    
    if not created and not user_role.is_active:
        user_role.is_active = True
        user_role.assigned_by = assigned_by
        user_role.notes = notes
        user_role.save()
    
    # Log the action
    log_rbac_action(
        action='assign_role',
        user=assigned_by,
        target_user=user,
        role=role,
        details={'notes': notes, 'created': created},
        request=request
    )
    
    return user_role

def revoke_role(user, role, revoked_by, request=None):
    """Revoke role from user"""
    try:
        user_role = UserRole.objects.get(user=user, role=role)
        user_role.is_active = False
        user_role.save()
        
        # Log the action
        log_rbac_action(
            action='revoke_role',
            user=revoked_by,
            target_user=user,
            role=role,
            request=request
        )
        
        return True
    except UserRole.DoesNotExist:
        return False

def require_permission(permission_codename):
    """Decorator to require specific permission"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required")
            
            if not has_permission(request.user, permission_codename):
                raise PermissionDenied(f"Permission '{permission_codename}' required")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_role(role_name):
    """Decorator to require specific role"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required")
            
            if not has_role(request.user, role_name):
                raise PermissionDenied(f"Role '{role_name}' required")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_superuser_or_permission(permission_codename):
    """Decorator to require superuser OR specific permission"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required")
            
            if not (request.user.is_superuser or has_permission(request.user, permission_codename)):
                raise PermissionDenied(f"Superuser or '{permission_codename}' permission required")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def create_default_permissions():
    """Create default permissions for the system"""
    default_permissions = [
        # Veteran Management
        ('veteran.view_all', 'View All Veterans', 'veteran'),
        ('veteran.view_own_state', 'View Own State Veterans', 'veteran'),
        ('veteran.add', 'Add Veterans', 'veteran'),
        ('veteran.edit', 'Edit Veterans', 'veteran'),
        ('veteran.delete', 'Delete Veterans', 'veteran'),
        ('veteran.approve', 'Approve Veterans', 'veteran'),
        
        # Financial Management
        ('financial.view_reports', 'View Financial Reports', 'financial'),
        ('financial.manage_transactions', 'Manage Transactions', 'financial'),
        ('financial.export_data', 'Export Financial Data', 'financial'),
        
        # Event Management
        ('event.view', 'View Events', 'event'),
        ('event.create', 'Create Events', 'event'),
        ('event.edit', 'Edit Events', 'event'),
        ('event.delete', 'Delete Events', 'event'),
        ('event.manage_registrations', 'Manage Event Registrations', 'event'),
        
        # Document Management
        ('document.view', 'View Documents', 'document'),
        ('document.upload', 'Upload Documents', 'document'),
        ('document.delete', 'Delete Documents', 'document'),
        
        # Gallery Management
        ('gallery.view', 'View Gallery', 'gallery'),
        ('gallery.upload', 'Upload Images', 'gallery'),
        ('gallery.delete', 'Delete Images', 'gallery'),
        
        # User Management
        ('user.view', 'View Users', 'user'),
        ('user.create', 'Create Users', 'user'),
        ('user.edit', 'Edit Users', 'user'),
        ('user.approve', 'Approve Users', 'user'),
        
        # System Administration
        ('system.manage_roles', 'Manage Roles', 'system'),
        ('system.manage_permissions', 'Manage Permissions', 'system'),
        ('system.view_audit_logs', 'View Audit Logs', 'system'),
        ('system.manage_settings', 'Manage System Settings', 'system'),
        
        # Reports
        ('report.generate', 'Generate Reports', 'report'),
        ('report.export', 'Export Reports', 'report'),
        ('report.view_analytics', 'View Analytics', 'report'),
    ]
    
    created_permissions = []
    for codename, name, category in default_permissions:
        permission, created = Permission.objects.get_or_create(
            codename=codename,
            defaults={
                'name': name,
                'category': category,
                'description': f'Permission to {name.lower()}'
            }
        )
        if created:
            created_permissions.append(permission)
    
    return created_permissions

def create_default_roles():
    """Create default roles for the system"""
    # Create permissions first
    create_default_permissions()
    
    default_roles = [
        {
            'name': 'State Administrator',
            'description': 'Full access to state-specific data and operations',
            'permissions': [
                'veteran.view_own_state', 'veteran.add', 'veteran.edit', 'veteran.approve',
                'event.view', 'event.create', 'event.edit', 'event.manage_registrations',
                'document.view', 'document.upload', 'gallery.view', 'gallery.upload',
                'user.view', 'user.create', 'user.approve', 'report.generate'
            ]
        },
        {
            'name': 'Financial Manager',
            'description': 'Access to financial data and transaction management',
            'permissions': [
                'financial.view_reports', 'financial.manage_transactions', 'financial.export_data',
                'veteran.view_all', 'report.generate', 'report.export'
            ]
        },
        {
            'name': 'Event Manager',
            'description': 'Manage events and registrations',
            'permissions': [
                'event.view', 'event.create', 'event.edit', 'event.manage_registrations',
                'veteran.view_all', 'document.view', 'gallery.view'
            ]
        },
        {
            'name': 'Content Manager',
            'description': 'Manage documents and gallery content',
            'permissions': [
                'document.view', 'document.upload', 'document.delete',
                'gallery.view', 'gallery.upload', 'gallery.delete',
                'veteran.view_all'
            ]
        },
        {
            'name': 'Veteran User',
            'description': 'Basic veteran access to personal data',
            'permissions': [
                'veteran.view_own_state', 'event.view', 'document.view', 'gallery.view'
            ]
        },
        {
            'name': 'Read Only Admin',
            'description': 'View-only access to all data',
            'permissions': [
                'veteran.view_all', 'financial.view_reports', 'event.view',
                'document.view', 'gallery.view', 'user.view', 'report.view_analytics'
            ]
        }
    ]
    
    created_roles = []
    for role_data in default_roles:
        role, created = Role.objects.get_or_create(
            name=role_data['name'],
            defaults={
                'description': role_data['description'],
                'is_system_role': True
            }
        )
        
        if created:
            # Add permissions to the role
            permissions = Permission.objects.filter(
                codename__in=role_data['permissions']
            )
            role.permissions.set(permissions)
            created_roles.append(role)
    
    return created_roles

def get_permission_matrix():
    """Get permission matrix for UI display"""
    permissions = Permission.objects.filter(is_active=True).order_by('category', 'name')
    roles = Role.objects.filter(is_active=True).order_by('name')
    
    matrix = {}
    for role in roles:
        role_permissions = role.permissions.filter(is_active=True).values_list('id', flat=True)
        matrix[role.id] = list(role_permissions)
    
    return {
        'permissions': permissions,
        'roles': roles,
        'matrix': matrix
    }