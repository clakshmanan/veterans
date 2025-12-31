from datetime import date
from django.utils import timezone
from .models import Notification, VeteranMember

def global_announcements(request):
    """Add global announcements to all templates"""
    today = date.today()
    now = timezone.now()
    
    # Get today's birthdays
    birthdays = VeteranMember.objects.filter(
        date_of_birth__month=today.month,
        date_of_birth__day=today.day,
        approved=True
    ).select_related('rank', 'state')[:5]
    
    # Get active notifications (not expired)
    notifications = Notification.objects.filter(
        is_active=True,
        expires_at__gte=now
    ).order_by('-created_at')[:10]
    
    return {
        'global_birthdays': birthdays,
        'global_notifications': notifications
    }
