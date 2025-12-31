# Models of the veteran_application

import os
from datetime import date, timedelta
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import json
from .validators import (
    validate_phone_number,
    validate_image_extension,
    validate_file_extension,
    validate_file_size,
    validate_resume_extension
)

# RBAC MODELS
class Permission(models.Model):
    """Individual permission that can be granted to roles"""
    name = models.CharField(max_length=100, unique=True)
    codename = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, default='general')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category})"

class Role(models.Model):
    """Custom roles that can be assigned to users"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    is_system_role = models.BooleanField(default=False)  # Built-in roles
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_roles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_permission_count(self):
        return self.permissions.count()

class UserRole(models.Model):
    """Assignment of roles to users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_roles')
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['user', 'role']
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

class RoleAuditLog(models.Model):
    """Audit trail for role and permission changes"""
    ACTION_CHOICES = [
        ('create_role', 'Role Created'),
        ('update_role', 'Role Updated'),
        ('delete_role', 'Role Deleted'),
        ('assign_role', 'Role Assigned'),
        ('revoke_role', 'Role Revoked'),
        ('grant_permission', 'Permission Granted'),
        ('revoke_permission', 'Permission Revoked'),
    ]
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='rbac_actions_performed')
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rbac_actions_received')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    permission = models.ForeignKey(Permission, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_action_display()} by {self.user.username if self.user else 'System'}"

def get_upload_path(instance, filename):
    """Generate upload path based on file extension"""
    ext = filename.split('.')[-1].lower()
    
    # Define file type categories
    pdf_extensions = ['pdf']
    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg']
    office_extensions = ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp']
    
    # Determine subdirectory based on file type
    if ext in pdf_extensions:
        subdir = 'pdf'
    elif ext in image_extensions:
        subdir = 'images'
    elif ext in office_extensions:
        subdir = 'office'
    else:
        subdir = 'other'
    
    # Create path: documents/category/year/month/filename
    from datetime import datetime
    now = datetime.now()
    return f'documents/{subdir}/{now.year}/{now.month:02d}/{filename}'

class State(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=5, unique=True)
    
    def __str__(self):
        return self.name

class Rank(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class BloodGroup(models.Model):
    name = models.CharField(max_length=5, unique=True)
    
    def __str__(self):
        return self.name

class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    class Meta:
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'
    
    def __str__(self):
        return self.name

# Backward compatibility alias
Group = Branch

class MedicalCategory(models.Model):
    """Medical categories for veterans (S1A1, S2A2, etc.)"""
    name = models.CharField(max_length=20, unique=True, help_text='e.g., S1A1, S2A2, S3A3')
    description = models.TextField(blank=True, help_text='Description of medical category')
    
    class Meta:
        verbose_name = 'Medical Category'
        verbose_name_plural = 'Medical Categories'
    
    def __str__(self):
        return self.name

class ECHS(models.Model):
    """Ex-Servicemen Contributory Health Scheme centers"""
    name = models.CharField(max_length=200, unique=True)
    location = models.CharField(max_length=200, blank=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        verbose_name = 'ECHS Center'
        verbose_name_plural = 'ECHS Centers'
    
    def __str__(self):
        return self.name

class DHQ(models.Model):
    """District Headquarters for service support"""
    name = models.CharField(max_length=200, unique=True)
    location = models.CharField(max_length=200, blank=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        verbose_name = 'District Headquarters'
        verbose_name_plural = 'District Headquarters'
    
    def __str__(self):
        return self.name

class VeteranMember(models.Model):
    association_id = models.AutoField(primary_key=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    enrolled_date = models.DateField(verbose_name='Course Completed Date', help_text='Date when educational qualification/course was completed')
    
    # PERSONAL INFORMATION
    profile_photo = models.ImageField(
        upload_to='profiles/%Y/%m/', 
        null=True, 
        blank=True,
        validators=[validate_image_extension, validate_file_size],
        help_text='Upload profile photo (JPG, PNG, max 5MB)'
    )
    name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    contact = models.CharField(max_length=15, validators=[validate_phone_number], help_text='10-digit mobile number')
    address = models.TextField()
    alternate_email = models.EmailField(blank=True, help_text='Secondary email address')
    educational_qualification = models.CharField(max_length=200, blank=True, help_text='Highest educational qualification')
    living_city = models.CharField(max_length=100, blank=True, help_text='Current city of residence')
    zip_code = models.CharField(max_length=10, blank=True, help_text='Postal/ZIP code')
    
    # EMERGENCY CONTACT
    emergency_contact_name = models.CharField(max_length=200, blank=True, help_text='Emergency contact person')
    emergency_contact_phone = models.CharField(max_length=15, blank=True, validators=[validate_phone_number], help_text='Emergency contact number')
    nearest_veteran_contact = models.CharField(max_length=15, blank=True, validators=[validate_phone_number], help_text='Nearest veteran contact number')
    
    # MEDICAL INFORMATION
    blood_group = models.ForeignKey(BloodGroup, on_delete=models.CASCADE)
    medical_category = models.ForeignKey(MedicalCategory, on_delete=models.SET_NULL, null=True, blank=True, default=None, help_text='Medical category (default: S1A1)')
    medical_category_text = models.CharField(max_length=100, blank=True, null=True, verbose_name='Medical Category (Custom)', help_text='Enter custom medical category if not in dropdown')
    disabilities = models.TextField(blank=True, help_text='Service-related disabilities')
    nearest_echs = models.ForeignKey(ECHS, on_delete=models.SET_NULL, null=True, blank=True, help_text='Nearest ECHS center')
    nearest_echs_text = models.CharField(max_length=200, blank=True, null=True, verbose_name='Nearest ECHS (Custom)', help_text='Enter custom ECHS center if not in dropdown')
    insurance_details = models.TextField(blank=True, help_text='Medical insurance information')
    medical_conditions = models.TextField(blank=True, help_text='Known medical conditions')
    
    # MILITARY INFORMATION
    # Legacy P-Number field (kept for backward compatibility, use association_number instead)
    p_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='Legacy Assn. Number (Deprecated)', help_text='Legacy field - use Association Number instead')
    service_number = models.CharField(max_length=50, unique=True, verbose_name='Service Number', help_text='Military service number (unique)')
    rank = models.ForeignKey(Rank, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='members')
    date_of_joining = models.DateField(verbose_name='Date of Joining')
    retired_on = models.DateField(verbose_name='Date of Retirement')
    specialization = models.TextField(blank=True, null=True, help_text='Area of expertise/specialization')
    decorations = models.TextField(blank=True, null=True, verbose_name='Awards & Decorations', help_text='Awards, medals, and decorations received')
    deployment_history = models.TextField(blank=True, null=True, help_text='Brief deployment history')
    unit_served = models.CharField(max_length=200, verbose_name='Last Ship Served', help_text='Last unit/ship served')
    nearest_dhq_text = models.CharField(max_length=200, verbose_name='Nearest ECHS', help_text='Enter Nearest ECHS')
    
    # ASSOCIATION INFORMATION
    association_number = models.CharField(max_length=30, unique=True, blank=True, null=True, verbose_name='Association Number', help_text='Unique association identity number')
    association_date = models.DateField()
    membership = models.BooleanField(default=False, verbose_name='Active Membership')
    subscription_ref_no = models.CharField(max_length=100, blank=True, null=True, verbose_name='Subscription Ref.No', help_text='Subscription reference number (mandatory for new registrations)')
    subscription_paid_on = models.DateField(null=True, blank=True)
    subscription_due = models.DateField(null=True, blank=True, editable=False)
    renewal_due_date = models.DateField(null=True, blank=True, editable=False, help_text='ID card renewal due date (1 year from registration)')
    document = models.FileField(
        upload_to=get_upload_path, 
        null=True, 
        blank=True,
        validators=[validate_file_extension, validate_file_size],
        help_text='Subscription payment document (PDF, DOC, DOCX, JPG, PNG, max 5MB)'
    )
    searching_for_job = models.BooleanField(default=False, help_text='Looking for job opportunities')
    
    # FAMILY DETAILS - SPOUSE
    spouse_name = models.CharField(max_length=200, help_text='Spouse full name')
    spouse_contact = models.CharField(max_length=15, blank=True, null=True, validators=[validate_phone_number], help_text='Spouse contact number')
    spouse_employed = models.CharField(max_length=200, blank=True, null=True, help_text='Spouse employment details')
    spouse_medical_details = models.TextField(blank=True, null=True, help_text='Spouse medical information')
    
    # Legacy fields for backward compatibility
    children_count = models.PositiveIntegerField(default=0, help_text='Number of children')
    
    # Welfare Information
    pension_details = models.TextField(blank=True, help_text='Pension scheme details')
    bank_account = models.CharField(max_length=100, blank=True, help_text='Bank account number')
    bank_name = models.CharField(max_length=200, blank=True, help_text='Bank name and branch')
    welfare_schemes = models.TextField(blank=True, help_text='Enrolled welfare programs')
    next_of_kin = models.CharField(max_length=200, blank=True, help_text='Next of kin/legal heir')
    next_of_kin_relation = models.CharField(max_length=50, blank=True, help_text='Relationship with next of kin')
    next_of_kin_contact = models.CharField(max_length=15, blank=True, validators=[validate_phone_number], help_text='Next of kin contact number')
    
    # System fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_members')
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        # Prefer service_number when available, fall back to Assn. Number (p_number) for legacy records
        sn = self.service_number or getattr(self, 'p_number', 'N/A')
        return f"{self.name} ({sn})"

    def clean(self):
        """DB-level enforcement: non-superusers can only associate members with their own state
        based on their username pattern 'state_{CODE}'. This uses only fields on the model
        (created_by and state) and does not depend on the request object.
        """
        super().clean()
        # During ModelForm validation, full_clean() is called BEFORE the view sets created_by.
        # In that case, skip this check and let the final save() (after view sets created_by)
        # enforce the constraint.
        # IMPORTANT: use created_by_id to avoid RelatedObjectDoesNotExist during validation
        user_id = getattr(self, 'created_by_id', None)
        if not user_id:
            return
        # Only fetch user object when id is present
        try:
            user = self.created_by
            if user.is_superuser:
                return
            username = (user.username or '').lower()
            if username.startswith('state_'):
                code = username.split('state_', 1)[1].upper()
                if not self.state or self.state.code != code:
                    raise ValidationError({
                        "state": (
                            "You are not authorized to create or modify members for this state. "
                            "Please select your assigned state."
                        )
                    })
        except Exception:
            # Skip validation if there are any issues with user lookup
            pass

        # Validate service_number format: digits-hyphen-letter (e.g., 12345-A)
        if self.service_number:
            import re
            if not re.fullmatch(r"\d+-[A-Za-z]", self.service_number):
                raise ValidationError({
                    'service_number': 'Invalid Service Number format. Expected digits-hyphen-letter (e.g., 12345-A).'
                })

    def save(self, *args, **kwargs):
        # Generate association number if not exists
        if not self.association_number:
            self.generate_association_number()
        
        # Set renewal due date
        if self.association_date and not self.renewal_due_date:
            self.renewal_due_date = self.get_renewal_due_date()
        
        # Ensure validation is always applied when saving via code or admin
        self.full_clean()
        return super().save(*args, **kwargs)
    
    def get_subscription_due_date(self):
        """Calculate subscription due date (365 days from subscription_paid_on)"""
        if self.subscription_paid_on:
            return self.subscription_paid_on + timedelta(days=365)
        return None
    
    def get_renewal_due_date(self):
        """Calculate ID card renewal due date (1 year from association_date)"""
        if self.association_date:
            return self.association_date + timedelta(days=365)
        return None
    
    def is_id_card_valid(self):
        """Check if ID card is still valid (not expired)"""
        renewal_due = self.get_renewal_due_date()
        if renewal_due:
            return date.today() <= renewal_due
        return False
    
    def generate_association_number(self):
        """Generate unique association number in format ICGVWA/STATE_CODE/00001
        Once allocated, this number will never be changed or reused.
        """
        if not self.association_number and self.state:
            # Get the highest sequence number for this state to ensure uniqueness
            from django.db.models import Max
            import re
            
            # Find all existing association numbers for this state
            existing_numbers = VeteranMember.objects.filter(
                state=self.state,
                association_number__isnull=False,
                association_number__startswith=f"ICGVWA/{self.state.code}/"
            ).values_list('association_number', flat=True)
            
            # Extract sequence numbers and find the maximum
            max_sequence = 0
            for number in existing_numbers:
                match = re.search(r'ICGVWA/' + re.escape(self.state.code) + r'/(\d+)$', number)
                if match:
                    sequence = int(match.group(1))
                    if sequence > max_sequence:
                        max_sequence = sequence
            
            # Generate next sequence number
            next_sequence = max_sequence + 1
            self.association_number = f"ICGVWA/{self.state.code}/{next_sequence:05d}"
            
            # Ensure uniqueness by checking if this number already exists
            while VeteranMember.objects.filter(association_number=self.association_number).exclude(pk=self.pk).exists():
                next_sequence += 1
                self.association_number = f"ICGVWA/{self.state.code}/{next_sequence:05d}"
        
        return self.association_number
    
    def get_verification_url(self):
        """Get verification URL for QR code"""
        from django.urls import reverse
        if self.association_number:
            return f"https://icgvwa.org/verify/{self.association_number}"
        return None
    
    def get_qr_code_data(self):
        """Get data for QR code generation"""
        return {
            'association_number': self.association_number,
            'name': self.name,
            'rank': self.rank.name,
            'state': self.state.name,
            'verification_url': self.get_verification_url(),
            'valid_until': self.get_renewal_due_date().strftime('%Y-%m-%d') if self.get_renewal_due_date() else None
        }
    
    def get_subscription_status(self):
        """Get subscription status with color coding"""
        due_date = self.get_subscription_due_date()
        if not due_date:
            return {'status': 'No Payment', 'color': 'secondary'}
        
        today = date.today()
        days_diff = (due_date - today).days
        
        if days_diff > 15:
            return {'status': 'Active', 'color': 'success'}
        elif days_diff >= -15:  # 15 days grace period
            return {'status': 'Due Soon', 'color': 'warning'}
        else:
            return {'status': 'Overdue', 'color': 'danger'}
    
    def has_user_account(self):
        """Check if veteran has a user account"""
        try:
            return hasattr(self, 'user_account')
        except:
            return False
    
    def get_profile_photo_url(self):
        """Get profile photo URL or default placeholder"""
        if self.profile_photo:
            return self.profile_photo.url
        return '/static/images/veterans/veteran1.svg'
    
    def get_full_service_info(self):
        """Get comprehensive service information"""
        info = {
            'rank': self.rank.name,
            'branch': self.branch.name,
            'service_number': self.service_number or 'Not provided',
            'unit_served': self.unit_served or 'Not provided',
            'specialization': self.specialization or 'Not provided'
        }
        return info

class UserState(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='state_profile')
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    approved = models.BooleanField(default=False, help_text='Approved by superadmin to access the system')
    
    # State Head Profile Information
    profile_photo = models.ImageField(
        upload_to='state_heads/%Y/', 
        null=True, 
        blank=True,
        validators=[validate_image_extension, validate_file_size],
        help_text='State head profile photo (JPG, PNG, max 5MB)'
    )
    full_name = models.CharField(max_length=200, blank=True, help_text='Full name of state head')
    designation = models.CharField(max_length=100, blank=True, help_text='e.g., State President, State Secretary')
    contact_number = models.CharField(max_length=15, blank=True, validators=[validate_phone_number], help_text='Contact number')
    email = models.EmailField(blank=True, help_text='Official email')
    bio = models.TextField(blank=True, help_text='Brief bio or message')
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} -> {self.state.code} ({'Approved' if self.approved else 'Pending'})"
    
    class Meta:
        verbose_name = 'User State Assignment'
        verbose_name_plural = 'User State Assignments'

class AccountsUser(models.Model):
    """Accounts user for financial management - Treasurer and Reports only"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='accounts_profile')
    approved = models.BooleanField(default=False, help_text='Approved by superadmin to access accounts')
    full_name = models.CharField(max_length=200, blank=True, help_text='Full name of accounts user')
    designation = models.CharField(max_length=100, default='Accounts Manager', help_text='e.g., Treasurer, Accounts Manager')
    contact_number = models.CharField(max_length=15, blank=True, validators=[validate_phone_number], help_text='Contact number')
    email = models.EmailField(blank=True, help_text='Official email')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - Accounts ({'Approved' if self.approved else 'Pending'})"
    
    class Meta:
        verbose_name = 'Accounts User'
        verbose_name_plural = 'Accounts Users'

class VeteranUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='veteran_profile')
    veteran_member = models.OneToOneField(VeteranMember, on_delete=models.CASCADE, related_name='user_account')
    approved = models.BooleanField(default=False, help_text='Approved by state admin')
    created_by_admin = models.BooleanField(default=False, help_text='Created by state admin')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} -> {self.veteran_member.name} ({'Approved' if self.approved else 'Pending'})"
    
    class Meta:
        verbose_name = 'Veteran User Account'
        verbose_name_plural = 'Veteran User Accounts'

class Message(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class CarouselSlide(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300)
    content = models.TextField()
    image = models.ImageField(
        upload_to='carousel/', 
        null=True, 
        blank=True,
        validators=[validate_image_extension, validate_file_size]
    )
    icon_class = models.CharField(max_length=50, default='fas fa-info-circle', help_text='FontAwesome icon class')
    background_color = models.CharField(max_length=50, default='bg-gradient-primary')
    order = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.title

class Document(models.Model):
    """Documents and media files for veterans"""
    DOCUMENT_TYPES = [
        ('circular', 'Circular'),
        ('notification', 'Notification'),
        ('form', 'Form'),
        ('guideline', 'Guideline'),
        ('policy', 'Policy Document'),
        ('announcement', 'Announcement'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=300, help_text='Document title')
    description = models.TextField(blank=True, help_text='Brief description of the document')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, default='notification')
    file = models.FileField(
        upload_to='documents/%Y/%m/',
        validators=[validate_file_extension, validate_file_size],
        help_text='Upload PDF, DOC, or image files (max 5MB)'
    )
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True, blank=True, 
                              help_text='Leave blank for all states, or select specific state')
    is_public = models.BooleanField(default=True, help_text='Visible to all users')
    is_important = models.BooleanField(default=False, help_text='Mark as important/urgent')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_important', '-created_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents & Media'
    
    def __str__(self):
        return f"{self.title} ({self.get_document_type_display()})"
    
    def get_file_extension(self):
        """Get file extension for icon display"""
        import os
        return os.path.splitext(self.file.name)[1].lower()
    
    def get_file_size(self):
        """Get human-readable file size"""
        try:
            size = self.file.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return "Unknown"

class Notification(models.Model):
    """System notifications for users"""
    NOTIFICATION_TYPES = [
        ('info', 'General_Info'),
        ('warning', 'Policy_Info'),
        ('success', 'Celebration_Info'),
        ('urgent', 'Obituary'),
    ]
    
    title = models.CharField(max_length=300)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True, blank=True,
                              help_text='Leave blank for all states')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text='Notification expiry date')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.title} ({self.get_notification_type_display()})"
    
    def is_expired(self):
        """Check if notification has expired"""
        from django.utils import timezone
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

class Child(models.Model):
    """Children details for veterans"""
    veteran = models.ForeignKey(VeteranMember, on_delete=models.CASCADE, related_name='children')
    child_photo = models.ImageField(
        upload_to='children/%Y/%m/', 
        null=True, 
        blank=True,
        validators=[validate_image_extension, validate_file_size],
        help_text='Child photo (JPG, PNG, max 5MB)'
    )
    child_name = models.CharField(max_length=200)
    child_dob = models.DateField(verbose_name='Date of Birth')
    child_qualification = models.CharField(max_length=200, blank=True, help_text='Educational qualification')
    specialization = models.CharField(max_length=200, blank=True, help_text='Area of specialization if any')
    searching_for_job = models.BooleanField(default=False, help_text='Looking for job opportunities')
    searching_for_alliance = models.BooleanField(default=False, help_text='Looking for matrimonial alliance')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Child'
        verbose_name_plural = 'Children'
        ordering = ['child_dob']
    
    def __str__(self):
        return f"{self.child_name} - {self.veteran.name}"
    
    def get_age(self):
        """Calculate child's age"""
        from datetime import date
        today = date.today()
        return today.year - self.child_dob.year - ((today.month, today.day) < (self.child_dob.month, self.child_dob.day))

class JobPortal(models.Model):
    """Job portal for veterans and their children"""
    APPLICANT_TYPE_CHOICES = [
        ('veteran', 'Veteran'),
        ('child', 'Veteran Child'),
    ]
    
    applicant_type = models.CharField(max_length=20, choices=APPLICANT_TYPE_CHOICES)
    veteran = models.ForeignKey(VeteranMember, on_delete=models.CASCADE, related_name='job_applications')
    child = models.ForeignKey(Child, on_delete=models.CASCADE, null=True, blank=True, related_name='job_applications')
    
    # Applicant details
    name = models.CharField(max_length=200)
    contact = models.CharField(max_length=15, validators=[validate_phone_number])
    email = models.EmailField(blank=True)
    qualification = models.CharField(max_length=200)
    specialization = models.CharField(max_length=200, blank=True)
    experience = models.TextField(blank=True, help_text='Work experience details')
    skills = models.TextField(blank=True, help_text='Key skills')
    preferred_location = models.CharField(max_length=200, blank=True)
    resume = models.FileField(
        upload_to='resumes/%Y/%m/', 
        null=True, 
        blank=True,
        validators=[validate_resume_extension, validate_file_size],
        help_text='Upload resume (PDF, DOC, DOCX, max 5MB)'
    )
    
    is_active = models.BooleanField(default=True, help_text='Active job seeker')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Job Portal Entry'
        verbose_name_plural = 'Job Portal'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_applicant_type_display()}"

class Matrimonial(models.Model):
    """Matrimonial portal for veterans' children"""
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    child = models.OneToOneField(Child, on_delete=models.CASCADE, related_name='matrimonial_profile', null=True, blank=True)
    child_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='Child Name', help_text='Enter child name if not in dropdown')
    veteran = models.ForeignKey(VeteranMember, on_delete=models.CASCADE, related_name='matrimonial_profiles')
    
    # Profile details
    photo = models.ImageField(
        upload_to='matrimonial/%Y/%m/', 
        null=True, 
        blank=True,
        validators=[validate_image_extension, validate_file_size],
        help_text='Profile photo (JPG, PNG, max 5MB)'
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    height = models.CharField(max_length=20, blank=True, help_text='Height in cm or feet')
    religion = models.CharField(max_length=100, blank=True)
    caste = models.CharField(max_length=100, blank=True)
    occupation = models.CharField(max_length=200, blank=True)
    annual_income = models.CharField(max_length=100, blank=True)
    about = models.TextField(blank=True, help_text='Brief description')
    expectations = models.TextField(blank=True, help_text='Partner expectations')
    contact_person = models.CharField(max_length=200, blank=True, help_text='Contact person name')
    contact_number = models.CharField(max_length=15, blank=True, validators=[validate_phone_number])
    
    is_active = models.BooleanField(default=True, help_text='Active profile')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Matrimonial Profile'
        verbose_name_plural = 'Matrimonial Profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        name = self.child_name if self.child_name else (self.child.child_name if self.child else 'Unknown')
        return f"{name} - {self.get_gender_display()}"

class ChatMessage(models.Model):
    """Chat messages between veterans across states"""
    MESSAGE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    sender = models.ForeignKey(VeteranMember, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(VeteranMember, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    status = models.CharField(max_length=20, choices=MESSAGE_STATUS_CHOICES, default='pending')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.name} -> {self.receiver.name}: {self.message[:50]}"

class ChatRequest(models.Model):
    """Chat requests between veterans from different states"""
    REQUEST_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    requester = models.ForeignKey(VeteranMember, on_delete=models.CASCADE, related_name='chat_requests_sent')
    recipient = models.ForeignKey(VeteranMember, on_delete=models.CASCADE, related_name='chat_requests_received')
    message = models.TextField(blank=True, help_text='Initial message or reason for contact')
    status = models.CharField(max_length=20, choices=REQUEST_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Chat Request'
        verbose_name_plural = 'Chat Requests'
        ordering = ['-created_at']
        unique_together = ['requester', 'recipient']
    
    def __str__(self):
        return f"{self.requester.name} -> {self.recipient.name} ({self.status})"

class FinancialYear(models.Model):
    """Financial year management"""
    year = models.CharField(max_length=9, unique=True, help_text='e.g., 2024-2025')
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return self.year

class SubscriptionPlan(models.Model):
    """Subscription plans for different member types"""
    name = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - ₹{self.amount}"

class Transaction(models.Model):
    """Financial transactions"""
    TRANSACTION_TYPES = [
        ('subscription', 'Subscription Payment'),
        ('donation', 'Donation'),
        ('expense', 'Expense'),
        ('refund', 'Refund'),
        ('other_income', 'Other Income'),
        ('event_fee', 'Event Fee'),
        ('crowdfunding', 'Crowd Funding'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
    ]
    
    transaction_id = models.CharField(max_length=50, unique=True)
    veteran = models.ForeignKey(VeteranMember, on_delete=models.CASCADE, null=True, blank=True, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_number = models.CharField(max_length=100, blank=True, help_text='Cheque/UPI/Bank reference')
    description = models.TextField(blank=True)
    receipt = models.FileField(
        upload_to='receipts/%Y/%m/', 
        null=True, 
        blank=True,
        validators=[validate_file_extension, validate_file_size]
    )
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    recorded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_id} - ₹{self.amount}"

class ExpenseCategory(models.Model):
    """Categories for expenses"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'Expense Categories'
    
    def __str__(self):
        return self.name

class Expense(models.Model):
    """Association expenses"""
    expense_id = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    bill_receipt = models.FileField(
        upload_to='expenses/%Y/%m/', 
        null=True, 
        blank=True,
        validators=[validate_file_extension, validate_file_size]
    )
    vendor_name = models.CharField(max_length=200, blank=True)
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approved_expenses')
    recorded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recorded_expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.expense_id} - ₹{self.amount}"

class BankAccount(models.Model):
    """Association bank accounts"""
    account_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50, unique=True)
    bank_name = models.CharField(max_length=200)
    branch = models.CharField(max_length=200)
    ifsc_code = models.CharField(max_length=20)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.account_name} - {self.account_number}"

class FinancialReport(models.Model):
    """Generated financial reports"""
    REPORT_TYPES = [
        ('monthly', 'Monthly Report'),
        ('quarterly', 'Quarterly Report'),
        ('annual', 'Annual Report'),
        ('custom', 'Custom Report'),
    ]
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    total_income = models.DecimalField(max_digits=15, decimal_places=2)
    total_expenses = models.DecimalField(max_digits=15, decimal_places=2)
    net_balance = models.DecimalField(max_digits=15, decimal_places=2)
    report_file = models.FileField(
        upload_to='reports/%Y/%m/', 
        null=True, 
        blank=True,
        validators=[validate_file_extension, validate_file_size]
    )
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.start_date} to {self.end_date})"

# EVENT MANAGEMENT MODELS
class EventCategory(models.Model):
    """Categories for events"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-calendar', help_text='FontAwesome icon class')
    color = models.CharField(max_length=20, default='primary', help_text='Bootstrap color class')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'Event Categories'
    
    def __str__(self):
        return self.name

class Event(models.Model):
    """Events and programs for veterans"""
    EVENT_STATUS = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=300)
    description = models.TextField()
    category = models.ForeignKey(EventCategory, on_delete=models.CASCADE)
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True, blank=True, help_text='Leave blank for all states')
    
    # Event details
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    venue = models.CharField(max_length=300)
    address = models.TextField()
    contact_person = models.CharField(max_length=200)
    contact_phone = models.CharField(max_length=15, validators=[validate_phone_number])
    contact_email = models.EmailField(blank=True)
    
    # Registration
    registration_required = models.BooleanField(default=True)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)
    
    # Media
    banner_image = models.ImageField(
        upload_to='events/%Y/%m/', 
        null=True, 
        blank=True,
        validators=[validate_image_extension, validate_file_size]
    )
    attachments = models.FileField(
        upload_to='events/docs/%Y/%m/', 
        null=True, 
        blank=True,
        validators=[validate_file_extension, validate_file_size]
    )
    
    # System fields
    status = models.CharField(max_length=20, choices=EVENT_STATUS, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return self.title
    
    def get_registration_count(self):
        return self.registrations.filter(status='confirmed').count()
    
    def is_registration_open(self):
        from django.utils import timezone
        now = timezone.now()
        if self.registration_deadline and now > self.registration_deadline:
            return False
        if self.max_participants and self.get_registration_count() >= self.max_participants:
            return False
        return self.status == 'published'

class EventRegistration(models.Model):
    """Event registrations by veterans"""
    REGISTRATION_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('attended', 'Attended'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    veteran = models.ForeignKey(VeteranMember, on_delete=models.CASCADE, related_name='event_registrations')
    
    # Registration details
    participants_count = models.PositiveIntegerField(default=1, help_text='Number of people attending')
    special_requirements = models.TextField(blank=True, help_text='Dietary, accessibility needs')
    
    # Payment
    payment_required = models.BooleanField(default=False)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, default='pending')
    payment_id = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=20, choices=REGISTRATION_STATUS, default='pending')
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['event', 'veteran']
        ordering = ['-registered_at']
    
    def __str__(self):
        return f"{self.veteran.name} - {self.event.title}"

# PAYMENT INTEGRATION MODELS
class PaymentGateway(models.Model):
    """Payment gateway configuration"""
    GATEWAY_TYPES = [
        ('razorpay', 'Razorpay'),
        ('stripe', 'Stripe'),
        ('payu', 'PayU'),
        ('ccavenue', 'CCAvenue'),
    ]
    
    name = models.CharField(max_length=50, choices=GATEWAY_TYPES, unique=True)
    display_name = models.CharField(max_length=100)
    api_key = models.CharField(max_length=200)
    secret_key = models.CharField(max_length=200)
    webhook_secret = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=False)
    is_test_mode = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.display_name

class PaymentOrder(models.Model):
    """Payment orders for various services"""
    ORDER_TYPES = [
        ('subscription', 'Subscription Payment'),
        ('event_registration', 'Event Registration'),
        ('donation', 'Donation'),
        ('membership_fee', 'Membership Fee'),
    ]
    
    PAYMENT_STATUS = [
        ('created', 'Created'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    order_id = models.CharField(max_length=100, unique=True)
    veteran = models.ForeignKey(VeteranMember, on_delete=models.CASCADE, related_name='payment_orders')
    order_type = models.CharField(max_length=30, choices=ORDER_TYPES)
    
    # Order details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    description = models.TextField()
    
    # Payment gateway details
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.CASCADE)
    gateway_order_id = models.CharField(max_length=200, blank=True)
    gateway_payment_id = models.CharField(max_length=200, blank=True)
    
    # Related objects
    event_registration = models.ForeignKey(EventRegistration, on_delete=models.CASCADE, null=True, blank=True)
    
    # Status and timestamps
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='created')
    payment_method = models.CharField(max_length=50, blank=True)
    failure_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order_id} - ₹{self.amount}"

class PaymentWebhook(models.Model):
    """Webhook logs from payment gateways"""
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    order = models.ForeignKey(PaymentOrder, on_delete=models.CASCADE, null=True, blank=True)
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.gateway.name} - {self.event_type}"

class AssociationVerification(models.Model):
    """Association number verification log"""
    association_number = models.CharField(max_length=30, db_index=True)
    verified_by = models.CharField(max_length=200, blank=True, help_text='Organization or person who verified')
    verification_date = models.DateTimeField(auto_now_add=True)
    verification_method = models.CharField(max_length=50, choices=[
        ('qr_scan', 'QR Code Scan'),
        ('manual', 'Manual Verification'),
        ('online', 'Online Verification')
    ], default='manual')
    notes = models.TextField(blank=True, help_text='Verification notes')
    
    class Meta:
        verbose_name = 'Association Verification'
        verbose_name_plural = 'Association Verifications'
        ordering = ['-verification_date']
    
    def __str__(self):
        return f"{self.association_number} - {self.verification_date.strftime('%Y-%m-%d')}"

# TWO-FACTOR AUTHENTICATION MODELS
class TwoFactorAuth(models.Model):
    """Two-factor authentication settings for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor')
    is_enabled = models.BooleanField(default=False)
    secret_key = models.CharField(max_length=32, blank=True, help_text='TOTP secret key')
    backup_codes = models.JSONField(default=list, help_text='Backup recovery codes')
    created_at = models.DateTimeField(auto_now_add=True)
    enabled_at = models.DateTimeField(null=True, blank=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Two-Factor Authentication'
        verbose_name_plural = 'Two-Factor Authentication'
    
    def __str__(self):
        return f"{self.user.username} - {'Enabled' if self.is_enabled else 'Disabled'}"

# REPORTING SYSTEM MODELS
class ReportConfiguration(models.Model):
    """Saved report configurations"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=50, choices=[
        ('veteran', 'Veteran Report'),
        ('financial', 'Financial Report'),
        ('administrative', 'Administrative Report'),
    ])
    selected_columns = models.JSONField(help_text='List of selected column names')
    filters = models.JSONField(default=dict, help_text='Applied filters')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_template = models.BooleanField(default=False, help_text='System template')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

# GALLERY MODELS
class GalleryImage(models.Model):
    """Gallery images for veterans and events"""
    title = models.CharField(max_length=300, help_text='Image title/caption')
    description = models.TextField(blank=True, help_text='Image description')
    image = models.ImageField(
        upload_to='gallery/%Y/%m/',
        validators=[validate_image_extension, validate_file_size],
        help_text='Upload image (JPG, PNG, max 5MB)'
    )
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True, blank=True, help_text='Related state')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gallery_images')
    is_public = models.BooleanField(default=True, help_text='Visible to all users')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Gallery Image'
        verbose_name_plural = 'Gallery Images'
    
    def __str__(self):
        return self.title


