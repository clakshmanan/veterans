from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db import models as django_models
from .models import Event, EventCategory, EventRegistration, PaymentOrder, State
from .services import PaymentService

def is_superuser(user):
    return user.is_superuser

@login_required
def events_list(request):
    """List all events"""
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
        events = Event.objects.filter(status='published')
    elif user_state:
        events = Event.objects.filter(
            status='published'
        ).filter(
            django_models.Q(state=user_state) | django_models.Q(state__isnull=True)
        )
    else:
        events = Event.objects.filter(status='published', state__isnull=True)
    
    events = events.order_by('start_date')
    categories = EventCategory.objects.filter(is_active=True)
    
    return render(request, 'veteran_app/events_list.html', {
        'events': events,
        'categories': categories
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
@user_passes_test(is_superuser)
def manage_events(request):
    """Manage events - Admin only"""
    events = Event.objects.all().order_by('-created_at')
    categories = EventCategory.objects.filter(is_active=True)
    
    return render(request, 'veteran_app/manage_events.html', {
        'events': events,
        'categories': categories
    })

@login_required
@user_passes_test(is_superuser)
def create_event(request):
    """Create new event"""
    if request.method == 'POST':
        from datetime import datetime
        
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        state_id = request.POST.get('state')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        venue = request.POST.get('venue')
        address = request.POST.get('address')
        contact_person = request.POST.get('contact_person')
        contact_phone = request.POST.get('contact_phone')
        registration_fee = request.POST.get('registration_fee', 0)
        max_participants = request.POST.get('max_participants')
        
        if all([title, description, category_id, start_date, end_date, venue, address, contact_person, contact_phone]):
            # Validate dates
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                today = datetime.now().date()
                
                if start_dt < today:
                    messages.error(request, 'Event start date cannot be in the past.')
                    return redirect('create_event')
                
                if end_dt < start_dt:
                    messages.error(request, 'Event end date must be after start date.')
                    return redirect('create_event')
                    
            except ValueError:
                messages.error(request, 'Invalid date format.')
                return redirect('create_event')
            
            category = get_object_or_404(EventCategory, id=category_id)
            state = State.objects.get(id=state_id) if state_id else None
            
            event = Event.objects.create(
                title=title,
                description=description,
                category=category,
                state=state,
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
            
            messages.success(request, f'Event "{title}" created successfully!')
            return redirect('manage_events')
        else:
            messages.error(request, 'Please fill all required fields.')
    
    categories = EventCategory.objects.filter(is_active=True)
    states = State.objects.all().order_by('name')
    
    return render(request, 'veteran_app/create_event.html', {
        'categories': categories,
        'states': states
    })