from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from .models import Role, Permission, UserRole, RoleAuditLog, VeteranUser, UserState
from .rbac_utils import (
    has_permission, assign_role, revoke_role, log_rbac_action,
    create_default_permissions, create_default_roles, get_permission_matrix,
    get_client_ip
)

def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def rbac_dashboard(request):
    """RBAC Management Dashboard"""
    # Statistics
    stats = {
        'total_users': User.objects.count(),
        'total_roles': Role.objects.filter(is_active=True).count(),
        'total_permissions': Permission.objects.filter(is_active=True).count(),
        'active_assignments': UserRole.objects.filter(is_active=True).count(),
        'recent_actions': RoleAuditLog.objects.count()
    }
    
    # Recent audit logs
    recent_logs = RoleAuditLog.objects.select_related(
        'user', 'target_user', 'role', 'permission'
    ).order_by('-timestamp')[:10]
    
    # Role distribution
    role_stats = Role.objects.filter(is_active=True).annotate(
        user_count=Count('role_assignments', filter=Q(role_assignments__is_active=True))
    ).order_by('-user_count')
    
    # Permission categories
    permission_categories = Permission.objects.filter(is_active=True).values(
        'category'
    ).annotate(count=Count('id')).order_by('category')
    
    return render(request, 'veteran_app/rbac/dashboard.html', {
        'stats': stats,
        'recent_logs': recent_logs,
        'role_stats': role_stats,
        'permission_categories': permission_categories
    })

@login_required
@user_passes_test(is_superuser)
def manage_roles(request):
    """Manage Roles"""
    roles_list = Role.objects.filter(is_active=True).annotate(
        user_count=Count('role_assignments', filter=Q(role_assignments__is_active=True)),
        permission_count=Count('permissions', filter=Q(permissions__is_active=True))
    ).order_by('name')
    
    paginator = Paginator(roles_list, 20)
    page_number = request.GET.get('page')
    roles = paginator.get_page(page_number)
    
    return render(request, 'veteran_app/rbac/manage_roles.html', {
        'roles': roles,
        'page_obj': roles
    })

@login_required
@user_passes_test(is_superuser)
def create_role(request):
    """Create New Role"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        permission_ids = request.POST.getlist('permissions')
        
        if not name:
            messages.error(request, 'Role name is required.')
            return redirect('manage_roles')
        
        if Role.objects.filter(name=name).exists():
            messages.error(request, 'Role with this name already exists.')
            return redirect('manage_roles')
        
        # Create role
        role = Role.objects.create(
            name=name,
            description=description,
            created_by=request.user,
            is_system_role=False
        )
        
        # Add permissions
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids, is_active=True)
            role.permissions.set(permissions)
        
        # Log action
        log_rbac_action(
            action='create_role',
            user=request.user,
            role=role,
            details={'permission_count': len(permission_ids)},
            request=request
        )
        
        messages.success(request, f'Role "{name}" created successfully!')
        return redirect('manage_roles')
    
    # GET request - show form
    permissions = Permission.objects.filter(is_active=True).order_by('category', 'name')
    permission_categories = permissions.values_list('category', flat=True).distinct()
    
    return render(request, 'veteran_app/rbac/create_role.html', {
        'permissions': permissions,
        'permission_categories': permission_categories
    })

@login_required
@user_passes_test(is_superuser)
def edit_role(request, role_id):
    """Edit Existing Role"""
    role = get_object_or_404(Role, id=role_id, is_active=True)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        permission_ids = request.POST.getlist('permissions')
        
        if not name:
            messages.error(request, 'Role name is required.')
            return redirect('edit_role', role_id=role.id)
        
        if Role.objects.filter(name=name).exclude(id=role.id).exists():
            messages.error(request, 'Role with this name already exists.')
            return redirect('edit_role', role_id=role.id)
        
        # Update role
        old_name = role.name
        role.name = name
        role.description = description
        role.save()
        
        # Update permissions
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids, is_active=True)
            role.permissions.set(permissions)
        else:
            role.permissions.clear()
        
        # Log action
        log_rbac_action(
            action='update_role',
            user=request.user,
            role=role,
            details={
                'old_name': old_name,
                'new_name': name,
                'permission_count': len(permission_ids)
            },
            request=request
        )
        
        messages.success(request, f'Role "{name}" updated successfully!')
        return redirect('manage_roles')
    
    # GET request - show form
    permissions = Permission.objects.filter(is_active=True).order_by('category', 'name')
    permission_categories = permissions.values_list('category', flat=True).distinct()
    role_permissions = role.permissions.filter(is_active=True).values_list('id', flat=True)
    
    return render(request, 'veteran_app/rbac/edit_role.html', {
        'role': role,
        'permissions': permissions,
        'permission_categories': permission_categories,
        'role_permissions': list(role_permissions)
    })

@login_required
@user_passes_test(is_superuser)
def delete_role(request, role_id):
    """Delete Role"""
    role = get_object_or_404(Role, id=role_id, is_active=True)
    
    if role.is_system_role:
        messages.error(request, 'Cannot delete system roles.')
        return redirect('manage_roles')
    
    # Check if role is assigned to users
    active_assignments = UserRole.objects.filter(role=role, is_active=True).count()
    if active_assignments > 0:
        messages.error(request, f'Cannot delete role. It is assigned to {active_assignments} users.')
        return redirect('manage_roles')
    
    if request.method == 'POST':
        role_name = role.name
        role.is_active = False
        role.save()
        
        # Log action
        log_rbac_action(
            action='delete_role',
            user=request.user,
            role=role,
            details={'role_name': role_name},
            request=request
        )
        
        messages.success(request, f'Role "{role_name}" deleted successfully!')
        return redirect('manage_roles')
    
    return render(request, 'veteran_app/rbac/delete_role.html', {
        'role': role,
        'active_assignments': active_assignments
    })

@login_required
@user_passes_test(is_superuser)
def manage_permissions(request):
    """Manage Permissions"""
    permissions_list = Permission.objects.filter(is_active=True).order_by('category', 'name')
    
    # Filter by category
    category_filter = request.GET.get('category')
    if category_filter:
        permissions_list = permissions_list.filter(category=category_filter)
    
    paginator = Paginator(permissions_list, 25)
    page_number = request.GET.get('page')
    permissions = paginator.get_page(page_number)
    
    # Get categories for filter
    categories = Permission.objects.filter(is_active=True).values_list(
        'category', flat=True
    ).distinct().order_by('category')
    
    return render(request, 'veteran_app/rbac/manage_permissions.html', {
        'permissions': permissions,
        'categories': categories,
        'selected_category': category_filter,
        'page_obj': permissions
    })

@login_required
@user_passes_test(is_superuser)
def create_permission(request):
    """Create New Permission"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        codename = request.POST.get('codename', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', '').strip()
        
        if not all([name, codename, category]):
            messages.error(request, 'Name, codename, and category are required.')
            return redirect('manage_permissions')
        
        if Permission.objects.filter(codename=codename).exists():
            messages.error(request, 'Permission with this codename already exists.')
            return redirect('manage_permissions')
        
        # Create permission
        permission = Permission.objects.create(
            name=name,
            codename=codename,
            description=description,
            category=category
        )
        
        # Log action
        log_rbac_action(
            action='grant_permission',
            user=request.user,
            permission=permission,
            details={'created': True},
            request=request
        )
        
        messages.success(request, f'Permission "{name}" created successfully!')
        return redirect('manage_permissions')
    
    # GET request - show form
    categories = Permission.objects.filter(is_active=True).values_list(
        'category', flat=True
    ).distinct().order_by('category')
    
    return render(request, 'veteran_app/rbac/create_permission.html', {
        'categories': categories
    })

@login_required
@user_passes_test(is_superuser)
def user_role_management(request):
    """User Role Assignment Management"""
    # Get all users with their roles
    users_list = User.objects.select_related().prefetch_related(
        'user_roles__role'
    ).annotate(
        role_count=Count('user_roles', filter=Q(user_roles__is_active=True))
    ).order_by('username')
    
    # Filter options
    user_type = request.GET.get('user_type')
    if user_type == 'superuser':
        users_list = users_list.filter(is_superuser=True)
    elif user_type == 'state_admin':
        users_list = users_list.filter(state_profile__isnull=False)
    elif user_type == 'veteran':
        users_list = users_list.filter(veteran_profile__isnull=False)
    elif user_type == 'regular':
        users_list = users_list.filter(
            is_superuser=False,
            state_profile__isnull=True,
            veteran_profile__isnull=True
        )
    
    paginator = Paginator(users_list, 20)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    
    # Get all active roles for assignment
    roles = Role.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'veteran_app/rbac/user_role_management.html', {
        'users': users,
        'roles': roles,
        'selected_user_type': user_type,
        'page_obj': users
    })

@login_required
@user_passes_test(is_superuser)
def assign_user_role(request):
    """Assign Role to User"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        role_id = request.POST.get('role_id')
        notes = request.POST.get('notes', '').strip()
        
        try:
            user = User.objects.get(id=user_id)
            role = Role.objects.get(id=role_id, is_active=True)
            
            # Check if already assigned
            if UserRole.objects.filter(user=user, role=role, is_active=True).exists():
                return JsonResponse({
                    'success': False,
                    'error': f'User already has role "{role.name}"'
                })
            
            # Assign role
            user_role = assign_role(user, role, request.user, notes, request)
            
            return JsonResponse({
                'success': True,
                'message': f'Role "{role.name}" assigned to {user.username} successfully!'
            })
            
        except (User.DoesNotExist, Role.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Invalid user or role'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
@user_passes_test(is_superuser)
def revoke_user_role(request):
    """Revoke Role from User"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        role_id = request.POST.get('role_id')
        
        try:
            user = User.objects.get(id=user_id)
            role = Role.objects.get(id=role_id)
            
            if revoke_role(user, role, request.user, request):
                return JsonResponse({
                    'success': True,
                    'message': f'Role "{role.name}" revoked from {user.username} successfully!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Role assignment not found'
                })
                
        except (User.DoesNotExist, Role.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Invalid user or role'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
@user_passes_test(is_superuser)
def permission_matrix(request):
    """Permission Matrix View"""
    matrix_data = get_permission_matrix()
    
    return render(request, 'veteran_app/rbac/permission_matrix.html', {
        'permissions': matrix_data['permissions'],
        'roles': matrix_data['roles'],
        'matrix': matrix_data['matrix']
    })

@login_required
@user_passes_test(is_superuser)
def update_role_permissions(request):
    """Update Role Permissions via AJAX"""
    if request.method == 'POST':
        role_id = request.POST.get('role_id')
        permission_ids = request.POST.getlist('permissions')
        
        try:
            role = Role.objects.get(id=role_id, is_active=True)
            
            # Update permissions
            if permission_ids:
                permissions = Permission.objects.filter(id__in=permission_ids, is_active=True)
                role.permissions.set(permissions)
            else:
                role.permissions.clear()
            
            # Log action
            log_rbac_action(
                action='update_role',
                user=request.user,
                role=role,
                details={'permission_count': len(permission_ids)},
                request=request
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Permissions updated for role "{role.name}"'
            })
            
        except Role.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Role not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
@user_passes_test(is_superuser)
def audit_logs(request):
    """View Audit Logs"""
    logs_list = RoleAuditLog.objects.select_related(
        'user', 'target_user', 'role', 'permission'
    ).order_by('-timestamp')
    
    # Filters
    action_filter = request.GET.get('action')
    user_filter = request.GET.get('user')
    date_filter = request.GET.get('date')
    
    if action_filter:
        logs_list = logs_list.filter(action=action_filter)
    
    if user_filter:
        logs_list = logs_list.filter(user__username__icontains=user_filter)
    
    if date_filter:
        from datetime import datetime
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            logs_list = logs_list.filter(timestamp__date=filter_date)
        except ValueError:
            pass
    
    paginator = Paginator(logs_list, 25)
    page_number = request.GET.get('page')
    logs = paginator.get_page(page_number)
    
    # Get filter options
    actions = RoleAuditLog.ACTION_CHOICES
    
    return render(request, 'veteran_app/rbac/audit_logs.html', {
        'logs': logs,
        'actions': actions,
        'selected_action': action_filter,
        'selected_user': user_filter,
        'selected_date': date_filter,
        'page_obj': logs
    })

@login_required
@user_passes_test(is_superuser)
def initialize_rbac(request):
    """Initialize RBAC with default roles and permissions"""
    if request.method == 'POST':
        try:
            # Create default permissions
            permissions = create_default_permissions()
            
            # Create default roles
            roles = create_default_roles()
            
            # Log action
            log_rbac_action(
                action='create_role',
                user=request.user,
                details={
                    'initialized': True,
                    'permissions_created': len(permissions),
                    'roles_created': len(roles)
                },
                request=request
            )
            
            messages.success(request, f'RBAC initialized successfully! Created {len(permissions)} permissions and {len(roles)} roles.')
            
        except Exception as e:
            messages.error(request, f'Error initializing RBAC: {str(e)}')
    
    return redirect('rbac_dashboard')

@login_required
@user_passes_test(is_superuser)
def get_user_details(request, user_id):
    """Get user details for modal display"""
    try:
        user = User.objects.get(id=user_id)
        
        # Get user type
        user_type = 'Regular User'
        profile_info = {}
        
        if user.is_superuser:
            user_type = 'Super Administrator'
        elif hasattr(user, 'state_profile'):
            user_type = f'State Admin ({user.state_profile.state.name})'
            profile_info = {
                'state': user.state_profile.state.name,
                'approved': user.state_profile.approved
            }
        elif hasattr(user, 'veteran_profile'):
            user_type = f'Veteran ({user.veteran_profile.veteran_member.name})'
            profile_info = {
                'veteran_name': user.veteran_profile.veteran_member.name,
                'state': user.veteran_profile.veteran_member.state.name,
                'approved': user.veteran_profile.approved
            }
        
        # Get current roles
        current_roles = UserRole.objects.filter(
            user=user, is_active=True
        ).select_related('role').values(
            'role__id', 'role__name', 'assigned_at', 'notes'
        )
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M'),
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never',
                'user_type': user_type,
                'profile_info': profile_info,
                'current_roles': list(current_roles)
            }
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        })