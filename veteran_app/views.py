from django.shortcuts import render, redirect, get_object_or_404
from datetime import date
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse, Http404
from django.core.exceptions import PermissionDenied
from django.db import models as django_models
from .models import Event
from django.contrib.auth.hashers import make_password
from .decorators import rate_limit, require_permissions, validate_state_access, require_state_access
from .models import (Rank, Branch, Message, VeteranMember, State, CarouselSlide, UserState, Document, Notification, VeteranUser,
                     Child, JobPortal, Matrimonial, ChatMessage, ChatRequest, BloodGroup, FinancialYear, Transaction, 
                     BankAccount, Expense, ExpenseCategory, FinancialReport, SubscriptionPlan, Event, EventCategory, 
                     EventRegistration, PaymentGateway, PaymentOrder, PaymentWebhook, TwoFactorAuth, ReportConfiguration, GalleryImage, AccountsUser)
Group = Branch  # Backward compatibility
from .forms import (RankForm, BranchForm, LoginForm, VeteranMemberForm, CarouselSlideForm, VeteranRegistrationForm, 
                    CreateVeteranUserForm, ChildForm, JobPortalForm, MatrimonialForm, AnnouncementForm)
GroupForm = BranchForm  # Backward compatibility
from django.utils.html import escape
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import Http404
import csv
import os
import mimetypes

def is_superuser(user):
    return user.is_superuser

def index(request):
    # If user is authenticated, check their role and approval status
    if request.user.is_authenticated and not request.user.is_superuser:
        try:
            # Check if user is a state admin
            user_state = request.user.state_profile
            if user_state.approved:
                # Redirect approved state admin to their state dashboard
                return redirect('state_dashboard', state_id=user_state.state.id)
        except UserState.DoesNotExist:
            # Check if user is a veteran
            try:
                veteran_user = request.user.veteran_profile
                if not veteran_user.approved:
                    # Redirect unapproved veteran to welcome page
                    return redirect('veteran_welcome')
                else:
                    # Redirect approved veteran to dashboard
                    return redirect('veteran_dashboard')
            except VeteranUser.DoesNotExist:
                pass
    
    # Get veteran birthdays (today and upcoming)
    from datetime import datetime, timedelta
    today = datetime.now().date()
    upcoming_days = 7  # Show birthdays for next 7 days
    
    veteran_birthdays = []
    for i in range(upcoming_days):
        check_date = today + timedelta(days=i)
        birthdays = VeteranMember.objects.filter(
            date_of_birth__month=check_date.month,
            date_of_birth__day=check_date.day,
            approved=True
        ).order_by('name')[:5]  # Limit to 5 per day
        
        for veteran in birthdays:
            age = today.year - veteran.date_of_birth.year
            if (today.month, today.day) < (veteran.date_of_birth.month, veteran.date_of_birth.day):
                age -= 1
            veteran_birthdays.append({
                'veteran': veteran,
                'date': check_date,
                'age': age + 1,  # Age they will turn
                'is_today': i == 0
            })
    
    # Get state admin notifications
    state_notifications = Notification.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    carousel_slides = CarouselSlide.objects.filter(is_active=True).order_by('order')[:5]
    total_members = VeteranMember.objects.count()
    active_members = VeteranMember.objects.filter(membership=True).count()
    states_covered = State.objects.count()
    
    return render(request, 'veteran_app/index.html', {
        'veteran_birthdays': veteran_birthdays,
        'state_notifications': state_notifications,
        'carousel_slides': carousel_slides,
        'total_members': total_members,
        'active_members': active_members,
        'states_covered': states_covered
    })

def about(request):
    return render(request, 'veteran_app/about.html')

def dashboard(request):
    """Dashboard view with metrics and quick access"""
    # Check if user is a veteran user - redirect them to appropriate dashboard
    if request.user.is_authenticated and hasattr(request.user, 'veteran_profile'):
        try:
            veteran_user = request.user.veteran_profile
            if not veteran_user.approved:
                messages.info(request, 'Your account is pending approval. Please wait for administrator approval.')
                return redirect('veteran_welcome')
            else:
                messages.info(request, 'Redirecting to your veteran dashboard.')
                return redirect('veteran_dashboard')
        except VeteranUser.DoesNotExist:
            pass
    
    # Get today's date
    from datetime import datetime, date
    today = date.today()
    
    # Debug: Print today's date for verification
    print(f"\n=== BIRTHDAY DEBUG ===")
    print(f"Checking for birthdays on: {today} (Month: {today.month}, Day: {today.day})")
    
    # Debug: Get all veterans with today's birthday (regardless of approval)
    all_today_birthdays = VeteranMember.objects.filter(
        date_of_birth__month=today.month,
        date_of_birth__day=today.day
    )
    print(f"\n=== VETERANS WITH TODAY'S BIRTHDAY ===")
    print(f"Found {all_today_birthdays.count()} veterans with today's birthday:")
    
    for vet in all_today_birthdays:
        print(f"\nVeteran Details:")
        print(f"- ID: {vet.association_id}")
        print(f"- Name: {vet.name}")
        print(f"- DOB: {vet.date_of_birth}")
        print(f"- Approved: {vet.approved}")
        print(f"- Rank: {vet.rank.name if vet.rank else 'N/A'}")
        print(f"- State: {vet.state.name if vet.state else 'N/A'}")
    
    # Debug: Search for veteran with name 'clakshmanan' (case-insensitive)
    print("\n=== SEARCHING FOR VETERAN 'clakshmanan' ===")
    try:
        # First try exact match with correct case
        clakshmanan = VeteranMember.objects.get(name='clakshmanan')
        print(f"Found exact case-sensitive match for 'clakshmanan':")
        print(f"- ID: {clakshmanan.id}")
        print(f"- Name: {clakshmanan.name}")
        print(f"- DOB: {clakshmanan.date_of_birth}")
        print(f"- Approved: {clakshmanan.approved}")
    except VeteranMember.DoesNotExist:
        print("No exact case-sensitive match for 'clakshmanan' found. Trying case-insensitive search...")
        try:
            # Try case-insensitive exact match
            clakshmanan = VeteranMember.objects.get(name__iexact='clakshmanan')
            print(f"Found case-insensitive match for 'clakshmanan':")
            print(f"- ID: {clakshmanan.association_id}")
            print(f"- Name in DB: {clakshmanan.name} (note: different case)")
            print(f"- DOB: {clakshmanan.date_of_birth}")
            print(f"- Approved: {clakshmanan.approved}")
        except VeteranMember.DoesNotExist:
            print("No exact match found. Trying partial match...")
            try:
                # Try partial match
                matches = VeteranMember.objects.filter(name__icontains='clakshmanan')
                if matches.exists():
                    print(f"Found {matches.count()} partial matches for 'clakshmanan':")
                    for i, vet in enumerate(matches, 1):
                        print(f"\nMatch {i}:")
                        print(f"- ID: {vet.association_id}")
                        print(f"- Name: {vet.name}")
                        print(f"- DOB: {vet.date_of_birth}")
                        print(f"- Approved: {vet.approved}")
                else:
                    print("No veteran with 'clakshmanan' in name found in database")
            except Exception as e:
                print(f"Error during partial name search: {str(e)}")
        except VeteranMember.MultipleObjectsReturned:
            print("Multiple exact matches for 'clakshmanan' found (case-insensitive)")
    except VeteranMember.MultipleObjectsReturned:
        print("Multiple exact case-sensitive matches for 'clakshmanan' found")
    
    # Filter veterans whose birthday is today and are approved
    todays_birthdays = VeteranMember.objects.filter(
        date_of_birth__month=today.month,
        date_of_birth__day=today.day,
        approved=True
    ).select_related('rank', 'state', 'blood_group').order_by('name')
    
    # Debug: Print query results
    print(f"\nFound {len(todays_birthdays)} approved birthdays today")
    
    veteran_birthdays = []
    for veteran in todays_birthdays:
        # Calculate current age (age they are today)
        age = today.year - veteran.date_of_birth.year
        # Adjust if birthday hasn't occurred this year yet
        if (today.month, today.day) < (veteran.date_of_birth.month, veteran.date_of_birth.day):
            age -= 1
        
        # Debug: Print veteran info
        print(f"- {veteran.name}: DOB {veteran.date_of_birth}, Current age: {age}")
        
        veteran_birthdays.append({
            'veteran': veteran,
            'age': age,  # Current age
            'is_today': True
        })
    
    # Get state admin notifications
    state_notifications = Notification.objects.filter(is_active=True).order_by('-created_at')[:10]
    
    # Calculate statistics
    total_members = VeteranMember.objects.count()
    active_members = VeteranMember.objects.filter(membership=True).count()
    states_covered = State.objects.count()
    current_month_year = today.strftime("%b %Y")
    
    return render(request, 'veteran_app/dashboard.html', {
        'veteran_birthdays': veteran_birthdays,
        'state_notifications': state_notifications,
        'total_members': total_members,
        'active_members': active_members,
        'states_covered': states_covered,
        'current_month_year': current_month_year
    })

def services(request):
    # If user is authenticated and is a state admin, redirect to their state dashboard
    if request.user.is_authenticated and not request.user.is_superuser:
        try:
            user_state = request.user.state_profile
            if user_state.approved:
                # Redirect state admin directly to their state dashboard
                return redirect('state_dashboard', state_id=user_state.state.id)
        except UserState.DoesNotExist:
            pass
    
    # For superusers and public users, show all states
    states = State.objects.all().order_by('name')
    return render(request, 'veteran_app/services.html', {'states': states})

def login_view(request):
    # Check if user is trying to verify 2FA
    if request.session.get('2fa_user_id'):
        return redirect('verify_2fa')
    
    if request.user.is_authenticated:
        # Redirect based on user role
        if request.user.is_superuser:
            return redirect('index')
        # Check if user has state profile and is approved
        try:
            user_state = request.user.state_profile
            if user_state.approved:
                # Redirect state admin directly to their state dashboard
                return redirect('state_dashboard', state_id=user_state.state.id)
            else:
                # User not approved, logout and show message
                logout(request)
                messages.warning(request, 'Your account is pending approval by the superadmin. Please contact the administrator.')
                return redirect('login')
        except UserState.DoesNotExist:
            # Check if user is a veteran
            try:
                veteran_user = request.user.veteran_profile
                return redirect('veteran_dashboard')
            except VeteranUser.DoesNotExist:
                # Regular user without state assignment
                return redirect('index')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # Check if user has 2FA enabled
                try:
                    two_factor = user.two_factor
                    if two_factor.is_enabled:
                        # Store user ID in session and redirect to 2FA verification
                        request.session['2fa_user_id'] = user.id
                        request.session['2fa_remember'] = request.POST.get('remember_me') == 'on'
                        return redirect('verify_2fa')
                except TwoFactorAuth.DoesNotExist:
                    pass
                
                # Check if user is superuser
                if user.is_superuser:
                    login(request, user)
                    messages.success(request, f'Hi, Superadmin {username}!')
                    return redirect('index')
                
                # Check if user has state profile
                try:
                    user_state = user.state_profile
                    if not user_state.approved:
                        messages.warning(request, 'Your account is pending approval by the superadmin. Please contact the administrator.')
                        return redirect('login')
                    
                    # User is approved, login and redirect to their state dashboard
                    login(request, user)
                    messages.success(request, f'Welcome back, {username}!')
                    return redirect('state_dashboard', state_id=user_state.state.id)
                except UserState.DoesNotExist:
                    # Check if user is accounts user
                    try:
                        accounts_user = user.accounts_profile
                        if not accounts_user.approved:
                            messages.warning(request, 'Your account is pending approval by the superadmin. Please contact the administrator.')
                            return redirect('login')
                        
                        # Accounts user is approved, login and redirect to treasurer dashboard
                        login(request, user)
                        messages.success(request, f'Welcome back, {username}!')
                        return redirect('treasurer_dashboard')
                    except:
                        # Check if user is a veteran
                        try:
                            veteran_user = user.veteran_profile
                            login(request, user)
                            messages.success(request, f'Welcome back, {username}!')
                            if veteran_user.approved:
                                return redirect('veteran_dashboard')
                            else:
                                return redirect('veteran_welcome')
                        except VeteranUser.DoesNotExist:
                            # Regular user without state assignment
                            login(request, user)
                            messages.success(request, f'Welcome back, {username}!')
                            return redirect('index')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'veteran_app/login.html', {'form': form})

@require_state_access()
def state_members(request, state_id):
    from django.core.paginator import Paginator
    
    try:
        state_id = int(state_id)
        state = get_object_or_404(State, id=state_id)
    except (ValueError, TypeError):
        raise Http404("Invalid state ID")
    
    # Check if user is a veteran user - redirect them to appropriate dashboard
    if hasattr(request.user, 'veteran_profile'):
        try:
            veteran_user = request.user.veteran_profile
            if not veteran_user.approved:
                messages.info(request, 'Your account is pending approval. Please wait for administrator approval.')
                return redirect('veteran_welcome')
            else:
                messages.info(request, 'Redirecting to your veteran dashboard.')
                return redirect('veteran_dashboard')
        except VeteranUser.DoesNotExist:
            pass
    
    # Permission checking is now handled by the @require_state_access decorator
    # This ensures:
    # 1. User is logged in
    # 2. Superusers can access any state
    # 3. State admins can only access their assigned state
    # 4. Users must be approved to access the system
    
    members_list = VeteranMember.objects.filter(state=state).order_by('-created_at')
    paginator = Paginator(members_list, 20)  # 20 members per page
    page_number = request.GET.get('page')
    members = paginator.get_page(page_number)
    
    return render(request, 'veteran_app/state_detail.html', {
        'state': state,
        'members': members,
        'page_obj': members
    })

@login_required
def add_member(request, state_id):
    try:
        state_id = int(state_id)
        state = get_object_or_404(State, id=state_id)
    except (ValueError, TypeError):
        raise Http404("Invalid state ID")
    
    # Check permissions - Proper authorization check
    if not request.user.is_superuser:
        try:
            user_state = request.user.state_profile
            if not user_state.approved:
                raise PermissionDenied('Your account is not approved.')
            if user_state.state != state:
                raise PermissionDenied('You do not have permission to add veterans to this state.')
        except UserState.DoesNotExist:
            raise PermissionDenied('You do not have permission to add veterans.')
    
    # State-based access control is sufficient - no need for Django model permissions
    
    if request.method == 'POST':
        form = VeteranMemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save(commit=False)
            member.state = state
            member.created_by = request.user
            
            # Validate dates don't exceed today
            today = date.today()
            date_fields = ['date_of_birth', 'enrolled_date', 'date_of_joining', 'retired_on', 'association_date', 'subscription_paid_on']
            for field in date_fields:
                field_value = getattr(member, field, None)
                if field_value and field_value > today:
                    messages.error(request, f'{field.replace("_", " ").title()} cannot be a future date.')
                    return render(request, 'veteran_app/member_form.html', {'form': form, 'state': state, 'action': 'Add'})
            
            # Set enrolled_date if not provided
            if not member.enrolled_date:
                member.enrolled_date = today
            # Auto-approve members created by superuser or state admin
            if request.user.is_superuser:
                member.approved = True
            else:
                # State admins can create pre-approved members
                member.approved = True
            try:
                member.save()
                
                # Handle subscription transaction if amount provided
                subscription_amount = request.POST.get('subscription_amount', '').strip()
                if subscription_amount and member.subscription_paid_on:
                    try:
                        from decimal import Decimal
                        import uuid
                        from datetime import datetime
                        
                        amount = Decimal(subscription_amount)
                        if amount > 0:
                            # Get or create current financial year
                            current_year = datetime.now().year
                            financial_year, created = FinancialYear.objects.get_or_create(
                                year=f"{current_year}-{current_year+1}",
                                defaults={
                                    'start_date': datetime(current_year, 4, 1).date(),
                                    'end_date': datetime(current_year+1, 3, 31).date(),
                                    'is_active': True
                                }
                            )
                            
                            # Generate transaction ID
                            transaction_id = f"SUB{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
                            
                            # Create transaction
                            Transaction.objects.create(
                                transaction_id=transaction_id,
                                veteran=member,
                                transaction_type='subscription',
                                amount=amount,
                                payment_method='online',
                                reference_number=member.subscription_ref_no or '',
                                description=f'Subscription payment by {member.name}',
                                financial_year=financial_year,
                                recorded_by=request.user
                            )
                            
                            # Update membership status
                            member.membership = True
                            member.save()
                    except (ValueError, Exception):
                        pass  # Silently ignore transaction errors
                
                messages.success(request, 'Veteran added successfully!')
                return redirect('state_members', state_id=state.id)
            except Exception as e:
                messages.error(request, f'Error adding veteran: {str(e)}')
        else:
            # Show specific field errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            messages.error(request, 'Please correct the errors highlighted in red below.')
    else:
        form = VeteranMemberForm()
    
    return render(request, 'veteran_app/member_form.html', {
        'form': form,
        'state': state,
        'action': 'Add'
    })

@login_required
def edit_member(request, member_id):
    try:
        member_id = int(member_id)
        member = get_object_or_404(VeteranMember, association_id=member_id)
    except (ValueError, TypeError):
        raise Http404("Invalid member ID")
    
    state = member.state
    
    # Generate association number if not exists
    if not member.association_number:
        member.generate_association_number()
        member.save(update_fields=['association_number'])
    
    # Check permissions
    if not request.user.is_superuser:
        try:
            user_state = request.user.state_profile
            if not user_state.approved:
                raise PermissionDenied('Your account is not approved.')
            if user_state.state != state:
                raise PermissionDenied('You do not have permission to edit this veteran.')
        except UserState.DoesNotExist:
            raise PermissionDenied('You do not have permission to edit veterans.')
    
    if request.method == 'POST':
        form = VeteranMemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            updated_member = form.save(commit=False)
            
            # Validate dates don't exceed today
            today = date.today()
            date_fields = ['date_of_birth', 'enrolled_date', 'date_of_joining', 'retired_on', 'association_date', 'subscription_paid_on']
            for field in date_fields:
                field_value = getattr(updated_member, field, None)
                if field_value and field_value > today:
                    messages.error(request, f'{field.replace("_", " ").title()} cannot be a future date.')
                    return render(request, 'veteran_app/member_form.html', {'form': form, 'state': state, 'action': 'Edit', 'member': member})
            
            try:
                old_subscription_date = member.subscription_paid_on
                updated_member.save()
                
                # Handle subscription transaction if amount provided and date changed
                subscription_amount = request.POST.get('subscription_amount', '').strip()
                if subscription_amount and updated_member.subscription_paid_on:
                    if old_subscription_date != updated_member.subscription_paid_on:
                        try:
                            from decimal import Decimal
                            import uuid
                            from datetime import datetime
                            
                            amount = Decimal(subscription_amount)
                            if amount > 0:
                                # Get or create current financial year
                                current_year = datetime.now().year
                                financial_year, created = FinancialYear.objects.get_or_create(
                                    year=f"{current_year}-{current_year+1}",
                                    defaults={
                                        'start_date': datetime(current_year, 4, 1).date(),
                                        'end_date': datetime(current_year+1, 3, 31).date(),
                                        'is_active': True
                                    }
                                )
                                
                                # Generate transaction ID
                                transaction_id = f"SUB{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
                                
                                # Create transaction
                                Transaction.objects.create(
                                    transaction_id=transaction_id,
                                    veteran=updated_member,
                                    transaction_type='subscription',
                                    amount=amount,
                                    payment_method='online',
                                    reference_number=updated_member.subscription_ref_no or '',
                                    description=f'Subscription payment by {updated_member.name}',
                                    financial_year=financial_year,
                                    recorded_by=request.user
                                )
                                
                                # Update membership status
                                updated_member.membership = True
                                updated_member.save()
                        except (ValueError, Exception):
                            pass  # Silently ignore transaction errors
                
                messages.success(request, 'Veteran updated successfully!')
                return redirect('state_members', state_id=state.id)
            except Exception as e:
                messages.error(request, f'Error updating veteran: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = VeteranMemberForm(instance=member)
    
    return render(request, 'veteran_app/member_form.html', {
        'form': form,
        'state': state,
        'action': 'Edit',
        'member': member
    })

@login_required
def delete_member(request, member_id):
    member = get_object_or_404(VeteranMember, association_id=member_id)
    state = member.state
    
    # Check permissions
    if not request.user.is_superuser:
        username = request.user.username.lower()
        if username.startswith('state_'):
            code = username.split('state_', 1)[1].upper()
            if state.code != code:
                messages.error(request, 'You do not have permission to delete this veteran.')
                return redirect('services')
        else:
            messages.error(request, 'You do not have permission to delete veterans.')
            return redirect('index')
    
    member.delete()
    messages.success(request, f'Veteran "{member.name}" deleted successfully!')
    return redirect('state_members', state_id=state.id)

@login_required
def approve_member(request, member_id):
    member = get_object_or_404(VeteranMember, association_id=member_id)
    
    # Check permissions - both superuser and state admin can approve
    if not request.user.is_superuser:
        try:
            user_state = request.user.state_profile
            if not user_state.approved or user_state.state != member.state:
                raise PermissionDenied('You do not have permission to approve this member.')
        except UserState.DoesNotExist:
            raise PermissionDenied('You do not have permission to approve members.')
    
    member.approved = True
    member.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'status': 'approved',
            'message': f'Veteran "{member.name}" approved successfully!'
        })
    
    messages.success(request, f'Veteran "{member.name}" approved successfully!')
    return redirect('state_members', state_id=member.state.id)

@login_required
def disapprove_member(request, member_id):
    member = get_object_or_404(VeteranMember, association_id=member_id)
    
    # Check permissions - both superuser and state admin can disapprove
    if not request.user.is_superuser:
        try:
            user_state = request.user.state_profile
            if not user_state.approved or user_state.state != member.state:
                raise PermissionDenied('You do not have permission to disapprove this member.')
        except UserState.DoesNotExist:
            raise PermissionDenied('You do not have permission to disapprove members.')
    
    member.approved = False
    member.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'status': 'pending',
            'message': f'Veteran "{member.name}" disapproved successfully!'
        })
    
    messages.warning(request, f'Veteran "{member.name}" disapproved successfully!')
    return redirect('state_members', state_id=member.state.id)

@login_required
def download_members(request, state_id):
    state = get_object_or_404(State, id=state_id)
    
    # Check permissions
    if not request.user.is_superuser:
        username = request.user.username.lower()
        if username.startswith('state_'):
            code = username.split('state_', 1)[1].upper()
            if state.code != code:
                messages.error(request, 'You do not have permission to download this data.')
                return redirect('services')
        else:
            messages.error(request, 'You do not have permission to download data.')
            return redirect('index')
    
    members = VeteranMember.objects.filter(state=state).order_by('name')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{state.code}_veterans.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Association ID', 'Association Number', 'Name', 'Rank', 'Branch', 'Service Number', 'Date of Birth',
        'Blood Group', 'Contact', 'Address', 'Living City', 'ZIP Code', 'Date of Joining', 'Retired On',
        'Enrolled Date', 'Association Date', 'Membership', 'Subscription Paid On',
        'Approved', 'Created At'
    ])
    
    for member in members:
        writer.writerow([
            member.association_id,
            member.association_number or 'Not Assigned',
            member.name,
            member.rank.name,
            member.branch.name,
            member.service_number,
            member.date_of_birth,
            member.blood_group.name,
            member.contact,
            member.address,
            member.living_city or '',
            member.zip_code or '',
            member.date_of_joining,
            member.retired_on,
            member.enrolled_date,
            member.association_date,
            'Yes' if member.membership else 'No',
            member.subscription_paid_on,
            'Yes' if member.approved else 'No',
            member.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response

@login_required
@user_passes_test(is_superuser)
def manage_data(request):
    ranks = Rank.objects.all().order_by('name')
    branches = Branch.objects.all().order_by('name')
    
    # Media statistics
    total_members = VeteranMember.objects.count()
    members_with_attachments = VeteranMember.objects.exclude(document='').count()
    media_stats = {
        'total_members': total_members,
        'members_with_attachments': members_with_attachments,
        'members_without_attachments': total_members - members_with_attachments,
        'attachment_percentage': round((members_with_attachments / total_members * 100) if total_members > 0 else 0, 1)
    }
    
    return render(request, 'veteran_app/manage_data.html', {
        'ranks': ranks,
        'branches': branches,
        'rank_form': RankForm(),
        'branch_form': BranchForm(),
        'media_stats': media_stats
    })

@login_required
@user_passes_test(is_superuser)
def add_rank(request):
    if request.method == 'POST':
        form = RankForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rank added successfully!')
        else:
            messages.error(request, 'Error adding rank. Please check the form.')
    return redirect('manage_data')

@login_required
@user_passes_test(is_superuser)
def delete_rank(request, rank_id):
    rank = get_object_or_404(Rank, id=rank_id)
    rank.delete()
    messages.success(request, f'Rank "{rank.name}" deleted successfully!')
    return redirect('manage_data')

@login_required
@user_passes_test(is_superuser)
def add_branch(request):
    if request.method == 'POST':
        form = BranchForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Branch added successfully!')
        else:
            messages.error(request, 'Error adding branch. Please check the form.')
    return redirect('manage_data')

@login_required
@user_passes_test(is_superuser)
def delete_branch(request, branch_id):
    branch = get_object_or_404(Branch, id=branch_id)
    branch.delete()
    messages.success(request, f'Branch "{branch.name}" deleted successfully!')
    return redirect('manage_data')

# Backward compatibility
add_group = add_branch
delete_group = delete_branch

@login_required
def download_document(request, member_id):
    try:
        member_id = int(member_id)
        member = get_object_or_404(VeteranMember, association_id=member_id)
    except (ValueError, TypeError):
        raise Http404("Invalid member ID")
    
    # Check permissions
    if not request.user.is_superuser:
        try:
            user_state = request.user.state_profile
            if not user_state.approved or user_state.state != member.state:
                raise PermissionDenied('You do not have permission to download this attachment.')
        except UserState.DoesNotExist:
            raise PermissionDenied('You do not have permission to download attachments.')
    
    # State-based access control is sufficient - no need for Django model permissions
    
    if not member.document:
        raise Http404('No attachment found for this veteran.')
    
    try:
        file_path = member.document.path
        # Validate file path to prevent directory traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(member.document.storage.location)):
            raise PermissionDenied('Invalid file path.')
        
        if not os.path.exists(file_path):
            raise Http404('Attachment file not found on server.')
        
        # Get the content type
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # Create response with proper headers
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type,
            as_attachment=True,
            filename=os.path.basename(file_path)
        )
        return response
        
    except (OSError, IOError) as e:
        raise Http404('Error accessing file.')

@login_required
@user_passes_test(is_superuser)
def manage_carousel(request):
    # Exclude the first slide (order=1) from management
    slides = CarouselSlide.objects.exclude(order=1).order_by('order')
    return render(request, 'veteran_app/manage_carousel.html', {
        'slides': slides,
        'slide_form': CarouselSlideForm(),
        'has_first_slide': CarouselSlide.objects.filter(order=1).exists()
    })

@login_required
@user_passes_test(is_superuser)
def add_carousel_slide(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        subtitle = request.POST.get('subtitle', '').strip()
        content = request.POST.get('content', '').strip()
        icon_class = request.POST.get('icon_class', '').strip()
        background_color = request.POST.get('background_color', 'bg-gradient-primary')
        order = max(2, int(request.POST.get('order', 2)))  # Ensure order is at least 2
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('image')
        
        if title and subtitle and content and image:
            try:
                # Check if order already exists
                if CarouselSlide.objects.filter(order=order).exists():
                    # Find the next available order
                    max_order = CarouselSlide.objects.aggregate(models.Max('order'))['order__max'] or 1
                    order = max_order + 1
                    
                slide = CarouselSlide.objects.create(
                    title=title,
                    subtitle=subtitle,
                    content=content,
                    icon_class=icon_class,
                    background_color=background_color,
                    order=order,
                    is_active=is_active,
                    image=image
                )
                messages.success(request, f'Carousel slide "{title}" added successfully with order {order}!')
            except Exception as e:
                messages.error(request, f'Error adding slide: {str(e)}')
        else:
            messages.error(request, 'Please fill all required fields (Title, Subtitle, Content, Image).')
    return redirect('manage_carousel')

@login_required
@user_passes_test(is_superuser)
def edit_carousel_slide(request, slide_id):
    slide = get_object_or_404(CarouselSlide, id=slide_id)
    
    # Prevent editing the first slide
    if slide.order == 1:
        messages.error(request, 'The first slide cannot be modified through this interface.')
        return redirect('manage_carousel')
        
    if request.method == 'POST':
        # Manual field extraction for modal form
        slide.title = request.POST.get('title', slide.title)
        slide.subtitle = request.POST.get('subtitle', slide.subtitle)
        slide.content = request.POST.get('content', slide.content)
        slide.icon_class = request.POST.get('icon_class', slide.icon_class)
        slide.background_color = request.POST.get('background_color', slide.background_color)
        
        # Prevent changing order to 1
        new_order = int(request.POST.get('order', slide.order))
        if new_order == 1:
            messages.error(request, 'Order 1 is reserved for the fixed home slide.')
            return redirect('manage_carousel')
        slide.order = new_order
        
        # Handle image upload
        if 'image' in request.FILES:
            slide.image = request.FILES['image']
        
        try:
            slide.save()
            messages.success(request, f'Carousel slide "{slide.title}" updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating slide: {str(e)}')
    return redirect('manage_carousel')

@login_required
@user_passes_test(is_superuser)
def delete_carousel_slide(request, slide_id):
    slide = get_object_or_404(CarouselSlide, id=slide_id)
    
    # Prevent deleting the first slide
    if slide.order == 1:
        messages.error(request, 'The first slide cannot be deleted as it is the fixed home slide.')
        return redirect('manage_carousel')
    
    title = slide.title
    slide.delete()
    messages.success(request, f'Slide "{title}" deleted successfully!')
    return redirect('manage_carousel')

@login_required
@user_passes_test(is_superuser)
def manage_users(request):
    """Manage state users and their approvals"""
    from django.contrib.auth.models import User
    
    # Get all state users (users with UserState profile)
    state_users = UserState.objects.select_related('user', 'state').all().order_by('state__name', 'user__username')
    
    # Get all veteran users
    veteran_users = VeteranUser.objects.select_related('user', 'veteran_member', 'veteran_member__state').all().order_by('veteran_member__state__name', 'veteran_member__name')
    
    # Get users without state profile (regular users)
    users_with_state = User.objects.filter(state_profile__isnull=False)
    users_with_veteran = User.objects.filter(veteran_profile__isnull=False)
    regular_users = User.objects.exclude(id__in=users_with_state).exclude(id__in=users_with_veteran).exclude(is_superuser=True).order_by('username')
    
    return render(request, 'veteran_app/manage_users.html', {
        'state_users': state_users,
        'veteran_users': veteran_users,
        'regular_users': regular_users
    })

@login_required
@user_passes_test(is_superuser)
def approve_user(request, user_state_id):
    """Approve a state user"""
    user_state = get_object_or_404(UserState, id=user_state_id)
    user_state.approved = True
    user_state.save()
    messages.success(request, f'User "{user_state.user.username}" approved successfully!')
    return redirect('manage_users')

@login_required
@user_passes_test(is_superuser)
def disapprove_user(request, user_state_id):
    """Disapprove a state user"""
    user_state = get_object_or_404(UserState, id=user_state_id)
    user_state.approved = False
    user_state.save()
    messages.warning(request, f'User "{user_state.user.username}" disapproved successfully!')
    return redirect('manage_users')

@login_required
def state_dashboard(request, state_id):
    """State-specific dashboard with calendar and statistics"""
    from datetime import datetime, timedelta
    from django.db.models import Count, Q
    from django.views.decorators.cache import never_cache
    
    state = get_object_or_404(State, id=state_id)
    
    # Check permissions: superuser can see all, state users only their state
    if not request.user.is_superuser:
        username = request.user.username.lower()
        if username.startswith('state_'):
            code = username.split('state_', 1)[1].upper()
            if state.code != code:
                messages.error(request, 'You do not have permission to view this state dashboard.')
                return redirect('index')
        else:
            messages.error(request, 'You do not have permission to view state dashboards.')
            return redirect('index')
    
    # Get current date
    current_date = datetime.now()
    
    # Calculate statistics
    all_members = VeteranMember.objects.filter(state=state)
    
    # This month's members
    first_day_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_members = all_members.filter(created_at__gte=first_day_of_month).count()
    
    stats = {
        'total_members': all_members.count(),
        'active_members': all_members.filter(membership=True).count(),
        'inactive_members': all_members.filter(membership=False).count(),
        'approved_members': all_members.filter(approved=True).count(),
        'pending_members': all_members.filter(approved=False).count(),
        'this_month_members': this_month_members,
    }
    
    # Get recent members (last 10) - force fresh query
    recent_members = all_members.select_related('rank', 'state').order_by('-created_at')[:10]
    
    response = render(request, 'veteran_app/state_dashboard.html', {
        'state': state,
        'stats': stats,
        'recent_members': recent_members,
        'current_date': current_date,
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@login_required
def media_documents(request):
    """View all documents and notifications"""
    from datetime import datetime
    from django.utils import timezone
    
    # Check if user is approved to access media
    if not request.user.is_superuser:
        try:
            # Check if state admin is approved
            if hasattr(request.user, 'state_profile') and not request.user.state_profile.approved:
                messages.error(request, 'Your account is pending approval. You cannot access media documents.')
                return redirect('index')
            # Check if veteran is approved
            elif hasattr(request.user, 'veteran_profile') and not request.user.veteran_profile.approved:
                messages.error(request, 'Your account is pending approval. You cannot access media documents.')
                return redirect('index')
        except:
            messages.error(request, 'Access denied. Please contact administrator.')
            return redirect('index')
    
    # Get user's state if applicable
    user_state = None
    if not request.user.is_superuser:
        try:
            user_state = request.user.state_profile.state
        except:
            pass
    
    # Filter documents based on user permissions
    if request.user.is_superuser:
        documents = Document.objects.filter(is_public=True)
    elif user_state:
        # State users see their state docs and all-state docs
        documents = Document.objects.filter(
            is_public=True
        ).filter(
            django_models.Q(state=user_state) | django_models.Q(state__isnull=True)
        )
    else:
        # Regular users see only all-state docs
        documents = Document.objects.filter(is_public=True, state__isnull=True)
    
    # Get active notifications
    if request.user.is_superuser:
        notifications = Notification.objects.filter(is_active=True)
    elif user_state:
        notifications = Notification.objects.filter(
            is_active=True
        ).filter(
            django_models.Q(state=user_state) | django_models.Q(state__isnull=True)
        )
    else:
        notifications = Notification.objects.filter(is_active=True, state__isnull=True)
    
    # Filter out expired notifications
    notifications = [n for n in notifications if not n.is_expired()]
    
    # Calculate statistics
    important_count = documents.filter(is_important=True).count()
    first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_count = documents.filter(created_at__gte=first_day_of_month).count()
    
    # Get all states for upload form
    all_states = State.objects.all().order_by('name')
    
    return render(request, 'veteran_app/media.html', {
        'documents': documents,
        'notifications': notifications,
        'important_count': important_count,
        'this_month_count': this_month_count,
        'all_states': all_states,
    })

@login_required
@user_passes_test(is_superuser)
def upload_document(request):
    """Upload a new document"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        document_type = request.POST.get('document_type')
        state_id = request.POST.get('state')
        is_important = request.POST.get('is_important') == 'on'
        is_public = request.POST.get('is_public') == 'on'
        file = request.FILES.get('file')
        
        if title and file:
            doc = Document(
                title=title,
                description=description,
                document_type=document_type,
                file=file,
                is_important=is_important,
                is_public=is_public,
                uploaded_by=request.user
            )
            
            if state_id:
                doc.state = State.objects.get(id=state_id)
            
            doc.save()
            messages.success(request, f'Document "{title}" uploaded successfully!')
        else:
            messages.error(request, 'Please provide title and file.')
    
    return redirect('media_documents')

@login_required
def view_document(request, doc_id):
    """View a document (opens in browser)"""
    from django.db import models
    
    doc = get_object_or_404(Document, id=doc_id)
    
    # Check permissions
    if not doc.is_public and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to view this document.')
        return redirect('media_documents')
    
    # Check state access
    if doc.state and not request.user.is_superuser:
        try:
            user_state = request.user.state_profile.state
            if doc.state != user_state:
                messages.error(request, 'You do not have permission to view this document.')
                return redirect('media_documents')
        except:
            messages.error(request, 'You do not have permission to view this document.')
            return redirect('media_documents')
    
    try:
        return FileResponse(doc.file.open('rb'), content_type='application/pdf')
    except:
        return FileResponse(doc.file.open('rb'))

@login_required
def download_document_file(request, doc_id):
    """Download a document"""
    from django.db import models
    
    doc = get_object_or_404(Document, id=doc_id)
    
    # Check permissions
    if not doc.is_public and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to download this document.')
        return redirect('media_documents')
    
    # Check state access
    if doc.state and not request.user.is_superuser:
        try:
            user_state = request.user.state_profile.state
            if doc.state != user_state:
                messages.error(request, 'You do not have permission to download this document.')
                return redirect('media_documents')
        except:
            messages.error(request, 'You do not have permission to download this document.')
            return redirect('media_documents')
    
    response = FileResponse(doc.file.open('rb'))
    response['Content-Disposition'] = f'attachment; filename="{doc.file.name}"'
    return response

@login_required
@user_passes_test(is_superuser)
def delete_document(request, doc_id):
    """Delete a document"""
    doc = get_object_or_404(Document, id=doc_id)
    title = doc.title
    doc.delete()
    messages.success(request, f'Document "{title}" deleted successfully!')
    return redirect('media_documents')

def veteran_register(request):
    """Veteran self-registration using P-Number"""
    if request.method == 'POST':
        form = VeteranRegistrationForm(request.POST)
        if form.is_valid():
            # Create user account
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            # Collect registration details
            svc = form.cleaned_data.get('service_number')
            name = form.cleaned_data.get('name') or 'Profile Incomplete'
            rank_obj = form.cleaned_data.get('rank')
            unit_served = form.cleaned_data.get('unit_served') or 'TBD'
            email = form.cleaned_data.get('email')
            mobile = form.cleaned_data.get('mobile')
            subscription_ref_no = form.cleaned_data.get('subscription_ref_no')
            state = form.cleaned_data.get('state')

            if getattr(form, 'is_existing_veteran', False):
                # Link to existing veteran member
                veteran = form.veteran_member
                # Update missing fields where provided
                updated = False
                if name and veteran.name in (None, '', 'Profile Incomplete'):
                    veteran.name = name
                    updated = True
                if unit_served and (not veteran.unit_served or veteran.unit_served in ('', 'TBD')):
                    veteran.unit_served = unit_served
                    updated = True
                if rank_obj and (not veteran.rank):
                    veteran.rank = rank_obj
                    updated = True
                if email and (not getattr(veteran, 'alternate_email', None)):
                    veteran.alternate_email = email
                    updated = True
                if mobile and (not getattr(veteran, 'contact', None)):
                    veteran.contact = mobile
                    updated = True
                if subscription_ref_no and (not getattr(veteran, 'subscription_ref_no', None) or veteran.subscription_ref_no == ''):
                    veteran.subscription_ref_no = subscription_ref_no
                    updated = True
                if updated:
                    veteran.save()

                VeteranUser.objects.create(
                    user=user,
                    veteran_member=veteran,
                    approved=False,
                    created_by_admin=False
                )
                messages.success(request, 'Registration successful! Your account is linked to existing profile and pending approval by the state administrator.')
            else:
                # Create new veteran member profile with provided values
                from datetime import date
                default_rank = rank_obj or Rank.objects.first()
                default_branch = Branch.objects.first()
                default_blood_group = BloodGroup.objects.first()

                veteran_member = VeteranMember.objects.create(
                    # legacy p_number column allows NULL; set to None to avoid UNIQUE constraint issues
                    # with empty strings when multiple registrations occur
                    p_number=None,
                    service_number=svc,
                    state=state,
                    name=name,
                    enrolled_date=date.today(),
                    date_of_birth=date(1970, 1, 1),  # Default DOB
                    contact=mobile or '0000000000',
                    address='Address not provided',
                    alternate_email=email or '',
                    blood_group=default_blood_group,
                    rank=default_rank,
                    branch=default_branch,
                    date_of_joining=date(1990, 1, 1),
                    retired_on=date(2020, 1, 1),
                    unit_served=unit_served,
                    nearest_dhq_text='TBD',
                    association_date=date.today(),
                    spouse_name='TBD',
                    subscription_ref_no=subscription_ref_no or '',
                    approved=False,  # Self-registered veterans need approval
                    created_by=user
                )

                VeteranUser.objects.create(
                    user=user,
                    veteran_member=veteran_member,
                    approved=False,
                    created_by_admin=False
                )
                messages.info(request, 'Registration successful! Please complete your profile. Your account is pending approval by the state administrator.')

            return redirect('login')
    else:
        form = VeteranRegistrationForm()
    
    return render(request, 'veteran_app/veteran_register.html', {'form': form})

@login_required
def veteran_welcome(request):
    """Welcome page for unapproved veterans"""
    try:
        veteran_user = request.user.veteran_profile
        if veteran_user.approved:
            return redirect('veteran_dashboard')
    except VeteranUser.DoesNotExist:
        return redirect('index')
    
    return render(request, 'veteran_app/veteran_welcome.html')

@login_required
def veteran_dashboard(request):
    """Veteran personal dashboard"""
    try:
        veteran_user = request.user.veteran_profile
        if not veteran_user.approved:
            return redirect('veteran_welcome')
        veteran = veteran_user.veteran_member
        
        # Generate association number if not exists
        if not veteran.association_number:
            veteran.generate_association_number()
            veteran.save(update_fields=['association_number'])
            
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Veteran profile not found.')
        return redirect('index')
    
    # Get children
    children = veteran.children.all()
    
    # Get payment history (all transactions for this veteran)
    payment_history = Transaction.objects.filter(
        veteran=veteran
    ).order_by('-created_at')[:10]  # Last 10 transactions
    
    # Calculate total paid
    from django.db.models import Sum
    total_paid = Transaction.objects.filter(
        veteran=veteran
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    return render(request, 'veteran_app/veteran_dashboard.html', {
        'veteran_user': veteran_user,
        'veteran': veteran,
        'children': children,
        'payment_history': payment_history,
        'total_paid': total_paid
    })

@login_required
def veteran_profile_edit(request):
    """Edit veteran profile"""
    try:
        veteran_user = request.user.veteran_profile
        veteran = veteran_user.veteran_member
        
        # Generate association number if not exists
        if not veteran.association_number:
            veteran.generate_association_number()
            veteran.save(update_fields=['association_number'])
            
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Veteran profile not found.')
        return redirect('index')
    
    if request.method == 'POST':
        form = VeteranMemberForm(request.POST, request.FILES, instance=veteran)
        subscription_amount = request.POST.get('subscription_amount', '').strip()
        old_subscription_date = veteran.subscription_paid_on
        
        if form.is_valid():
            try:
                updated_veteran = form.save()
                
                # Check if subscription payment was added/updated and amount provided
                if subscription_amount and updated_veteran.subscription_paid_on:
                    # Only create transaction if subscription date changed or is new
                    if old_subscription_date != updated_veteran.subscription_paid_on:
                        try:
                            from decimal import Decimal
                            import uuid
                            from datetime import datetime
                            
                            amount = Decimal(subscription_amount)
                            if amount > 0:
                                # Get or create current financial year
                                current_year = datetime.now().year
                                financial_year, created = FinancialYear.objects.get_or_create(
                                    year=f"{current_year}-{current_year+1}",
                                    defaults={
                                        'start_date': datetime(current_year, 4, 1).date(),
                                        'end_date': datetime(current_year+1, 3, 31).date(),
                                        'is_active': True
                                    }
                                )
                                
                                # Generate transaction ID
                                transaction_id = f"SUB{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
                                
                                # Create transaction
                                Transaction.objects.create(
                                    transaction_id=transaction_id,
                                    veteran=updated_veteran,
                                    transaction_type='subscription',
                                    amount=amount,
                                    payment_method='online',
                                    reference_number=updated_veteran.subscription_ref_no or '',
                                    description=f'Subscription payment by {updated_veteran.name}',
                                    financial_year=financial_year,
                                    recorded_by=request.user
                                )
                                
                                # Update membership status
                                updated_veteran.membership = True
                                updated_veteran.save()
                                
                                messages.success(request, f'Profile updated and subscription payment of ₹{amount} recorded successfully!')
                            else:
                                messages.success(request, 'Profile updated successfully!')
                        except (ValueError, Exception) as e:
                            messages.warning(request, f'Profile updated but subscription transaction failed: {str(e)}')
                    else:
                        messages.success(request, 'Profile updated successfully!')
                else:
                    messages.success(request, 'Profile updated successfully!')
                
                return redirect('veteran_dashboard')
            except Exception as e:
                messages.error(request, f'Error saving profile: {str(e)}')
        else:
            # Form has validation errors - show them to user
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            
            # Show non-field errors
            for error in form.non_field_errors():
                messages.error(request, f'Form error: {error}')
            
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = VeteranMemberForm(instance=veteran)
    
    return render(request, 'veteran_app/veteran_profile_edit.html', {
        'form': form,
        'veteran': veteran
    })

@login_required
def create_veteran_user(request, state_id):
    """State admin creates user account for veteran"""
    state = get_object_or_404(State, id=state_id)
    
    # Check permissions
    if not request.user.is_superuser:
        username = request.user.username.lower()
        if username.startswith('state_'):
            code = username.split('state_', 1)[1].upper()
            if state.code != code:
                messages.error(request, 'You do not have permission to create accounts for this state.')
                return redirect('services')
        else:
            messages.error(request, 'You do not have permission to create veteran accounts.')
            return redirect('index')
    
    if request.method == 'POST':
        form = CreateVeteranUserForm(request.POST, state=state)
        if form.is_valid():
            # Create user account
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            
            # Link to veteran member
            VeteranUser.objects.create(
                user=user,
                veteran_member=form.cleaned_data['veteran'],
                approved=True,  # Auto-approved when created by admin
                created_by_admin=True
            )
            
            messages.success(request, f'User account created for {form.cleaned_data["veteran"].name}!')
            return redirect('manage_veteran_users', state_id=state.id)
    else:
        form = CreateVeteranUserForm(state=state)
    
    return render(request, 'veteran_app/create_veteran_user.html', {
        'form': form,
        'state': state
    })

@login_required
def manage_veteran_users(request, state_id):
    """Manage veteran user accounts for a state"""
    from django.core.paginator import Paginator
    
    state = get_object_or_404(State, id=state_id)
    
    # Check permissions
    if not request.user.is_superuser:
        username = request.user.username.lower()
        if username.startswith('state_'):
            code = username.split('state_', 1)[1].upper()
            if state.code != code:
                messages.error(request, 'You do not have permission to manage this state.')
                return redirect('services')
        else:
            messages.error(request, 'You do not have permission to manage veteran accounts.')
            return redirect('index')
    
    # Get veteran users for this state
    veteran_users_list = VeteranUser.objects.filter(
        veteran_member__state=state
    ).select_related('user', 'veteran_member')
    
    paginator = Paginator(veteran_users_list, 20)  # 20 per page
    page_number = request.GET.get('page')
    veteran_users = paginator.get_page(page_number)
    
    return render(request, 'veteran_app/manage_veteran_users.html', {
        'state': state,
        'veteran_users': veteran_users,
        'page_obj': veteran_users
    })

@login_required
def approve_veteran_user(request, veteran_user_id):
    """Approve veteran user account - Superadmin or State Admin"""
    veteran_user = get_object_or_404(VeteranUser, id=veteran_user_id)
    state = veteran_user.veteran_member.state
    
    # Check permissions - Superadmin has override control
    if request.user.is_superuser:
        # Superadmin can approve any veteran
        pass
    else:
        try:
            user_state = request.user.state_profile
            if user_state.state != state:
                messages.error(request, 'You do not have permission to approve this account.')
                return redirect('services')
        except UserState.DoesNotExist:
            messages.error(request, 'You do not have permission to approve veteran accounts.')
            return redirect('index')
    
    veteran_user.approved = True
    veteran_user.approved_by = request.user
    veteran_user.save()
    
    approver_type = "Superadmin" if request.user.is_superuser else "State Admin"
    messages.success(request, f'Account approved for {veteran_user.veteran_member.name} by {approver_type}!')
    
    if request.user.is_superuser:
        return redirect('manage_users')
    else:
        return redirect('manage_veteran_users', state_id=state.id)

@login_required
def disapprove_veteran_user(request, veteran_user_id):
    """Disapprove veteran user account - Superadmin or State Admin"""
    veteran_user = get_object_or_404(VeteranUser, id=veteran_user_id)
    state = veteran_user.veteran_member.state
    
    # Check permissions - Superadmin has override control
    if request.user.is_superuser:
        # Superadmin can disapprove any veteran
        pass
    else:
        try:
            user_state = request.user.state_profile
            if user_state.state != state:
                messages.error(request, 'You do not have permission to disapprove this account.')
                return redirect('services')
        except UserState.DoesNotExist:
            messages.error(request, 'You do not have permission to disapprove veteran accounts.')
            return redirect('index')
    
    veteran_user.approved = False
    veteran_user.save()
    
    approver_type = "Superadmin" if request.user.is_superuser else "State Admin"
    messages.warning(request, f'Account disapproved for {veteran_user.veteran_member.name} by {approver_type}!')
    
    if request.user.is_superuser:
        return redirect('manage_users')
    else:
        return redirect('manage_veteran_users', state_id=state.id)

@login_required
def veteran_profile_detail(request):
    """Comprehensive veteran profile view"""
    try:
        veteran_user = request.user.veteran_profile
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Veteran profile not found.')
        return redirect('index')
    
    return render(request, 'veteran_app/veteran_profile_detail.html', {
        'veteran': veteran,
        'veteran_user': veteran_user
    })

# Portal Views
@login_required
def job_portal(request):
    """Job portal listing"""
    from django.core.paginator import Paginator
    
    # Check if veteran is approved
    if not request.user.is_superuser:
        try:
            veteran_user = request.user.veteran_profile
            if not veteran_user.approved:
                return redirect('veteran_welcome')
        except VeteranUser.DoesNotExist:
            pass
    
    job_seekers_list = JobPortal.objects.filter(is_active=True).order_by('-created_at')
    paginator = Paginator(job_seekers_list, 15)  # 15 per page
    page_number = request.GET.get('page')
    job_seekers = paginator.get_page(page_number)
    
    return render(request, 'veteran_app/job_portal.html', {
        'job_seekers': job_seekers,
        'page_obj': job_seekers
    })

@login_required
def job_portal_add(request):
    """Add job seeker profile"""
    if request.user.is_superuser:
        messages.info(request, 'Superadmin: Select a veteran to add job profile for.')
        return redirect('job_portal')
    
    try:
        veteran_user = request.user.veteran_profile
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Only veterans can add job profiles.')
        return redirect('job_portal')
    
    if request.method == 'POST':
        form = JobPortalForm(request.POST, request.FILES)
        if form.is_valid():
            job_profile = form.save(commit=False)
            job_profile.veteran = veteran
            job_profile.save()
            messages.success(request, 'Job profile added successfully!')
            return redirect('job_portal')
    else:
        form = JobPortalForm()
        # Pre-populate veteran's children for selection
        form.fields['child'].queryset = veteran.children.all()
    
    return render(request, 'veteran_app/job_portal_form.html', {'form': form})

@login_required
def job_portal_edit(request, job_id):
    """Edit job seeker profile"""
    try:
        veteran_user = request.user.veteran_profile
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Only veterans can edit job profiles.')
        return redirect('job_portal')
    
    job_profile = get_object_or_404(JobPortal, id=job_id, veteran=veteran)
    
    if request.method == 'POST':
        form = JobPortalForm(request.POST, request.FILES, instance=job_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job profile updated successfully!')
            return redirect('job_portal')
    else:
        form = JobPortalForm(instance=job_profile)
        form.fields['child'].queryset = veteran.children.all()
    
    return render(request, 'veteran_app/job_portal_form.html', {
        'form': form,
        'editing_job': job_profile
    })

@login_required
def job_portal_delete(request, job_id):
    """Delete job seeker profile"""
    try:
        veteran_user = request.user.veteran_profile
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Only veterans can delete job profiles.')
        return redirect('job_portal')
    
    job_profile = get_object_or_404(JobPortal, id=job_id, veteran=veteran)
    job_name = job_profile.name
    job_profile.delete()
    messages.success(request, f'Job profile for {job_name} deleted successfully!')
    return redirect('job_portal')

@login_required
@user_passes_test(is_superuser)
def admin_job_portal(request):
    """Admin view for managing job applications with resume access"""
    from django.core.paginator import Paginator
    
    job_applications_list = JobPortal.objects.select_related(
        'veteran', 'veteran__state', 'veteran__rank', 'child'
    ).order_by('-created_at')
    states = State.objects.all().order_by('name')
    
    paginator = Paginator(job_applications_list, 20)  # 20 per page
    page_number = request.GET.get('page')
    job_applications = paginator.get_page(page_number)
    
    return render(request, 'veteran_app/admin_job_portal.html', {
        'job_applications': job_applications,
        'states': states,
        'page_obj': job_applications
    })

@login_required
@user_passes_test(is_superuser)
def job_application_details(request, job_id):
    """Get job application details for modal view"""
    job = get_object_or_404(JobPortal, id=job_id)
    
    html = f"""
    <div class="row">
        <div class="col-md-6">
            <p><strong>Name:</strong> {job.name}</p>
            <p><strong>Type:</strong> {job.get_applicant_type_display()}</p>
            <p><strong>Veteran:</strong> {job.veteran.name}</p>
            <p><strong>Rank:</strong> {job.veteran.rank.name}</p>
            <p><strong>State:</strong> {job.veteran.state.name}</p>
        </div>
        <div class="col-md-6">
            <p><strong>Contact:</strong> {job.contact}</p>
            <p><strong>Email:</strong> {job.email or 'N/A'}</p>
            <p><strong>Qualification:</strong> {job.qualification}</p>
            <p><strong>Specialization:</strong> {job.specialization or 'N/A'}</p>
            <p><strong>Preferred Location:</strong> {job.preferred_location or 'N/A'}</p>
        </div>
    </div>
    {f'<div class="mt-3"><strong>Experience:</strong><br>{job.experience}</div>' if job.experience else ''}
    {f'<div class="mt-3"><strong>Skills:</strong><br>{job.skills}</div>' if job.skills else ''}
    {f'<div class="mt-3"><a href="{job.resume.url}" class="btn btn-success" download><i class="fas fa-download"></i> Download Resume</a></div>' if job.resume else '<div class="mt-3 text-muted">No resume uploaded</div>'}
    """
    
    return JsonResponse({'html': html})

@login_required
def matrimonial_portal(request):
    """Matrimonial portal listing"""
    from django.core.paginator import Paginator
    
    # Check if veteran is approved
    if not request.user.is_superuser:
        try:
            veteran_user = request.user.veteran_profile
            if not veteran_user.approved:
                return redirect('veteran_welcome')
        except VeteranUser.DoesNotExist:
            pass
    
    profiles_list = Matrimonial.objects.filter(is_active=True).order_by('-created_at')
    paginator = Paginator(profiles_list, 12)  # 12 per page
    page_number = request.GET.get('page')
    profiles = paginator.get_page(page_number)
    
    return render(request, 'veteran_app/matrimonial_portal.html', {
        'profiles': profiles,
        'page_obj': profiles
    })

@login_required
def matrimonial_add(request):
    """Add matrimonial profile"""
    if request.user.is_superuser:
        messages.info(request, 'Superadmin: Select a veteran to add matrimonial profile for.')
        return redirect('matrimonial_portal')
    
    try:
        veteran_user = request.user.veteran_profile
        if not veteran_user.approved:
            messages.error(request, 'Your account is pending approval. You cannot add matrimonial profiles.')
            return redirect('index')
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Only veterans can add matrimonial profiles.')
        return redirect('matrimonial_portal')
    
    if request.method == 'POST':
        form = MatrimonialForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.veteran = veteran
            profile.save()
            messages.success(request, 'Matrimonial profile added successfully!')
            return redirect('matrimonial_portal')
    else:
        form = MatrimonialForm()
        # Pre-populate veteran's children for selection
        form.fields['child'].queryset = veteran.children.all()
    
    return render(request, 'veteran_app/matrimonial_form.html', {'form': form})

@login_required
def matrimonial_edit(request, profile_id):
    """Edit matrimonial profile"""
    try:
        veteran_user = request.user.veteran_profile
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Only veterans can edit matrimonial profiles.')
        return redirect('matrimonial_portal')
    
    profile = get_object_or_404(Matrimonial, id=profile_id, veteran=veteran)
    
    if request.method == 'POST':
        form = MatrimonialForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Matrimonial profile updated successfully!')
            return redirect('matrimonial_portal')
    else:
        form = MatrimonialForm(instance=profile)
        form.fields['child'].queryset = veteran.children.all()
    
    return render(request, 'veteran_app/matrimonial_form.html', {
        'form': form,
        'editing_profile': profile
    })

@login_required
def matrimonial_delete(request, profile_id):
    """Delete matrimonial profile"""
    try:
        veteran_user = request.user.veteran_profile
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Only veterans can delete matrimonial profiles.')
        return redirect('matrimonial_portal')
    
    profile = get_object_or_404(Matrimonial, id=profile_id, veteran=veteran)
    child_name = profile.child.child_name
    profile.delete()
    messages.success(request, f'Matrimonial profile for {child_name} deleted successfully!')
    return redirect('matrimonial_portal')

@login_required
def chat_portal(request):
    """Chat portal - list veterans from other states"""
    from django.core.paginator import Paginator
    
    if request.user.is_superuser:
        # Superadmin can view all veterans and chat requests
        other_veterans_list = VeteranMember.objects.filter(approved=True).select_related('state', 'rank')
        sent_requests = ChatRequest.objects.all().select_related('requester', 'recipient')
        received_requests = ChatRequest.objects.all().select_related('requester', 'recipient')
    else:
        try:
            veteran_user = request.user.veteran_profile
            if not veteran_user.approved:
                messages.error(request, 'Your account is pending approval. You cannot access chat portal.')
                return redirect('veteran_welcome')
            veteran = veteran_user.veteran_member
        except VeteranUser.DoesNotExist:
            messages.error(request, 'Only veterans can access chat portal.')
            return redirect('index')
        
        # Get veterans from other states (exclude own state and self)
        other_veterans_list = VeteranMember.objects.exclude(
            state=veteran.state
        ).exclude(
            association_id=veteran.association_id
        ).filter(
            approved=True
        ).select_related('state', 'rank').order_by('state__name', 'name')
        
        # Get existing chat requests
        sent_requests = ChatRequest.objects.filter(requester=veteran).select_related('recipient', 'recipient__state')
        received_requests = ChatRequest.objects.filter(recipient=veteran).select_related('requester', 'requester__state')
    
    paginator = Paginator(other_veterans_list, 20)  # 20 per page
    page_number = request.GET.get('page')
    other_veterans = paginator.get_page(page_number)
    
    return render(request, 'veteran_app/chat_portal.html', {
        'other_veterans': other_veterans,
        'sent_requests': sent_requests,
        'received_requests': received_requests,
        'page_obj': other_veterans
    })

@login_required
def send_chat_request(request, veteran_id):
    """Send chat request to another veteran"""
    try:
        veteran_user = request.user.veteran_profile
        requester = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Only veterans can send chat requests.')
        return redirect('index')
    
    recipient = get_object_or_404(VeteranMember, association_id=veteran_id)
    
    # Check if request already exists
    existing_request = ChatRequest.objects.filter(requester=requester, recipient=recipient).first()
    if existing_request:
        messages.warning(request, 'Chat request already sent to this veteran.')
        return redirect('chat_portal')
    
    if request.method == 'POST':
        message = request.POST.get('message', '')
        ChatRequest.objects.create(
            requester=requester,
            recipient=recipient,
            message=message
        )
        messages.success(request, f'Chat request sent to {recipient.name}!')
        return redirect('chat_portal')
    
    return render(request, 'veteran_app/send_chat_request.html', {'recipient': recipient})

@login_required
def accept_chat_request(request, request_id):
    """Accept a chat request"""
    try:
        veteran_user = request.user.veteran_profile
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Only veterans can manage chat requests.')
        return redirect('index')
    
    chat_request = get_object_or_404(ChatRequest, id=request_id, recipient=veteran)
    chat_request.status = 'accepted'
    chat_request.responded_at = timezone.now()
    chat_request.save()
    
    messages.success(request, f'Chat request from {chat_request.requester.name} accepted!')
    return redirect('chat_portal')

@login_required
def reject_chat_request(request, request_id):
    """Reject a chat request"""
    try:
        veteran_user = request.user.veteran_profile
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Only veterans can manage chat requests.')
        return redirect('index')
    
    chat_request = get_object_or_404(ChatRequest, id=request_id, recipient=veteran)
    chat_request.status = 'rejected'
    chat_request.responded_at = timezone.now()
    chat_request.save()
    
    messages.warning(request, f'Chat request from {chat_request.requester.name} rejected.')
    return redirect('chat_portal')

@login_required
def manage_children(request):
    """Manage veteran's children"""
    try:
        veteran_user = request.user.veteran_profile
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Only veterans can manage children profiles.')
        return redirect('index')
    
    children = veteran.children.all()
    children_count = children.count()
    max_children = veteran.children_count
    can_add_more = children_count < max_children
    
    if request.method == 'POST':
        if not can_add_more:
            messages.error(request, f'You have reached the maximum number of children ({max_children}). Please update your profile if you need to add more.')
            return redirect('manage_children')
        
        form = ChildForm(request.POST, request.FILES)
        if form.is_valid():
            child = form.save(commit=False)
            child.veteran = veteran
            child.save()
            messages.success(request, 'Child profile added successfully!')
            return redirect('manage_children')
    else:
        form = ChildForm()
    
    return render(request, 'veteran_app/manage_children.html', {
        'children': children,
        'form': form,
        'can_add_more': can_add_more,
        'children_count': children_count,
        'max_children': max_children
    })

@login_required
def edit_child(request, child_id):
    """Edit child profile"""
    try:
        veteran_user = request.user.veteran_profile
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Only veterans can edit children profiles.')
        return redirect('index')
    
    child = get_object_or_404(Child, id=child_id, veteran=veteran)
    
    if request.method == 'POST':
        form = ChildForm(request.POST, request.FILES, instance=child)
        if form.is_valid():
            form.save()
            messages.success(request, 'Child profile updated successfully!')
            return redirect('manage_children')
    else:
        form = ChildForm(instance=child)
    
    return render(request, 'veteran_app/manage_children.html', {
        'children': veteran.children.all(),
        'form': form,
        'editing_child': child
    })

@login_required
def delete_child(request, child_id):
    """Delete child profile"""
    try:
        veteran_user = request.user.veteran_profile
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Only veterans can delete children profiles.')
        return redirect('index')
    
    child = get_object_or_404(Child, id=child_id, veteran=veteran)
    child_name = child.child_name
    child.delete()
    messages.success(request, f'Child profile for {child_name} deleted successfully!')
    return redirect('manage_children')

@login_required
def post_announcement(request):
    """Post announcement - State admins and superadmin"""
    if request.method == 'POST':
        from datetime import datetime, date
        from django.utils import timezone
        
        title = request.POST.get('title')
        message = request.POST.get('message')
        notification_type = request.POST.get('notification_type', 'info')
        expiry_date = request.POST.get('expiry_date')
        
        if title and message and expiry_date:
            try:
                # Validate expiry date
                expiry_date_obj = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                today = date.today()
                
                if expiry_date_obj <= today:
                    messages.error(request, 'Expiry date must be in the future.')
                    return redirect('post_announcement')
                
                # Limit expiry to maximum 1 year from today
                from datetime import timedelta
                max_expiry = today + timedelta(days=365)
                if expiry_date_obj > max_expiry:
                    messages.error(request, 'Expiry date cannot be more than 1 year from today.')
                    return redirect('post_announcement')
                
                # Convert date to datetime
                expiry_datetime = timezone.make_aware(datetime.strptime(expiry_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59))
                
                notification = Notification(
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    expires_at=expiry_datetime
                )
                
                # Set state for state admins
                if not request.user.is_superuser:
                    try:
                        user_state = request.user.state_profile
                        notification.state = user_state.state
                    except UserState.DoesNotExist:
                        messages.error(request, 'Only state admins and superadmin can post announcements.')
                        return redirect('index')
                
                notification.save()
                messages.success(request, 'Announcement posted successfully!')
            except ValueError:
                messages.error(request, 'Invalid expiry date format.')
        else:
            messages.error(request, 'Please provide title, message, and expiry date.')
    
    # Redirect based on user type
    if request.user.is_superuser:
        return redirect('index')
    else:
        try:
            user_state = request.user.state_profile
            return redirect('state_dashboard', state_id=user_state.state.id)
        except UserState.DoesNotExist:
            return redirect('index')

@login_required
@user_passes_test(is_superuser)
def password_reset_admin(request):
    """Superadmin password reset interface"""
    # Get all state users
    state_users = UserState.objects.select_related('user', 'state').all().order_by('state__name', 'user__username')
    
    # Get all veteran users
    veteran_users = VeteranUser.objects.select_related('user', 'veteran_member', 'veteran_member__state').all().order_by('veteran_member__state__name', 'veteran_member__name')
    
    # Get regular users (no state or veteran profile, not superuser)
    users_with_state = User.objects.filter(state_profile__isnull=False)
    users_with_veteran = User.objects.filter(veteran_profile__isnull=False)
    regular_users = User.objects.exclude(id__in=users_with_state).exclude(id__in=users_with_veteran).exclude(is_superuser=True).order_by('username')
    
    # Get all states for filtering
    states = State.objects.all().order_by('name')
    
    return render(request, 'veteran_app/password_reset_admin.html', {
        'state_users': state_users,
        'veteran_users': veteran_users,
        'regular_users': regular_users,
        'states': states
    })

@login_required
@user_passes_test(is_superuser)
@rate_limit(max_requests=3, window=300)
def reset_user_password(request):
    """Reset password for any user"""
    if request.method == 'POST':
        try:
            user_id = int(request.POST.get('user_id', 0))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid user ID.')
            return redirect('password_reset_admin')
        
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        if not user_id or not new_password or not confirm_password:
            messages.error(request, 'All fields are required.')
            return redirect('password_reset_admin')
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('password_reset_admin')
        
        # Enhanced password validation
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('password_reset_admin')
        
        if len(new_password) > 128:
            messages.error(request, 'Password too long.')
            return redirect('password_reset_admin')
        
        try:
            user = get_object_or_404(User, id=user_id)
            user.password = make_password(new_password)
            user.save()
            
            # Determine user type for success message
            user_type = "User"
            try:
                if hasattr(user, 'state_profile'):
                    user_type = f"State Admin ({user.state_profile.state.name})"
                elif hasattr(user, 'veteran_profile'):
                    user_type = f"Veteran ({user.veteran_profile.veteran_member.name})"
            except:
                pass
            
            messages.success(request, f'Password successfully reset for {user_type}: {user.username}')
            
        except (ValueError, User.DoesNotExist) as e:
            messages.error(request, 'Error resetting password.')
    
    return redirect('password_reset_admin')

# Treasurer Financial Management Views
@login_required
def treasurer_dashboard(request):
    """Treasurer dashboard with financial overview"""
    # Allow superuser and accounts user
    if not (request.user.is_superuser or request.user.username == 'accounts'):
        messages.error(request, 'Access denied. Only superuser and accounts user can access treasurer dashboard.')
        return redirect('index')
    
    from django.db.models import Sum, Count, Q
    from datetime import datetime, timedelta
    
    # Get current financial year or create default
    current_year = datetime.now().year
    financial_year, created = FinancialYear.objects.get_or_create(
        year=f"{current_year}-{current_year+1}",
        defaults={
            'start_date': datetime(current_year, 4, 1).date(),
            'end_date': datetime(current_year+1, 3, 31).date(),
            'is_active': True
        }
    )
    
    # Other transactions (donations, expenses, other income)
    transactions = Transaction.objects.filter(financial_year=financial_year)
    
    # Calculate actual subscription income from transactions
    subscription_income = transactions.filter(
        transaction_type='subscription'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Count paid subscriptions in current financial year
    paid_subscriptions = transactions.filter(
        transaction_type='subscription'
    ).count()
    other_income = transactions.filter(transaction_type__in=['donation', 'other_income']).aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    
    total_income = subscription_income + other_income
    
    financial_summary = {
        'total_income': total_income,
        'subscription_income': subscription_income,
        'other_income': other_income,
        'total_expenses': total_expenses,
        'net_balance': total_income - total_expenses,
        'active_members': VeteranMember.objects.filter(membership=True).count(),
        'paid_subscriptions': paid_subscriptions
    }
    
    # Subscription statistics
    from datetime import date
    today = date.today()
    all_members = VeteranMember.objects.all()
    subscription_stats = {
        'active': 0, 'due_soon': 0, 'overdue': 0, 'no_payment': 0
    }
    
    for member in all_members:
        status = member.get_subscription_status()
        if status['status'] == 'Active':
            subscription_stats['active'] += 1
        elif status['status'] == 'Due Soon':
            subscription_stats['due_soon'] += 1
        elif status['status'] == 'Overdue':
            subscription_stats['overdue'] += 1
        else:
            subscription_stats['no_payment'] += 1
    
    # Recent transactions (expenses and other income only)
    recent_transactions = transactions.order_by('-created_at')[:10]
    
    # Recent subscription payments from veterans
    recent_subscriptions = VeteranMember.objects.filter(
        subscription_paid_on__isnull=False
    ).order_by('-subscription_paid_on')[:5]
    
    # Bank accounts
    bank_accounts = BankAccount.objects.filter(is_active=True)
    
    # Veterans for dropdown
    veterans = VeteranMember.objects.filter(approved=True).order_by('name')
    
    return render(request, 'veteran_app/treasurer_dashboard.html', {
        'financial_summary': financial_summary,
        'subscription_stats': subscription_stats,
        'recent_transactions': recent_transactions,
        'recent_subscriptions': recent_subscriptions,
        'bank_accounts': bank_accounts,
        'veterans': veterans,
        'financial_year': financial_year
    })

@login_required
def add_transaction(request):
    """Add new financial transaction"""
    # Allow superuser and accounts user
    if not (request.user.is_superuser or request.user.username == 'accounts'):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    if request.method == 'POST':
        import uuid
        from datetime import datetime
        from decimal import Decimal, InvalidOperation
        
        # Validate and sanitize inputs
        try:
            veteran_id = int(request.POST.get('veteran')) if request.POST.get('veteran') else None
        except (ValueError, TypeError):
            veteran_id = None
        
        transaction_type = request.POST.get('transaction_type', '').strip()
        payment_method = request.POST.get('payment_method', '').strip()
        reference_number = escape(request.POST.get('reference_number', '').strip())
        description = escape(request.POST.get('description', '').strip())
        
        # Validate transaction type and payment method
        valid_types = ['subscription', 'donation', 'expense', 'refund', 'other_income', 'event_fee', 'crowdfunding']
        valid_methods = ['cash', 'bank_transfer', 'upi', 'cheque', 'online']
        
        if transaction_type not in valid_types:
            messages.error(request, 'Invalid transaction type.')
            return redirect('treasurer_dashboard')
        
        if payment_method not in valid_methods:
            messages.error(request, 'Invalid payment method.')
            return redirect('treasurer_dashboard')
        
        # Validate amount
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            if amount <= 0 or amount > Decimal('999999.99'):
                messages.error(request, 'Invalid amount.')
                return redirect('treasurer_dashboard')
        except (InvalidOperation, ValueError):
            messages.error(request, 'Invalid amount format.')
            return redirect('treasurer_dashboard')
        
        # Generate unique transaction ID
        transaction_id = f"TXN{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        
        try:
            # Get current financial year
            current_year = datetime.now().year
            financial_year = FinancialYear.objects.get(
                year=f"{current_year}-{current_year+1}"
            )
            
            # Create transaction
            transaction = Transaction.objects.create(
                transaction_id=transaction_id,
                veteran_id=veteran_id,
                transaction_type=transaction_type,
                amount=amount,
                payment_method=payment_method,
                reference_number=reference_number[:100],  # Limit length
                description=description[:500],  # Limit length
                receipt=request.FILES.get('receipt'),
                financial_year=financial_year,
                recorded_by=request.user
            )
        except FinancialYear.DoesNotExist:
            messages.error(request, 'Financial year not found.')
            return redirect('treasurer_dashboard')
        except Exception:
            messages.error(request, 'Error creating transaction.')
            return redirect('treasurer_dashboard')
        
        # Update veteran subscription if applicable
        if transaction.transaction_type == 'subscription' and transaction.veteran:
            veteran = transaction.veteran
            veteran.subscription_paid_on = date.today()
            veteran.membership = True
            veteran.save()
        
        messages.success(request, f'Transaction {transaction_id} added successfully!')
    
    return redirect('treasurer_dashboard')

@login_required
def transaction_list(request):
    """List all transactions with filtering"""
    # Allow superuser and accounts user
    if not (request.user.is_superuser or request.user.username == 'accounts'):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    from django.core.paginator import Paginator
    from django.db.models import Sum, Q
    
    transactions = Transaction.objects.all().order_by('-created_at')
    
    # Apply filters
    if request.GET.get('type'):
        transactions = transactions.filter(transaction_type=request.GET.get('type'))
    
    if request.GET.get('method'):
        transactions = transactions.filter(payment_method=request.GET.get('method'))
    
    if request.GET.get('from_date'):
        transactions = transactions.filter(created_at__date__gte=request.GET.get('from_date'))
    
    if request.GET.get('to_date'):
        transactions = transactions.filter(created_at__date__lte=request.GET.get('to_date'))
    
    # Calculate summary
    income = transactions.exclude(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    expenses = transactions.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    
    summary = {
        'total_income': income,
        'total_expenses': expenses,
        'net_amount': income - expenses
    }
    
    # Pagination
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)
    
    return render(request, 'veteran_app/transaction_list.html', {
        'transactions': transactions,
        'summary': summary
    })

@login_required
def transaction_detail(request, transaction_id):
    """Get transaction details for modal view"""
    # Allow superuser and accounts user
    if not (request.user.is_superuser or request.user.username == 'accounts'):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    html = f"""
    <div class="row">
        <div class="col-md-6">
            <strong>Transaction ID:</strong> {transaction.transaction_id}<br>
            <strong>Type:</strong> {transaction.get_transaction_type_display()}<br>
            <strong>Amount:</strong> ₹{transaction.amount}<br>
            <strong>Payment Method:</strong> {transaction.get_payment_method_display()}<br>
        </div>
        <div class="col-md-6">
            <strong>Date:</strong> {transaction.created_at.strftime('%B %d, %Y at %I:%M %p')}<br>
            <strong>Member:</strong> {transaction.veteran.name if transaction.veteran else 'N/A'}<br>
            <strong>Reference:</strong> {transaction.reference_number or 'N/A'}<br>
            <strong>Recorded By:</strong> {transaction.recorded_by.username}<br>
        </div>
    </div>
    {f'<div class="mt-3"><strong>Description:</strong><br>{transaction.description}</div>' if transaction.description else ''}
    """
    
    return JsonResponse({'html': html})

@login_required
def delete_transaction(request, transaction_id):
    """Delete a transaction"""
    # Allow superuser and accounts user
    if not (request.user.is_superuser or request.user.username == 'accounts'):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        transaction = get_object_or_404(Transaction, id=transaction_id)
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully!')
    
    return JsonResponse({'success': True})

@login_required
def generate_report(request):
    """Generate financial reports"""
    # Allow superuser and accounts user
    if not (request.user.is_superuser or request.user.username == 'accounts'):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    if request.method == 'POST':
        from django.http import HttpResponse
        from django.db.models import Sum
        import csv
        from datetime import datetime
        
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        report_type = request.POST.get('report_type')
        
        # Filter transactions
        transactions = Transaction.objects.filter(
            created_at__date__range=[start_date, end_date]
        ).order_by('-created_at')
        
        # Calculate totals
        income = transactions.exclude(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        expenses = transactions.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="financial_report_{start_date}_to_{end_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Financial Report', f'{start_date} to {end_date}'])
        writer.writerow([])
        writer.writerow(['Summary'])
        writer.writerow(['Total Income', f'₹{income}'])
        writer.writerow(['Total Expenses', f'₹{expenses}'])
        writer.writerow(['Net Balance', f'₹{income - expenses}'])
        writer.writerow([])
        writer.writerow(['Transaction Details'])
        writer.writerow(['Date', 'Transaction ID', 'Type', 'Member', 'Amount', 'Method', 'Reference', 'Description'])
        
        for transaction in transactions:
            writer.writerow([
                transaction.created_at.strftime('%Y-%m-%d %H:%M'),
                transaction.transaction_id,
                transaction.get_transaction_type_display(),
                transaction.veteran.name if transaction.veteran else 'N/A',
                transaction.amount,
                transaction.get_payment_method_display(),
                transaction.reference_number,
                transaction.description
            ])
        
        return response
    
    return redirect('treasurer_dashboard')

@login_required
def export_transactions(request):
    """Export transactions to CSV"""
    # Allow superuser and accounts user
    if not (request.user.is_superuser or request.user.username == 'accounts'):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    from django.http import HttpResponse
    import csv
    
    transactions = Transaction.objects.all().order_by('-created_at')
    
    # Apply same filters as transaction_list
    if request.GET.get('type'):
        transactions = transactions.filter(transaction_type=request.GET.get('type'))
    if request.GET.get('method'):
        transactions = transactions.filter(payment_method=request.GET.get('method'))
    if request.GET.get('from_date'):
        transactions = transactions.filter(created_at__date__gte=request.GET.get('from_date'))
    if request.GET.get('to_date'):
        transactions = transactions.filter(created_at__date__lte=request.GET.get('to_date'))
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Transaction ID', 'Type', 'Member', 'Amount', 'Method', 'Reference', 'Description'])
    
    for transaction in transactions:
        writer.writerow([
            transaction.created_at.strftime('%Y-%m-%d %H:%M'),
            transaction.transaction_id,
            transaction.get_transaction_type_display(),
            transaction.veteran.name if transaction.veteran else 'N/A',
            transaction.amount,
            transaction.get_payment_method_display(),
            transaction.reference_number,
            transaction.description
        ])
    
    return response

# User Profile and Settings Views
@login_required
@rate_limit(max_requests=10, window=300)
def user_profile(request):
    """User profile page"""
    if request.method == 'POST':
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        user = request.user
        email = escape(request.POST.get('email', '').strip())
        first_name = escape(request.POST.get('first_name', '').strip())
        last_name = escape(request.POST.get('last_name', '').strip())
        
        # Handle profile photo upload
        if 'profile_photo' in request.FILES:
            profile_photo = request.FILES['profile_photo']
            # Check if user has veteran profile or state profile
            if hasattr(user, 'veteran_profile'):
                veteran = user.veteran_profile.veteran_member
                veteran.profile_photo = profile_photo
                veteran.save()
            elif hasattr(user, 'state_profile'):
                state_profile = user.state_profile
                state_profile.profile_photo = profile_photo
                state_profile.save()
        
        # Validate email
        if email:
            try:
                validate_email(email)
                user.email = email
            except ValidationError:
                messages.error(request, 'Invalid email address.')
                return redirect('user_profile')
        
        # Validate names (max 150 chars, no special chars)
        if len(first_name) > 150 or len(last_name) > 150:
            messages.error(request, 'Names must be less than 150 characters.')
            return redirect('user_profile')
        
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('user_profile')
    
    return render(request, 'veteran_app/user_profile.html')

@login_required
def user_settings(request):
    """User settings page"""
    return render(request, 'veteran_app/user_settings.html')

@login_required
@rate_limit(max_requests=3, window=300)
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        from django.contrib.auth import update_session_auth_hash
        from django.contrib.auth.forms import PasswordChangeForm
        
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('user_settings')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    
    return redirect('user_settings')

@login_required
def update_preferences(request):
    """Update user preferences"""
    if request.method == 'POST':
        messages.success(request, 'Preferences updated successfully!')
    
    return redirect('user_settings')

# EVENT MANAGEMENT VIEWS
@login_required
def events_list(request):
    """List all events"""
    from django.utils import timezone
    from django.core.paginator import Paginator
    
    # Get user's state if applicable
    user_state = None
    if not request.user.is_superuser:
        try:
            user_state = request.user.state_profile.state
        except:
            try:
                veteran_user = request.user.veteran_profile
                user_state = veteran_user.veteran_member.state
            except:
                pass
    
    # Filter events based on user permissions
    if request.user.is_superuser:
        events_list = Event.objects.filter(status='published')
    elif user_state:
        # Show events created by admin (created_by is superuser) OR events for user's state
        events_list = Event.objects.filter(
            status='published'
        ).filter(
            django_models.Q(state=user_state) | 
            django_models.Q(state__isnull=True) |
            django_models.Q(created_by__is_superuser=True)
        )
    else:
        # Non-state users see only admin events (no state assigned)
        events_list = Event.objects.filter(
            status='published',
            created_by__is_superuser=True
        )
    
    # Filter to show only upcoming events (start_date >= today)
    events_list = events_list.filter(start_date__gte=timezone.now().date()).order_by('start_date')
    categories = EventCategory.objects.filter(is_active=True)
    
    paginator = Paginator(events_list, 12)  # 12 per page
    page_number = request.GET.get('page')
    events = paginator.get_page(page_number)
    
    return render(request, 'veteran_app/events_list.html', {
        'events': events,
        'categories': categories,
        'page_obj': events
    })

@login_required
def event_detail(request, event_id):
    """Event detail and registration"""
    event = get_object_or_404(Event, id=event_id, status='published')
    
    # Check if user can register
    can_register = False
    existing_registration = None
    
    if hasattr(request.user, 'veteran_profile'):
        try:
            veteran_user = request.user.veteran_profile
            if veteran_user.approved:
                veteran = veteran_user.veteran_member
                existing_registration = EventRegistration.objects.filter(
                    event=event, veteran=veteran
                ).first()
                can_register = not existing_registration and event.is_registration_open()
        except:
            pass
    
    return render(request, 'veteran_app/event_detail.html', {
        'event': event,
        'can_register': can_register,
        'existing_registration': existing_registration
    })

@login_required
def register_for_event(request, event_id):
    """Register for an event"""
    event = get_object_or_404(Event, id=event_id, status='published')
    
    try:
        veteran_user = request.user.veteran_profile
        if not veteran_user.approved:
            messages.error(request, 'Your account is pending approval.')
            return redirect('event_detail', event_id=event.id)
        veteran = veteran_user.veteran_member
    except:
        messages.error(request, 'Only veterans can register for events.')
        return redirect('event_detail', event_id=event.id)
    
    # Check if already registered
    if EventRegistration.objects.filter(event=event, veteran=veteran).exists():
        messages.warning(request, 'You are already registered for this event.')
        return redirect('event_detail', event_id=event.id)
    
    if not event.is_registration_open():
        messages.error(request, 'Registration is closed for this event.')
        return redirect('event_detail', event_id=event.id)
    
    if request.method == 'POST':
        participants_count = int(request.POST.get('participants_count', 1))
        special_requirements = request.POST.get('special_requirements', '')
        
        # Create registration
        registration = EventRegistration.objects.create(
            event=event,
            veteran=veteran,
            participants_count=participants_count,
            special_requirements=special_requirements,
            payment_required=event.registration_fee > 0,
            payment_amount=event.registration_fee * participants_count
        )
        
        # Handle payment if required
        if event.registration_fee > 0:
            try:
                from .services import PaymentService
                payment_service = PaymentService()
                payment_order, razorpay_order = payment_service.create_order(
                    veteran=veteran,
                    order_type='event_registration',
                    amount=registration.payment_amount,
                    description=f'Registration for {event.title}',
                    event_registration=registration
                )
                
                return render(request, 'veteran_app/payment_page.html', {
                    'event': event,
                    'registration': registration,
                    'payment_order': payment_order,
                    'razorpay_order': razorpay_order,
                    'razorpay_key': payment_service.gateway.api_key
                })
            except Exception as e:
                registration.delete()
                messages.error(request, f'Payment setup failed: {str(e)}')
                return redirect('event_detail', event_id=event.id)
        else:
            # Free event - confirm registration
            registration.status = 'confirmed'
            registration.save()
            messages.success(request, 'Registration successful!')
            return redirect('event_detail', event_id=event.id)
    
    return render(request, 'veteran_app/event_registration.html', {
        'event': event
    })

@login_required
def payment_success(request):
    """Handle successful payment"""
    payment_id = request.GET.get('razorpay_payment_id')
    order_id = request.GET.get('razorpay_order_id')
    signature = request.GET.get('razorpay_signature')
    
    if not all([payment_id, order_id, signature]):
        messages.error(request, 'Invalid payment response.')
        return redirect('events_list')
    
    try:
        payment_order = PaymentOrder.objects.get(gateway_order_id=order_id)
        from .services import PaymentService
        payment_service = PaymentService()
        
        if payment_service.verify_payment(payment_id, order_id, signature):
            payment_service.process_successful_payment(payment_order, payment_id)
            messages.success(request, 'Payment successful! Your registration is confirmed.')
            
            if payment_order.event_registration:
                return redirect('event_detail', event_id=payment_order.event_registration.event.id)
        else:
            messages.error(request, 'Payment verification failed.')
    except Exception as e:
        messages.error(request, f'Payment processing error: {str(e)}')
    
    return redirect('events_list')

@login_required
def payment_failed(request):
    """Handle failed payment"""
    messages.error(request, 'Payment failed. Please try again.')
    return redirect('events_list')

@login_required
def manage_events(request):
    """Manage events - Superadmin and State Admins can view events"""
    from django.core.paginator import Paginator
    
    # Get user's state if applicable
    user_state = None
    if not request.user.is_superuser:
        try:
            user_state = request.user.state_profile
            if not user_state.approved:
                messages.error(request, 'Your account is pending approval.')
                return redirect('index')
            user_state = user_state.state
        except UserState.DoesNotExist:
            messages.error(request, 'Access denied. Only state admins and superadmin can manage events.')
            return redirect('index')
    
    # Filter events based on user permissions
    if request.user.is_superuser:
        events_list = Event.objects.all()
    else:
        # State admins can see events for their state and all-state events
        events_list = Event.objects.filter(
            django_models.Q(state=user_state) | django_models.Q(state__isnull=True)
        )
    
    events_list = events_list.order_by('-created_at')
    categories = EventCategory.objects.filter(is_active=True)
    
    paginator = Paginator(events_list, 15)  # 15 per page
    page_number = request.GET.get('page')
    events = paginator.get_page(page_number)
    
    return render(request, 'veteran_app/manage_events.html', {
        'events': events,
        'categories': categories,
        'page_obj': events,
        'user_state': user_state
    })

@login_required
def create_event(request):
    """Create new event - Superadmin and State Admins"""
    # Check permissions
    user_state = None
    if not request.user.is_superuser:
        try:
            user_state = request.user.state_profile
            if not user_state.approved:
                messages.error(request, 'Your account is pending approval.')
                return redirect('index')
            user_state = user_state.state
        except UserState.DoesNotExist:
            messages.error(request, 'Access denied. Only state admins and superadmin can create events.')
            return redirect('index')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_name = request.POST.get('category', '').strip()
        state_id = request.POST.get('state')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        venue = request.POST.get('venue')
        address = request.POST.get('address')
        contact_person = request.POST.get('contact_person')
        contact_phone = request.POST.get('contact_phone')
        registration_fee = request.POST.get('registration_fee', 0)
        max_participants = request.POST.get('max_participants')
        
        if all([title, description, category_name, start_date, end_date, venue, address, contact_person, contact_phone]):
            # Get or create category
            category, created = EventCategory.objects.get_or_create(
                name=category_name,
                defaults={'is_active': True}
            )
            
            # Handle state assignment
            event_state = None
            if request.user.is_superuser:
                # Superadmin can create events for any state or all states
                event_state = State.objects.get(id=state_id) if state_id else None
            else:
                # State admins can only create events for their state
                event_state = user_state
            
            event = Event.objects.create(
                title=title,
                description=description,
                category=category,
                state=event_state,
                start_date=start_date,
                end_date=end_date,
                venue=venue,
                address=address,
                contact_person=contact_person,
                contact_phone=contact_phone,
                registration_fee=registration_fee,
                max_participants=max_participants if max_participants else None,
                banner_image=request.FILES.get('banner_image'),
                created_by=request.user,
                status='published'
            )
            
            # Create notification for the event
            from datetime import datetime, timedelta
            notification_message = f'New event "{title}" has been announced. Registration is now open!'
            if event_state:
                notification_message += f' This event is for {event_state.name} members.'
            else:
                notification_message += ' This event is open to all state members.'
            
            Notification.objects.create(
                title=f'New Event: {title}',
                message=notification_message,
                notification_type='info',
                state=event_state,
                expires_at=datetime.now() + timedelta(days=30)  # Notification expires in 30 days
            )
            
            messages.success(request, f'Event "{title}" created successfully and notification sent to members!')
            return redirect('manage_events')
        else:
            messages.error(request, 'Please fill all required fields.')
    
    # Get available states based on user permissions
    if request.user.is_superuser:
        states = State.objects.all().order_by('name')
    else:
        states = [user_state] if user_state else []
    
    return render(request, 'veteran_app/create_event.html', {
        'states': states,
        'user_state': user_state
    })

@login_required
def edit_event(request, event_id):
    """Edit existing event - Superadmin and State Admins"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check permissions
    user_state = None
    if not request.user.is_superuser:
        try:
            user_state = request.user.state_profile
            if not user_state.approved:
                messages.error(request, 'Your account is pending approval.')
                return redirect('index')
            user_state = user_state.state
            
            # State admins can only edit events for their state or all-state events
            if event.state and event.state != user_state:
                messages.error(request, 'You can only edit events for your state.')
                return redirect('manage_events')
        except UserState.DoesNotExist:
            messages.error(request, 'Access denied.')
            return redirect('index')
    
    if request.method == 'POST':
        event.title = request.POST.get('title')
        event.description = request.POST.get('description')
        category_name = request.POST.get('category', '').strip()
        state_id = request.POST.get('state')
        event.start_date = request.POST.get('start_date')
        event.end_date = request.POST.get('end_date')
        event.venue = request.POST.get('venue')
        event.address = request.POST.get('address')
        event.contact_person = request.POST.get('contact_person')
        event.contact_phone = request.POST.get('contact_phone')
        event.registration_fee = request.POST.get('registration_fee', 0)
        event.max_participants = request.POST.get('max_participants') or None
        
        if category_name:
            category, created = EventCategory.objects.get_or_create(
                name=category_name,
                defaults={'is_active': True}
            )
            event.category = category
        
        # Handle state assignment based on user permissions
        if request.user.is_superuser:
            event.state = State.objects.get(id=state_id) if state_id else None
        # State admins cannot change the state of existing events
        
        if 'banner_image' in request.FILES:
            event.banner_image = request.FILES['banner_image']
        
        event.save()
        messages.success(request, f'Event "{event.title}" updated successfully!')
        return redirect('manage_events')
    
    # Get available states based on user permissions
    if request.user.is_superuser:
        states = State.objects.all().order_by('name')
    else:
        states = [user_state] if user_state else []
    
    return render(request, 'veteran_app/edit_event.html', {
        'event': event,
        'states': states,
        'user_state': user_state
    })

@login_required
def delete_event(request, event_id):
    """Delete event - Superadmin and State Admins"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check permissions
    if not request.user.is_superuser:
        try:
            user_state = request.user.state_profile
            if not user_state.approved:
                messages.error(request, 'Your account is pending approval.')
                return redirect('index')
            
            # State admins can only delete events for their state or all-state events
            if event.state and event.state != user_state.state:
                messages.error(request, 'You can only delete events for your state.')
                return redirect('manage_events')
        except UserState.DoesNotExist:
            messages.error(request, 'Access denied.')
            return redirect('manage_events')
    
    title = event.title
    event.delete()
    messages.success(request, f'Event "{title}" deleted successfully!')
    return redirect('manage_events')

@login_required
@user_passes_test(is_superuser)
def payment_settings(request):
    """Payment gateway settings"""
    gateways = PaymentGateway.objects.all()
    
    if request.method == 'POST':
        gateway_id = request.POST.get('gateway_id')
        api_key = request.POST.get('api_key')
        secret_key = request.POST.get('secret_key')
        is_active = request.POST.get('is_active') == 'on'
        is_test_mode = request.POST.get('is_test_mode') == 'on'
        
        if gateway_id and api_key and secret_key:
            gateway = get_object_or_404(PaymentGateway, id=gateway_id)
            gateway.api_key = api_key
            gateway.secret_key = secret_key
            gateway.is_active = is_active
            gateway.is_test_mode = is_test_mode
            gateway.save()
            
            messages.success(request, f'{gateway.display_name} settings updated!')
        else:
            messages.error(request, 'Please fill all required fields.')
    
    return render(request, 'veteran_app/payment_settings.html', {
        'gateways': gateways
    })

# TWO-FACTOR AUTHENTICATION VIEWS
@login_required
def setup_2fa(request):
    """Setup 2FA for user account"""
    from .two_factor_utils import generate_secret_key, generate_totp_uri, generate_qr_code, generate_backup_codes
    from django.utils import timezone
    
    two_factor, created = TwoFactorAuth.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'generate':
            # Generate new secret key
            two_factor.secret_key = generate_secret_key()
            two_factor.save()
            messages.info(request, 'Scan the QR code with your authenticator app.')
        
        elif action == 'verify':
            from .two_factor_utils import verify_totp_code
            code = request.POST.get('code', '').strip()
            
            if verify_totp_code(two_factor.secret_key, code):
                two_factor.is_enabled = True
                two_factor.enabled_at = timezone.now()
                two_factor.backup_codes = generate_backup_codes()
                two_factor.save()
                messages.success(request, '2FA enabled successfully! Save your backup codes.')
                return redirect('view_backup_codes')
            else:
                messages.error(request, 'Invalid code. Please try again.')
        
        elif action == 'disable':
            two_factor.is_enabled = False
            two_factor.secret_key = ''
            two_factor.backup_codes = []
            two_factor.save()
            messages.warning(request, '2FA has been disabled.')
            return redirect('user_settings')
    
    # Generate QR code if secret exists
    qr_code = None
    if two_factor.secret_key:
        uri = generate_totp_uri(request.user, two_factor.secret_key)
        qr_code = generate_qr_code(uri)
    
    return render(request, 'veteran_app/setup_2fa.html', {
        'two_factor': two_factor,
        'qr_code': qr_code
    })

def verify_2fa(request):
    """Verify 2FA code during login"""
    from .two_factor_utils import verify_totp_code, verify_backup_code
    from django.utils import timezone
    
    user_id = request.session.get('2fa_user_id')
    if not user_id:
        return redirect('login')
    
    user = get_object_or_404(User, id=user_id)
    two_factor = get_object_or_404(TwoFactorAuth, user=user)
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        use_backup = request.POST.get('use_backup') == 'true'
        
        verified = False
        if use_backup:
            verified = verify_backup_code(two_factor.backup_codes, code)
            if verified:
                two_factor.save()
                messages.info(request, 'Backup code used. Please generate new backup codes.')
        else:
            verified = verify_totp_code(two_factor.secret_key, code)
        
        if verified:
            # Update last used
            two_factor.last_used = timezone.now()
            two_factor.save()
            
            # Complete login
            login(request, user)
            del request.session['2fa_user_id']
            
            # Redirect based on user role
            if user.is_superuser:
                messages.success(request, f'Welcome back, Superadmin {user.username}!')
                return redirect('index')
            
            try:
                user_state = user.state_profile
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('state_dashboard', state_id=user_state.state.id)
            except UserState.DoesNotExist:
                try:
                    veteran_user = user.veteran_profile
                    messages.success(request, f'Welcome back, {user.username}!')
                    if veteran_user.approved:
                        return redirect('veteran_dashboard')
                    else:
                        return redirect('veteran_welcome')
                except VeteranUser.DoesNotExist:
                    messages.success(request, f'Welcome back, {user.username}!')
                    return redirect('index')
        else:
            messages.error(request, 'Invalid code. Please try again.')
    
    return render(request, 'veteran_app/verify_2fa.html', {
        'user': user
    })

@login_required
def view_backup_codes(request):
    """View backup recovery codes"""
    try:
        two_factor = request.user.two_factor
        if not two_factor.is_enabled:
            messages.error(request, '2FA is not enabled.')
            return redirect('setup_2fa')
    except TwoFactorAuth.DoesNotExist:
        messages.error(request, '2FA is not set up.')
        return redirect('setup_2fa')
    
    return render(request, 'veteran_app/backup_codes.html', {
        'backup_codes': two_factor.backup_codes
    })

@login_required
def regenerate_backup_codes(request):
    """Regenerate backup codes"""
    from .two_factor_utils import generate_backup_codes
    
    if request.method == 'POST':
        try:
            two_factor = request.user.two_factor
            if two_factor.is_enabled:
                two_factor.backup_codes = generate_backup_codes()
                two_factor.save()
                messages.success(request, 'New backup codes generated successfully!')
                return redirect('view_backup_codes')
        except TwoFactorAuth.DoesNotExist:
            messages.error(request, '2FA is not set up.')
    
    return redirect('setup_2fa')

# REPORTING VIEWS
@login_required
def reports_builder(request):
    """Custom report builder"""
    # Allow superuser and accounts user
    if not (request.user.is_superuser or request.user.username == 'accounts'):
        try:
            user_state = request.user.state_profile
            if not user_state.approved:
                messages.error(request, 'Access denied.')
                return redirect('index')
        except UserState.DoesNotExist:
            messages.error(request, 'Access denied.')
            return redirect('index')
    
    user_state = None
    if not request.user.is_superuser:
        try:
            user_state = request.user.state_profile.state
        except:
            pass
    
    veteran_columns = [
        {'name': 'association_id', 'label': 'Association ID', 'type': 'text'},
        {'name': 'name', 'label': 'Name', 'type': 'text'},
        {'name': 'service_number', 'label': 'Service Number', 'type': 'text'},
        {'name': 'rank', 'label': 'Rank', 'type': 'text'},
        {'name': 'branch', 'label': 'Branch', 'type': 'text'},
        {'name': 'state', 'label': 'State', 'type': 'text'},
        {'name': 'date_of_birth', 'label': 'Date of Birth', 'type': 'date'},
        {'name': 'contact', 'label': 'Contact', 'type': 'text'},
        {'name': 'address', 'label': 'Address', 'type': 'text'},
        {'name': 'living_city', 'label': 'Living City', 'type': 'text'},
        {'name': 'zip_code', 'label': 'ZIP Code', 'type': 'text'},
        {'name': 'alternate_email', 'label': 'Alternate Email', 'type': 'text'},
        {'name': 'blood_group', 'label': 'Blood Group', 'type': 'text'},
        {'name': 'medical_category', 'label': 'Medical Category', 'type': 'text'},
        {'name': 'nearest_echs', 'label': 'Nearest ECHS', 'type': 'text'},
        {'name': 'nearest_dhq', 'label': 'Nearest DHQ', 'type': 'text'},
        {'name': 'educational_qualification', 'label': 'Educational Qualification', 'type': 'text'},
        {'name': 'living_city', 'label': 'Living City', 'type': 'text'},
        {'name': 'emergency_contact_name', 'label': 'Emergency Contact Name', 'type': 'text'},
        {'name': 'emergency_contact_phone', 'label': 'Emergency Contact Phone', 'type': 'text'},
        {'name': 'date_of_joining', 'label': 'Date of Joining', 'type': 'date'},
        {'name': 'retired_on', 'label': 'Retired On', 'type': 'date'},
        {'name': 'unit_served', 'label': 'Last Ship Served', 'type': 'text'},
        {'name': 'specialization', 'label': 'Specialization', 'type': 'text'},
        {'name': 'decorations', 'label': 'Awards & Decorations', 'type': 'text'},
        {'name': 'enrolled_date', 'label': 'Enrolled Date', 'type': 'date'},
        {'name': 'association_date', 'label': 'Association Date', 'type': 'date'},
        {'name': 'membership', 'label': 'Membership Status', 'type': 'boolean'},
        {'name': 'subscription_paid_on', 'label': 'Subscription Paid On', 'type': 'date'},
        {'name': 'spouse_name', 'label': 'Spouse Name', 'type': 'text'},
        {'name': 'spouse_contact', 'label': 'Spouse Contact', 'type': 'text'},
        {'name': 'children_count', 'label': 'Children Count', 'type': 'text'},
        {'name': 'pension_details', 'label': 'Pension Details', 'type': 'text'},
        {'name': 'bank_account', 'label': 'Bank Account', 'type': 'text'},
        {'name': 'bank_name', 'label': 'Bank Name', 'type': 'text'},
        {'name': 'next_of_kin', 'label': 'Next of Kin', 'type': 'text'},
        {'name': 'next_of_kin_relation', 'label': 'Next of Kin Relation', 'type': 'text'},
        {'name': 'next_of_kin_contact', 'label': 'Next of Kin Contact', 'type': 'text'},
        {'name': 'approved', 'label': 'Approval Status', 'type': 'boolean'},
        {'name': 'created_at', 'label': 'Created At', 'type': 'date'},
        {'name': 'updated_at', 'label': 'Updated At', 'type': 'date'},
    ]
    
    states = State.objects.all().order_by('name')
    saved_configs = ReportConfiguration.objects.filter(
        django_models.Q(created_by=request.user) | django_models.Q(is_template=True)
    )
    
    return render(request, 'veteran_app/reports_builder.html', {
        'veteran_columns': veteran_columns,
        'states': states,
        'saved_configs': saved_configs,
        'user_state': user_state
    })

@login_required
def generate_report(request):
    """Generate and download report"""
    if request.method != 'POST':
        return redirect('reports_builder')
    
    import csv
    from datetime import datetime
    
    selected_columns = request.POST.getlist('columns')
    if not selected_columns:
        messages.error(request, 'Please select at least one column.')
        return redirect('reports_builder')
    
    state_filter = request.POST.get('state_filter')
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    date_field = request.POST.get('date_field')
    membership_filter = request.POST.get('membership_filter')
    approval_filter = request.POST.get('approval_filter')
    export_format = request.POST.get('export_format', 'csv')
    
    # Validate dates don't exceed today
    today = datetime.now().date()
    if from_date:
        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
        if from_date_obj > today:
            messages.error(request, 'From Date cannot be a future date.')
            return redirect('reports_builder')
    if to_date:
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
        if to_date_obj > today:
            messages.error(request, 'To Date cannot be a future date.')
            return redirect('reports_builder')
    if from_date and to_date and from_date > to_date:
        messages.error(request, 'From Date cannot be later than To Date.')
        return redirect('reports_builder')
    
    queryset = VeteranMember.objects.all()
    
    if not request.user.is_superuser:
        try:
            user_state = request.user.state_profile.state
            queryset = queryset.filter(state=user_state)
        except:
            pass
    elif state_filter:
        queryset = queryset.filter(state_id=state_filter)
    
    if from_date and to_date and date_field:
        filter_kwargs = {f"{date_field}__range": [from_date, to_date]}
        queryset = queryset.filter(**filter_kwargs)
    
    if membership_filter:
        queryset = queryset.filter(membership=(membership_filter == 'true'))
    
    if approval_filter:
        queryset = queryset.filter(approved=(approval_filter == 'true'))
    
    queryset = queryset.select_related('state', 'rank', 'branch', 'blood_group')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="veteran_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    headers = [col.replace('_', ' ').title() for col in selected_columns]
    writer.writerow(headers)
    
    for member in queryset:
        row = []
        for col in selected_columns:
            if col == 'state':
                row.append(member.state.name)
            elif col == 'rank':
                row.append(member.rank.name)
            elif col == 'branch':
                row.append(member.branch.name)
            elif col == 'blood_group':
                row.append(member.blood_group.name)
            elif col == 'medical_category':
                row.append(member.medical_category.name if member.medical_category else member.medical_category_text or '')
            elif col == 'nearest_echs':
                row.append(member.nearest_echs.name if member.nearest_echs else member.nearest_echs_text or '')
            elif col == 'nearest_dhq':
                row.append(member.nearest_dhq_text or '')
            elif col == 'membership':
                row.append('Active' if member.membership else 'Inactive')
            elif col == 'approved':
                row.append('Approved' if member.approved else 'Pending')
            else:
                value = getattr(member, col, '')
                row.append(value if value else '')
        writer.writerow(row)
    
    return response

@login_required
def save_report_config(request):
    """Save report configuration"""
    if request.method == 'POST':
        name = request.POST.get('config_name')
        selected_columns = request.POST.getlist('columns')
        
        if name and selected_columns:
            ReportConfiguration.objects.create(
                name=name,
                description=request.POST.get('config_description', ''),
                report_type='veteran',
                selected_columns=selected_columns,
                filters={},
                created_by=request.user
            )
            messages.success(request, f'Report configuration "{name}" saved!')
        else:
            messages.error(request, 'Please provide a name and select columns.')
    
    return redirect('reports_builder')

@login_required
def load_report_config(request, config_id):
    """Load saved report configuration"""
    config = get_object_or_404(ReportConfiguration, id=config_id)
    
    if not config.is_template and config.created_by != request.user:
        messages.error(request, 'Access denied.')
        return redirect('reports_builder')
    
    return JsonResponse({
        'name': config.name,
        'columns': config.selected_columns,
        'filters': config.filters
    })

# GALLERY VIEWS
def gallery(request):
    """Public gallery view - accessible to everyone"""
    from django.db.models import Count, Sum
    from django.core.paginator import Paginator
    
    images_list = GalleryImage.objects.filter(is_public=True).select_related('state', 'uploaded_by').order_by('-created_at')
    
    # Filter by state if requested
    state_filter = request.GET.get('state')
    if state_filter:
        images_list = images_list.filter(state_id=state_filter)
    
    states = State.objects.all().order_by('name')
    
    # Calculate statistics per state
    state_stats = []
    for state in states:
        state_images = GalleryImage.objects.filter(state=state, is_public=True)
        count = state_images.count()
        total_size = sum([img.image.size for img in state_images if img.image]) / (1024 * 1024)  # MB
        if count > 0:
            state_stats.append({
                'state': state,
                'count': count,
                'size': round(total_size, 2)
            })
    
    # Check if user can upload
    can_upload = False
    if request.user.is_authenticated:
        if request.user.is_superuser:
            can_upload = True
        else:
            try:
                user_state = request.user.state_profile
                if user_state.approved:
                    can_upload = True
            except UserState.DoesNotExist:
                pass
    
    paginator = Paginator(images_list, 24)  # 24 per page (grid layout)
    page_number = request.GET.get('page')
    images = paginator.get_page(page_number)
    
    return render(request, 'veteran_app/gallery.html', {
        'images': images,
        'states': states,
        'can_upload': can_upload,
        'state_stats': state_stats,
        'page_obj': images
    })

@login_required
def upload_gallery_image(request):
    """Upload image to gallery - State admins and superuser only"""
    # Check permissions
    if not request.user.is_superuser:
        try:
            user_state = request.user.state_profile
            if not user_state.approved:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
                messages.error(request, 'Access denied.')
                return redirect('gallery')
        except UserState.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
            messages.error(request, 'Only state admins and superadmin can upload images.')
            return redirect('gallery')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        state_id = request.POST.get('state')
        image = request.FILES.get('image')
        
        if title and image:
            try:
                gallery_image = GalleryImage(
                    title=title,
                    description=description,
                    image=image,
                    uploaded_by=request.user,
                    is_public=True
                )
                
                # Set state for state admins
                if not request.user.is_superuser:
                    try:
                        user_state = request.user.state_profile
                        gallery_image.state = user_state.state
                    except UserState.DoesNotExist:
                        pass
                elif state_id:
                    gallery_image.state = State.objects.get(id=state_id)
                
                gallery_image.save()
                
                # Return JSON for AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': f'Image "{title}" uploaded successfully!'})
                
                messages.success(request, f'Image "{title}" uploaded successfully!')
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': str(e)}, status=500)
                messages.error(request, f'Error uploading image: {str(e)}')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Title and image are required'}, status=400)
            messages.error(request, 'Please provide title and image.')
    
    return redirect('gallery')

@login_required
def delete_gallery_image(request, image_id):
    """Delete gallery image - Superuser can delete any, state admins can delete their own"""
    image = get_object_or_404(GalleryImage, id=image_id)
    
    # Check permissions
    if request.user.is_superuser:
        # Superuser can delete any image
        pass
    else:
        # State admins can only delete their own images
        if image.uploaded_by != request.user:
            messages.error(request, 'You can only delete your own images.')
            return redirect('gallery')
    
    title = image.title
    image.delete()
    messages.success(request, f'Image "{title}" deleted successfully!')
    return redirect('gallery')

    # Page directive to the indexing
    ''' 
    slider =  capsule.image_Modifier("Enter the screen number")
    crud = Non_crud_modifier(" Veteran Message with contect manual")
    if user_state_login:
        call_image_Folder("capsule.image-Modifier")
        image_in_sequence_header
    '''


# VETERAN PAYMENT CRUD VIEWS
@login_required
def veteran_add_payment(request):
    """Veteran adds their own payment transaction"""
    try:
        veteran_user = request.user.veteran_profile
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Only veterans can add payments'}, status=403)
    
    if request.method == 'POST':
        import uuid
        from datetime import datetime
        from decimal import Decimal
        
        transaction_type = request.POST.get('transaction_type', 'subscription')
        amount = Decimal(request.POST.get('amount', '0'))
        payment_method = request.POST.get('payment_method', 'online')
        reference_number = request.POST.get('reference_number', '').strip()
        description = request.POST.get('description', '').strip()
        
        if amount <= 0:
            return JsonResponse({'success': False, 'error': 'Invalid amount'}, status=400)
        
        # Validate transaction type
        valid_types = ['subscription', 'donation', 'event_fee', 'crowdfunding', 'other_income']
        if transaction_type not in valid_types:
            return JsonResponse({'success': False, 'error': 'Invalid transaction type'}, status=400)
        
        # Get current financial year
        current_year = datetime.now().year
        financial_year, created = FinancialYear.objects.get_or_create(
            year=f"{current_year}-{current_year+1}",
            defaults={
                'start_date': datetime(current_year, 4, 1).date(),
                'end_date': datetime(current_year+1, 3, 31).date(),
                'is_active': True
            }
        )
        
        # Generate transaction ID
        transaction_id = f"PAY{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        
        # Create transaction
        Transaction.objects.create(
            transaction_id=transaction_id,
            veteran=veteran,
            transaction_type=transaction_type,
            amount=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            description=description or f'{transaction_type.replace("_", " ").title()} payment by {veteran.name}',
            financial_year=financial_year,
            recorded_by=request.user
        )
        
        return JsonResponse({'success': True, 'message': 'Payment added successfully!'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def veteran_edit_payment(request, transaction_id):
    """Veteran edits their own payment transaction"""
    try:
        veteran_user = request.user.veteran_profile
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
    
    transaction = get_object_or_404(Transaction, id=transaction_id, veteran=veteran)
    
    if request.method == 'POST':
        from decimal import Decimal
        
        transaction_type = request.POST.get('transaction_type', transaction.transaction_type)
        amount = Decimal(request.POST.get('amount', '0'))
        payment_method = request.POST.get('payment_method', transaction.payment_method)
        reference_number = request.POST.get('reference_number', '').strip()
        description = request.POST.get('description', '').strip()
        
        if amount <= 0:
            return JsonResponse({'success': False, 'error': 'Invalid amount'}, status=400)
        
        # Validate transaction type
        valid_types = ['subscription', 'donation', 'event_fee', 'crowdfunding', 'other_income']
        if transaction_type not in valid_types:
            return JsonResponse({'success': False, 'error': 'Invalid transaction type'}, status=400)
        
        transaction.transaction_type = transaction_type
        transaction.amount = amount
        transaction.payment_method = payment_method
        transaction.reference_number = reference_number
        transaction.description = description
        transaction.save()
        
        return JsonResponse({'success': True, 'message': 'Payment updated successfully!'})
    
    # Return transaction data for modal
    return JsonResponse({
        'id': transaction.id,
        'transaction_type': transaction.transaction_type,
        'amount': str(transaction.amount),
        'payment_method': transaction.payment_method,
        'reference_number': transaction.reference_number,
        'description': transaction.description
    })

@login_required
def veteran_delete_payment(request, transaction_id):
    """Veteran deletes their own payment transaction"""
    try:
        veteran_user = request.user.veteran_profile
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
    
    transaction = get_object_or_404(Transaction, id=transaction_id, veteran=veteran)
    transaction.delete()
    
    return JsonResponse({'success': True, 'message': 'Payment deleted successfully!'})

# ASSOCIATION ID CARD VIEWS
@login_required
def association_id_card(request):
    """Display Association Identity Card for approved veterans"""
    try:
        veteran_user = request.user.veteran_profile
        if not veteran_user.approved:
            messages.error(request, 'Your account is pending approval. You cannot access the ID card.')
            return redirect('veteran_welcome')
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Only approved veterans can access the Association ID Card.')
        return redirect('index')
    
    # Generate association number if not exists
    if not veteran.association_number:
        veteran.generate_association_number()
        veteran.save()
    
    # Check if ID card is valid (not expired)
    is_valid = veteran.is_id_card_valid()
    renewal_due_date = veteran.get_renewal_due_date()
    
    # Terms and conditions for the back of the card
    terms_conditions = [
        "1. This card is the property of the Indian Coast Guard Veteran Welfare Association (ICGVWA).",
        "2. This card is non-transferable and must be carried by the member at all times during association events.",
        "3. Loss of this card must be reported immediately to the state association office.",
        "4. This card is valid for one year and must be renewed annually.",
        "5. The member agrees to abide by the constitution and by-laws of ICGVWA.",
        "6. Any misuse of this card will result in immediate cancellation of membership.",
        "7. The association reserves the right to verify the authenticity of this card at any time.",
        "8. For any queries or assistance, contact your state head (or) Admin Staff."
    ]
    
    # Issuing authority information
    issuing_authority = {
        'title': 'Secretary',
        'organization': 'Indian Coast Guard Veteran Welfare Association',
        'signature_line': 'Authorized Signature'
    }
    
    return render(request, 'veteran_app/association_id_card.html', {
        'veteran': veteran,
        'is_valid': is_valid,
        'renewal_due_date': renewal_due_date,
        'terms_conditions': terms_conditions,
        'issuing_authority': issuing_authority
    })

@login_required
def download_id_card(request):
    """Download Association ID Card as PDF in A4 format"""
    try:
        veteran_user = request.user.veteran_profile
        if not veteran_user.approved:
            messages.error(request, 'Your account is pending approval.')
            return redirect('veteran_welcome')
        veteran = veteran_user.veteran_member
    except VeteranUser.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    from django.http import HttpResponse
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch, cm
    from reportlab.lib.colors import black, blue, red, white
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib import colors
    from io import BytesIO
    import os
    
    # Create PDF buffer
    buffer = BytesIO()
    
    # Create A4 PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           rightMargin=2*cm, leftMargin=2*cm, 
                           topMargin=2*cm, bottomMargin=2*cm)
    
    # Container for the 'Flowable' objects
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles for A4 ID card
    title_style = styles['Title']
    title_style.textColor = blue
    title_style.fontSize = 16
    title_style.spaceAfter = 12
    title_style.alignment = 1  # Center
    
    heading_style = styles['Heading2']
    heading_style.textColor = black
    heading_style.fontSize = 14
    heading_style.spaceAfter = 12
    heading_style.alignment = 1  # Center
    
    normal_style = styles['Normal']
    normal_style.fontSize = 12
    normal_style.spaceAfter = 6
    
    small_style = styles['Normal']
    small_style.fontSize = 10
    small_style.spaceAfter = 4
    
    # HEADER
    elements.append(Paragraph("<b>INDIAN COAST GUARD VETERAN WELFARE ASSOCIATION</b>", title_style))
    elements.append(Paragraph("<b>ASSOCIATION IDENTITY CARD</b>", heading_style))
    elements.append(Spacer(1, 1*cm))
    
    # MEMBER INFORMATION TABLE
    photo_cell = "No Photo"
    if veteran.profile_photo:
        try:
            photo_path = veteran.profile_photo.path
            if os.path.exists(photo_path):
                photo_cell = Image(photo_path, width=4*cm, height=5*cm)
        except:
            pass
    
    # Member details
    member_data = [
        ['Association Number:', veteran.association_number or 'Not Assigned'],
        ['Name:', veteran.name],
        ['Rank:', f"{veteran.rank.name} (Retd.)"],
        ['Service Number:', veteran.service_number],
        ['State:', veteran.state.name],
        ['Blood Group:', veteran.blood_group.name],
        ['Contact:', veteran.contact],
        ['Date of Birth:', veteran.date_of_birth.strftime('%d-%m-%Y')],
        ['Association Date:', veteran.association_date.strftime('%d-%m-%Y') if veteran.association_date else 'N/A'],
    ]
    
    # Create main table with photo and details
    main_table_data = [[photo_cell, Table(member_data, colWidths=[4*cm, 8*cm])]]
    main_table = Table(main_table_data, colWidths=[5*cm, 12*cm])
    main_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (1, 0), (1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    elements.append(main_table)
    elements.append(Spacer(1, 1*cm))
    
    # VALIDITY INFORMATION
    renewal_date = veteran.get_renewal_due_date()
    validity_text = f"Valid until: {renewal_date.strftime('%d-%m-%Y')}" if renewal_date else "Validity: Contact Association"
    elements.append(Paragraph(f"<b>{validity_text}</b>", normal_style))
    
    status = "VALID" if veteran.is_id_card_valid() else "EXPIRED"
    elements.append(Paragraph(f"<b>STATUS: {status}</b>", normal_style))
    elements.append(Spacer(1, 1*cm))
    
    # TERMS AND CONDITIONS
    elements.append(Paragraph("<b>TERMS AND CONDITIONS</b>", heading_style))
    
    terms = [
        "1. This card is the property of the Indian Coast Guard Veteran Welfare Association (ICGVWA).",
        "2. This card is non-transferable and must be carried by the member at all times during association events.",
        "3. Loss of this card must be reported immediately to the state association office.",
        "4. This card is valid for one year and must be renewed annually.",
        "5. The member agrees to abide by the constitution and by-laws of ICGVWA.",
        "6. Any misuse of this card will result in immediate cancellation of membership."
    ]
    
    for term in terms:
        elements.append(Paragraph(term, small_style))
    
    elements.append(Spacer(1, 1*cm))
    
    # ISSUING AUTHORITY
    authority_text = f"""<b>ISSUING AUTHORITY</b><br/>
Indian Coast Guard Veteran Welfare Association<br/>
{veteran.state.name} Chapter<br/>
Issue Date: {veteran.association_date.strftime('%d-%m-%Y') if veteran.association_date else 'N/A'}<br/>
<br/>
_________________________<br/>
Secretary, ICGVWA {veteran.state.name}"""
    
    elements.append(Paragraph(authority_text, normal_style))
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    # Create response
    response = HttpResponse(pdf_data, content_type='application/pdf')
    filename = f"ICGVWA_ID_Card_{veteran.association_number or veteran.service_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
