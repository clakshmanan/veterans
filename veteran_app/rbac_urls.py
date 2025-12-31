from django.urls import path
from . import rbac_views

rbac_urlpatterns = [
    # RBAC Dashboard
    path('rbac/', rbac_views.rbac_dashboard, name='rbac_dashboard'),
    
    # Role Management
    path('rbac/roles/', rbac_views.manage_roles, name='manage_roles'),
    path('rbac/roles/create/', rbac_views.create_role, name='create_role'),
    path('rbac/roles/<int:role_id>/edit/', rbac_views.edit_role, name='edit_role'),
    path('rbac/roles/<int:role_id>/delete/', rbac_views.delete_role, name='delete_role'),
    
    # Permission Management
    path('rbac/permissions/', rbac_views.manage_permissions, name='manage_permissions'),
    path('rbac/permissions/create/', rbac_views.create_permission, name='create_permission'),
    
    # User Role Assignment
    path('rbac/users/', rbac_views.user_role_management, name='user_role_management'),
    path('rbac/users/assign-role/', rbac_views.assign_user_role, name='assign_user_role'),
    path('rbac/users/revoke-role/', rbac_views.revoke_user_role, name='revoke_user_role'),
    path('rbac/users/<int:user_id>/details/', rbac_views.get_user_details, name='get_user_details'),
    
    # Permission Matrix
    path('rbac/matrix/', rbac_views.permission_matrix, name='permission_matrix'),
    path('rbac/matrix/update/', rbac_views.update_role_permissions, name='update_role_permissions'),
    
    # Audit Logs
    path('rbac/audit/', rbac_views.audit_logs, name='rbac_audit_logs'),
    
    # Initialize RBAC
    path('rbac/initialize/', rbac_views.initialize_rbac, name='initialize_rbac'),
]