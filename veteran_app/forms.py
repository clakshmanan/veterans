# pylint: disable=no-member

from django import forms
import re
from datetime import date
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import (Rank, Branch, VeteranMember, CarouselSlide, State,
                     Child, JobPortal, Matrimonial)
from .validators import validate_phone_number
Group = Branch  # Backward compatibility

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

class RankForm(forms.ModelForm):
    class Meta:
        model = Rank
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter rank name'})
        }

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter branch name'})
        }

# Backward compatibility
GroupForm = BranchForm

class VeteranMemberForm(forms.ModelForm):
    subscription_due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'readonly': True}),
        help_text='Automatically calculated as 365 days from Subscription Paid On date'
    )
    
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        label='Branch',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select military branch'
    )
    
    class Meta:
        model = VeteranMember
        fields = [
            # Personal Information
            'profile_photo', 'name', 'date_of_birth', 'contact', 'address', 'alternate_email',
            'educational_qualification', 'living_city', 'zip_code', 'enrolled_date',
            
            # Emergency Contact
            'emergency_contact_name', 'emergency_contact_phone', 'nearest_veteran_contact',
           
           # Medical Information
            'blood_group', 'medical_category', 'medical_category_text', 'disabilities', 'nearest_echs_text', 'insurance_details', 'medical_conditions',
            
            # Military Information
            'service_number', 'rank', 'branch', 'date_of_joining', 'retired_on',
            'specialization', 'decorations', 'deployment_history', 'unit_served', 'nearest_dhq_text',
            
            # Association Information
            'association_date', 'membership', 'subscription_ref_no', 'subscription_paid_on', 'document', 'searching_for_job',
            
            # Family Details - Spouse
            'spouse_name', 'spouse_contact', 'spouse_employed', 'spouse_medical_details',
            
            # Legacy
            'children_count',
            
            # Welfare Information
            'pension_details', 'bank_account', 'bank_name', 'welfare_schemes', 
            'next_of_kin', 'next_of_kin_relation', 'next_of_kin_contact'
        ]
        widgets = {
            # Personal Information
            'profile_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'pattern': '(\+91|91)?[6-9]\d{9}', 'title': '10-digit mobile number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'alternate_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'educational_qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'living_city': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
            'enrolled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            
            # Emergency Contact
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'pattern': '(\+91|91)?[6-9]\d{9}', 'title': '10-digit mobile number'}),
            'nearest_veteran_contact': forms.TextInput(attrs={'class': 'form-control', 'pattern': '(\+91|91)?[6-9]\d{9}', 'title': '10-digit mobile number'}),
            
            # Medical Information
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'medical_category': forms.Select(attrs={'class': 'form-select'}),
            'medical_category_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category Description'}),
            'disabilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nearest_echs_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter nearest ECHS'}),
            'insurance_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'medical_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            
            # Military Information
            'service_number': forms.TextInput(attrs={'class': 'form-control'}),
            'rank': forms.Select(attrs={'class': 'form-select'}),
            'date_of_joining': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'retired_on': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'decorations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'deployment_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'unit_served': forms.TextInput(attrs={'class': 'form-control'}),
            'nearest_dhq_text': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter nearest District Headquarters (e.g., Mumbai DHQ, Delhi DHQ)'
            }),
            
            # Association Information
            'association_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'membership': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'subscription_ref_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subscription Reference Number'}),
            'subscription_paid_on': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'document': forms.FileInput(attrs={'class': 'form-control'}),
            'searching_for_job': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # Family Details - Spouse
            'spouse_name': forms.TextInput(attrs={'class': 'form-control'}),
            'spouse_contact': forms.TextInput(attrs={'class': 'form-control', 'pattern': '(\+91|91)?[6-9]\d{9}', 'title': '10-digit mobile number'}),
            'spouse_employed': forms.TextInput(attrs={'class': 'form-control'}),
            'spouse_medical_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            
            # Legacy
            'children_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            
            # Welfare Information
            'pension_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'bank_account': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'welfare_schemes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'next_of_kin': forms.TextInput(attrs={'class': 'form-control'}),
            'next_of_kin_relation': forms.TextInput(attrs={'class': 'form-control'}),
            'next_of_kin_contact': forms.TextInput(attrs={'class': 'form-control', 'pattern': '(\+91|91)?[6-9]\d{9}', 'title': '10-digit mobile number'})
        }
     
    def __init__(self, *args, **kwargs):
        # Check if this is for profile editing (instance exists) or new member creation
        is_profile_edit = kwargs.get('instance') and kwargs.get('instance').pk
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            # Set the calculated subscription due date
            due_date = self.instance.get_subscription_due_date()
            if due_date:
                self.fields['subscription_due_date'].initial = due_date
        
        # Set custom labels for better UX
        self.fields['branch'].label = 'Branch'
        self.fields['rank'].label = 'Rank'
        self.fields['service_number'].label = 'Service Number'
        self.fields['unit_served'].label = 'Last Ship/Unit Served'
        self.fields['nearest_dhq_text'].label = 'Nearest DHQ'
        self.fields['spouse_name'].label = 'Spouse Name'
        self.fields['date_of_birth'].label = 'Date of Birth'
        self.fields['date_of_joining'].label = 'Date of Joining Service'
        self.fields['retired_on'].label = 'Date of Retirement'
        self.fields['association_date'].label = 'Association Joining Date'
        self.fields['subscription_ref_no'].label = 'Subscription Ref.No'
        self.fields['subscription_paid_on'].label = 'Subscription Paid On'
        self.fields['blood_group'].label = 'Blood Group'
        self.fields['medical_category'].label = 'Medical Category'
        self.fields['nearest_echs_text'].label = 'Nearest ECHS'
        self.fields['living_city'].label = 'Living City'
        self.fields['zip_code'].label = 'Postal/Zib Code'
        self.fields['enrolled_date'].label = 'Course Completed Date'
        
        # Mark required fields only for new member creation, not for profile editing
        if not is_profile_edit:
            try:
                self.fields['service_number'].required = True
                self.fields['unit_served'].required = True
                self.fields['nearest_dhq_text'].required = True
                self.fields['spouse_name'].required = True
            except KeyError:
                # If fields are not present in some contexts, ignore
                pass
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > date.today():
            raise forms.ValidationError('Date of Birth cannot be a future date.')
        return dob
    
    def clean_enrolled_date(self):
        enrolled_date = self.cleaned_data.get('enrolled_date')
        if enrolled_date and enrolled_date > date.today():
            raise forms.ValidationError('Enrolled Date cannot be a future date.')
        return enrolled_date
    
    def clean_date_of_joining(self):
        joining_date = self.cleaned_data.get('date_of_joining')
        if joining_date and joining_date > date.today():
            raise forms.ValidationError('Date of Joining cannot be a future date.')
        return joining_date
    
    def clean_retired_on(self):
        retired_date = self.cleaned_data.get('retired_on')
        if retired_date and retired_date > date.today():
            raise forms.ValidationError('Retirement Date cannot be a future date.')
        return retired_date
    
    def clean_association_date(self):
        assoc_date = self.cleaned_data.get('association_date')
        if assoc_date and assoc_date > date.today():
            raise forms.ValidationError('Association Date cannot be a future date.')
        return assoc_date
    
    def clean_subscription_paid_on(self):
        sub_date = self.cleaned_data.get('subscription_paid_on')
        if sub_date and sub_date > date.today():
            raise forms.ValidationError('Subscription Paid Date cannot be a future date.')
        return sub_date
    
    def clean(self):
        cleaned_data = super().clean()
        dob = cleaned_data.get('date_of_birth')
        joining_date = cleaned_data.get('date_of_joining')
        retired_date = cleaned_data.get('retired_on')
        enrolled_date = cleaned_data.get('enrolled_date')
        
        # Validate date relationships
        if dob and joining_date and joining_date <= dob:
            raise forms.ValidationError('Date of Joining must be after Date of Birth.')
        
        if joining_date and retired_date and retired_date <= joining_date:
            raise forms.ValidationError('Retirement Date must be after Date of Joining.')
        
        if dob and enrolled_date and enrolled_date <= dob:
            raise forms.ValidationError('Enrolled Date must be after Date of Birth.')
        
        return cleaned_data

class CarouselSlideForm(forms.ModelForm):
    class Meta:
        model = CarouselSlide
        fields = ['title', 'subtitle', 'content', 'image', 'icon_class', 'background_color', 'order', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Slide Title'}),
            'subtitle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Slide Subtitle'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Slide Content'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'icon_class': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fas fa-anchor'}),
            'background_color': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('bg-gradient-primary', 'Blue Gradient'),
                ('bg-gradient-success', 'Green Gradient'),
                ('bg-gradient-info', 'Light Blue Gradient'),
                ('bg-gradient-warning', 'Orange Gradient'),
                ('bg-gradient-danger', 'Red Gradient'),
            ]),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class VeteranRegistrationForm(forms.Form):
    """Self-registration form for veterans."""
    # pylint: disable=attribute-defined-outside-init
    service_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your Service Number',
            'pattern': r'\d+-[A-Za-z]',
            'title': 'Format: digits-hyphen-letter (e.g., 12345-A)'
        }),
        help_text='Enter your Unique Military Service Number-Letter.'
        #  help_text='Enter your military Service Number (unique). Format: digits-hyphen-letter (e.g., 12345-A)'
    )
    # Additional personal details while registering
    name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}), required=False)
    rank = forms.ModelChoiceField(queryset=Rank.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}), required=False)
    unit_served = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Unit / Last Unit Served'}), required=False)
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email ID'}))
    mobile = forms.CharField(
        required=False,
        validators=[validate_phone_number],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '10-digit mobile number',
            'pattern': '(\+91|91)?[6-9]\d{9}',
            'title': '10-digit mobile number'
        })
    )
    subscription_ref_no = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subscription Reference Number'}),
        help_text='Enter your subscription reference number (mandatory)'
    )
    state = forms.ModelChoiceField(
        queryset=State.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select your state for veteran association membership'
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        help_text='Password must be at least 8 characters'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.veteran_member = None
        self.is_existing_veteran = False
    
    def clean_service_number(self):
        service_number = self.cleaned_data['service_number']
        # Validate format: digits-hyphen-single letter
        if not re.fullmatch(r"\d+-[A-Za-z]", service_number or ""):
            raise forms.ValidationError('Invalid Service Number format. Expected digits-hyphen-letter (e.g., 12345-A).')
        # Check if Service Number is already registered
        if VeteranMember.objects.filter(service_number=service_number).exists():
            existing_veteran = VeteranMember.objects.get(service_number=service_number)
            if hasattr(existing_veteran, 'user_account') and existing_veteran.user_account:
                raise forms.ValidationError('This Service Number already has a user account registered.')
            # Service Number exists but no user account - allow linking
            self.veteran_member = existing_veteran
            self.is_existing_veteran = True
        else:
            # New service number - will create new veteran profile
            self.veteran_member = None
            self.is_existing_veteran = False
        return service_number
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists.')
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data

class CreateVeteranUserForm(forms.Form):
    veteran = forms.ModelChoiceField(
        queryset=VeteranMember.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select a veteran without user account'
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username for veteran'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Temporary password'}),
        help_text='Veteran can change this password after first login'
    )
    
    def __init__(self, *args, **kwargs):
        state = kwargs.pop('state', None)
        super().__init__(*args, **kwargs)
        if state:
            # Only show veterans from this state who don't have user accounts
            veterans_without_accounts = VeteranMember.objects.filter(
                state=state
            ).exclude(
                user_account__isnull=False
            )
            self.fields['veteran'].queryset = veterans_without_accounts
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists.')
        return username

class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['child_photo', 'child_name', 'child_dob', 'child_qualification', 
                  'specialization', 'searching_for_job', 'searching_for_alliance']
        widgets = {
            'child_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'child_name': forms.TextInput(attrs={'class': 'form-control'}),
            'child_dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'child_qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'searching_for_job': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'searching_for_alliance': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def clean_child_dob(self):
        child_dob = self.cleaned_data.get('child_dob')
        if child_dob and child_dob > date.today():
            raise forms.ValidationError('Child Date of Birth cannot be a future date.')
        return child_dob

class JobPortalForm(forms.ModelForm):
    class Meta:
        model = JobPortal
        fields = ['applicant_type', 'child', 'name', 'contact', 'email', 'qualification',
                  'specialization', 'experience', 'skills', 'preferred_location', 'resume']
        widgets = {
            'applicant_type': forms.Select(attrs={'class': 'form-select'}),
            'child': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'pattern': '(\+91|91)?[6-9]\d{9}', 'title': '10-digit mobile number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'preferred_location': forms.TextInput(attrs={'class': 'form-control'}),
            'resume': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'})
        }

class MatrimonialForm(forms.ModelForm):
    class Meta:
        model = Matrimonial
        fields = ['child', 'child_name', 'photo', 'gender', 'height', 'religion', 'caste', 'occupation',
                  'annual_income', 'about', 'expectations', 'contact_person', 'contact_number']
        widgets = {
            'child': forms.Select(attrs={'class': 'form-select'}),
            'child_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter child name'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'height': forms.TextInput(attrs={'class': 'form-control'}),
            'religion': forms.TextInput(attrs={'class': 'form-control'}),
            'caste': forms.TextInput(attrs={'class': 'form-control'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'annual_income': forms.TextInput(attrs={'class': 'form-control'}),
            'about': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'expectations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'pattern': '(\+91|91)?[6-9]\d{9}', 'title': '10-digit mobile number'})
        }

class PasswordResetForm(forms.Form):
    user_id = forms.IntegerField(widget=forms.HiddenInput())
    new_password = forms.CharField(
        min_length=8,
        max_length=128,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'}),
        help_text='Password must be at least 8 characters long'
    )
    confirm_password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )
    
    def clean_user_id(self):
        user_id = self.cleaned_data['user_id']
        if user_id <= 0:
            raise forms.ValidationError('Invalid user ID.')
        return user_id
    
    def clean_new_password(self):
        password = self.cleaned_data['new_password']
        # Strong password validation
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        if password.isdigit():
            raise forms.ValidationError('Password cannot be entirely numeric.')
        if not any(c.isupper() for c in password):
            raise forms.ValidationError('Password must contain at least one uppercase letter.')
        if not any(c.islower() for c in password):
            raise forms.ValidationError('Password must contain at least one lowercase letter.')
        if not any(c.isdigit() for c in password):
            raise forms.ValidationError('Password must contain at least one number.')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            raise forms.ValidationError('Password must contain at least one special character (!@#$%^&*...).')
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data

class UserProfileForm(forms.Form):
    email = forms.EmailField(
        required=False,
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    def clean_first_name(self):
        name = self.cleaned_data['first_name'].strip()
        if name and not name.replace(' ', '').replace('-', '').replace('.', '').isalpha():
            raise forms.ValidationError('Name can only contain letters, spaces, hyphens, and periods.')
        return name
    
    def clean_last_name(self):
        name = self.cleaned_data['last_name'].strip()
        if name and not name.replace(' ', '').replace('-', '').replace('.', '').isalpha():
            raise forms.ValidationError('Name can only contain letters, spaces, hyphens, and periods.')
        return name

class TransactionForm(forms.Form):
    TRANSACTION_TYPES = [
        ('subscription', 'Subscription Payment'),
        ('donation', 'Donation'),
        ('expense', 'Expense'),
        ('refund', 'Refund'),
        ('other_income', 'Other Income'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
    ]
    
    veteran = forms.ModelChoiceField(
        queryset=VeteranMember.objects.filter(approved=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    transaction_type = forms.ChoiceField(
        choices=TRANSACTION_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        max_value=999999.99,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHODS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    reference_number = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    description = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    receipt = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'})
    )
    transaction_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text='Leave blank for today\'s date'
    )
    
    def clean_reference_number(self):
        ref = self.cleaned_data['reference_number'].strip()
        if ref and not ref.replace('-', '').replace('_', '').isalnum():
            raise forms.ValidationError('Reference number can only contain letters, numbers, hyphens, and underscores.')
        return ref
    
    def clean_transaction_date(self):
        trans_date = self.cleaned_data.get('transaction_date')
        if trans_date and trans_date > date.today():
            raise forms.ValidationError('Transaction Date cannot be a future date.')
        return trans_date

class AnnouncementForm(forms.Form):
    """Form for posting announcements with date validation"""
    NOTIFICATION_TYPES = [
        ('info', 'General Info'),
        ('warning', 'Policy Info'),
        ('success', 'Celebration Info'),
        ('urgent', 'Obituary'),
    ]
    
    title = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Announcement title'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Announcement message'})
    )
    notification_type = forms.ChoiceField(
        choices=NOTIFICATION_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='info'
    )
    expiry_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text='Date when this announcement will expire'
    )
    
    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get('expiry_date')
        if expiry_date:
            today = date.today()
            if expiry_date <= today:
                raise forms.ValidationError('Expiry date must be in the future.')
            # Limit expiry to maximum 1 year from today
            from datetime import timedelta
            max_expiry = today + timedelta(days=365)
            if expiry_date > max_expiry:
                raise forms.ValidationError('Expiry date cannot be more than 1 year from today.')
        return expiry_date