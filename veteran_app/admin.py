# MODELS REGISTRATION.

from django.contrib import admin
from .models import (State, Rank, Branch, BloodGroup, VeteranMember, Message, UserState, 
                     Document, Notification, MedicalCategory, ECHS, DHQ, Child, 
                     JobPortal, Matrimonial, ChatMessage, ChatRequest, VeteranUser, CarouselSlide, AccountsUser)
Group = Branch  # Backward compatibility

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']

@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

# Backward compatibility
GroupAdmin = BranchAdmin

@admin.register(BloodGroup)
class BloodGroupAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(VeteranMember)
class VeteranMemberAdmin(admin.ModelAdmin):
    list_display = ['association_id', 'name', 'association_number', 'state', 'rank', 'service_number', 'approved']
    list_filter = ['state', 'rank', 'branch', 'blood_group', 'approved']
    search_fields = ['name', 'service_number', 'association_number', 'p_number', 'association_id', 'alternate_email', 'contact']
    readonly_fields = ['association_id', 'created_by', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Association Information', {
            'fields': ('association_number', 'association_date', 'membership', 'subscription_ref_no', 'subscription_paid_on', 'renewal_due_date')
        }),
        ('Basic Information', {
            'fields': ('name', 'service_number', 'rank', 'branch', 'state', 'approved')
        }),
        ('Contact Information', {
            'fields': ('contact', 'address', 'living_city', 'zip_code', 'alternate_email')
        }),
        ('System Fields', {
            'fields': ('association_id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'content']

@admin.register(CarouselSlide)
class CarouselSlideAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'subtitle', 'content']
    list_editable = ['order', 'is_active']
    ordering = ['order']

@admin.register(UserState)
class UserStateAdmin(admin.ModelAdmin):
    list_display = ['user', 'state', 'full_name', 'designation', 'approved', 'created_at']
    list_filter = ['approved', 'state', 'created_at']
    search_fields = ['user__username', 'state__name', 'state__code', 'full_name', 'designation']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['approved']
    fieldsets = (
        ('User & State', {
            'fields': ('user', 'state', 'approved')
        }),
        ('State Head Profile', {
            'fields': ('profile_photo', 'full_name', 'designation', 'contact_number', 'email', 'bio')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'state', 'is_important', 'is_public', 'uploaded_by', 'created_at']
    list_filter = ['document_type', 'state', 'is_important', 'is_public', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['uploaded_by', 'created_at', 'updated_at']
    list_editable = ['is_important', 'is_public']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set uploaded_by on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'state', 'is_active', 'created_at', 'expires_at']
    list_filter = ['notification_type', 'state', 'is_active', 'created_at']
    search_fields = ['title', 'message']
    list_editable = ['is_active']

@admin.register(MedicalCategory)
class MedicalCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']

@admin.register(ECHS)
class ECHSAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'state']
    list_filter = ['state']
    search_fields = ['name', 'location']

@admin.register(DHQ)
class DHQAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'state']
    list_filter = ['state']
    search_fields = ['name', 'location']

@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ['child_name', 'veteran', 'child_dob', 'child_qualification', 'searching_for_job', 'searching_for_alliance']
    list_filter = ['searching_for_job', 'searching_for_alliance', 'created_at']
    search_fields = ['child_name', 'veteran__name', 'child_qualification']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(JobPortal)
class JobPortalAdmin(admin.ModelAdmin):
    list_display = ['name', 'applicant_type', 'veteran', 'qualification', 'preferred_location', 'is_active', 'created_at']
    list_filter = ['applicant_type', 'is_active', 'created_at']
    search_fields = ['name', 'qualification', 'skills', 'veteran__name']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']

@admin.register(Matrimonial)
class MatrimonialAdmin(admin.ModelAdmin):
    list_display = ['child', 'veteran', 'gender', 'occupation', 'is_active', 'created_at']
    list_filter = ['gender', 'is_active', 'created_at']
    search_fields = ['child__child_name', 'veteran__name', 'occupation']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'status', 'is_read', 'created_at']
    list_filter = ['status', 'is_read', 'created_at']
    search_fields = ['sender__name', 'receiver__name', 'message']
    readonly_fields = ['created_at']

@admin.register(ChatRequest)
class ChatRequestAdmin(admin.ModelAdmin):
    list_display = ['requester', 'recipient', 'status', 'created_at', 'responded_at']
    list_filter = ['status', 'created_at']
    search_fields = ['requester__name', 'recipient__name']
    readonly_fields = ['created_at']

@admin.register(VeteranUser)
class VeteranUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'veteran_member', 'approved', 'created_by_admin', 'created_at']
    list_filter = ['approved', 'created_by_admin', 'created_at']
    search_fields = ['user__username', 'veteran_member__name', 'veteran_member__p_number']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['approved']

@admin.register(AccountsUser)
class AccountsUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'designation', 'approved', 'created_at']
    list_filter = ['approved', 'created_at']
    search_fields = ['user__username', 'full_name', 'designation', 'email']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['approved']
    fieldsets = (
        ('User & Access', {
            'fields': ('user', 'approved')
        }),
        ('Profile Information', {
            'fields': ('full_name', 'designation', 'contact_number', 'email')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )