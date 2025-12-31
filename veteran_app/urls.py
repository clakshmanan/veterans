from django.urls import path
from . import views
from .rbac_urls import rbac_urlpatterns

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('services/', views.services, name='services'),
    path('login/', views.login_view, name='login'),
    
    # State and Member Management
    path('state/<int:state_id>/dashboard/', views.state_dashboard, name='state_dashboard'),
    path('state/<int:state_id>/members/', views.state_members, name='state_members'),
    path('state/<int:state_id>/add-member/', views.add_member, name='add_member'),
    path('member/<int:member_id>/edit/', views.edit_member, name='edit_member'),
    path('member/<int:member_id>/delete/', views.delete_member, name='delete_member'),
    path('member/<int:member_id>/approve/', views.approve_member, name='approve_member'),
    path('member/<int:member_id>/disapprove/', views.disapprove_member, name='disapprove_member'),
    path('member/<int:member_id>/download/', views.download_document, name='download_document'),
    path('state/<int:state_id>/download/', views.download_members, name='download_members'),
    
    # Data Management (Superuser only)
    path('manage-data/', views.manage_data, name='manage_data'),
    path('add-rank/', views.add_rank, name='add_rank'),
    path('delete-rank/<int:rank_id>/', views.delete_rank, name='delete_rank'),
    path('add-branch/', views.add_branch, name='add_branch'),
    path('delete-branch/<int:branch_id>/', views.delete_branch, name='delete_branch'),
    # Backward compatibility
    path('add-group/', views.add_group, name='add_group'),
    path('delete-group/<int:group_id>/', views.delete_group, name='delete_group'),
    
    # Carousel Management (Superuser only)
    path('manage-carousel/', views.manage_carousel, name='manage_carousel'),
    path('add-carousel-slide/', views.add_carousel_slide, name='add_carousel_slide'),
    path('edit-carousel-slide/<int:slide_id>/', views.edit_carousel_slide, name='edit_carousel_slide'),
    path('delete-carousel-slide/<int:slide_id>/', views.delete_carousel_slide, name='delete_carousel_slide'),
    
    # User Management (Superuser only)
    path('manage-users/', views.manage_users, name='manage_users'),
    path('approve-user/<int:user_state_id>/', views.approve_user, name='approve_user'),
    path('disapprove-user/<int:user_state_id>/', views.disapprove_user, name='disapprove_user'),
    
    # Password Reset Management (Superuser only)
    path('password-reset-admin/', views.password_reset_admin, name='password_reset_admin'),
    path('reset-user-password/', views.reset_user_password, name='reset_user_password'),
    
    # Treasurer Financial Management (Superuser only)
    path('treasurer-dashboard/', views.treasurer_dashboard, name='treasurer_dashboard'),
    path('add-transaction/', views.add_transaction, name='add_transaction'),
    path('transaction-list/', views.transaction_list, name='transaction_list'),
    path('transaction-detail/<int:transaction_id>/', views.transaction_detail, name='transaction_detail'),
    path('delete-transaction/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    path('generate-report/', views.generate_report, name='generate_report'),
    path('export-transactions/', views.export_transactions, name='export_transactions'),
    
    # User Profile and Settings
    path('profile/', views.user_profile, name='user_profile'),
    path('settings/', views.user_settings, name='user_settings'),
    path('change-password/', views.change_password, name='change_password'),
    path('update-preferences/', views.update_preferences, name='update_preferences'),
    
    # Media & Documents
    path('media/', views.media_documents, name='media_documents'),
    path('media/upload/', views.upload_document, name='upload_document'),
    path('media/view/<int:doc_id>/', views.view_document, name='view_document'),
    path('media/download/<int:doc_id>/', views.download_document_file, name='download_document_file'),
    path('media/delete/<int:doc_id>/', views.delete_document, name='delete_document'),
    
    # Veteran User Management
    path('veteran-register/', views.veteran_register, name='veteran_register'),
    path('veteran-welcome/', views.veteran_welcome, name='veteran_welcome'),
    path('veteran-dashboard/', views.veteran_dashboard, name='veteran_dashboard'),
    path('veteran-profile-edit/', views.veteran_profile_edit, name='veteran_profile_edit'),
    path('state/<int:state_id>/create-veteran-user/', views.create_veteran_user, name='create_veteran_user'),
    path('state/<int:state_id>/manage-veteran-users/', views.manage_veteran_users, name='manage_veteran_users'),
    path('approve-veteran-user/<int:veteran_user_id>/', views.approve_veteran_user, name='approve_veteran_user'),
    path('disapprove-veteran-user/<int:veteran_user_id>/', views.disapprove_veteran_user, name='disapprove_veteran_user'),
    path('veteran-profile-detail/', views.veteran_profile_detail, name='veteran_profile_detail'),
    
    # Portal Features
    path('job-portal/', views.job_portal, name='job_portal'),
    path('job-portal/add/', views.job_portal_add, name='job_portal_add'),
    path('job-portal/edit/<int:job_id>/', views.job_portal_edit, name='job_portal_edit'),
    path('job-portal/delete/<int:job_id>/', views.job_portal_delete, name='job_portal_delete'),
    path('job-portal/admin/', views.admin_job_portal, name='admin_job_portal'),
    path('job-portal/details/<int:job_id>/', views.job_application_details, name='job_application_details'),
    path('matrimonial-portal/', views.matrimonial_portal, name='matrimonial_portal'),
    path('matrimonial-portal/add/', views.matrimonial_add, name='matrimonial_add'),
    path('matrimonial-portal/edit/<int:profile_id>/', views.matrimonial_edit, name='matrimonial_edit'),
    path('matrimonial-portal/delete/<int:profile_id>/', views.matrimonial_delete, name='matrimonial_delete'),
    path('chat-portal/', views.chat_portal, name='chat_portal'),
    path('chat-request/<int:veteran_id>/', views.send_chat_request, name='send_chat_request'),
    path('chat-request/accept/<int:request_id>/', views.accept_chat_request, name='accept_chat_request'),
    path('chat-request/reject/<int:request_id>/', views.reject_chat_request, name='reject_chat_request'),
    path('manage-children/', views.manage_children, name='manage_children'),
    path('child/<int:child_id>/edit/', views.edit_child, name='edit_child'),
    path('child/<int:child_id>/delete/', views.delete_child, name='delete_child'),
    path('post-announcement/', views.post_announcement, name='post_announcement'),


    # Event Management
    path('events/', views.events_list, name='events_list'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('events/<int:event_id>/register/', views.register_for_event, name='register_for_event'),
    path('manage-events/', views.manage_events, name='manage_events'),
    path('create-event/', views.create_event, name='create_event'),
    path('edit-event/<int:event_id>/', views.edit_event, name='edit_event'),
    path('delete-event/<int:event_id>/', views.delete_event, name='delete_event'),
    
    # Payment Integration
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('payment-settings/', views.payment_settings, name='payment_settings'),
    
    # Two-Factor Authentication
    path('setup-2fa/', views.setup_2fa, name='setup_2fa'),
    path('verify-2fa/', views.verify_2fa, name='verify_2fa'),
    path('backup-codes/', views.view_backup_codes, name='view_backup_codes'),
    path('regenerate-backup-codes/', views.regenerate_backup_codes, name='regenerate_backup_codes'),
    
    # Reporting System
    path('reports/', views.reports_builder, name='reports_builder'),
    path('reports/generate/', views.generate_report, name='generate_report'),
    path('reports/save-config/', views.save_report_config, name='save_report_config'),
    path('reports/load-config/<int:config_id>/', views.load_report_config, name='load_report_config'),
    
    # Gallery
    path('gallery/', views.gallery, name='gallery'),
    path('gallery/upload/', views.upload_gallery_image, name='upload_gallery_image'),
    path('gallery/delete/<int:image_id>/', views.delete_gallery_image, name='delete_gallery_image'),
    
    # Veteran Payment CRUD
    path('veteran-payment/add/', views.veteran_add_payment, name='veteran_add_payment'),
    path('veteran-payment/edit/<int:transaction_id>/', views.veteran_edit_payment, name='veteran_edit_payment'),
    path('veteran-payment/delete/<int:transaction_id>/', views.veteran_delete_payment, name='veteran_delete_payment'),
    
    # Association ID Card
    path('association-id-card/', views.association_id_card, name='association_id_card'),
    path('download-id-card/', views.download_id_card, name='download_id_card'),
]

# Add RBAC URLs
urlpatterns += rbac_urlpatterns