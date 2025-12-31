from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import State, VeteranMember, VeteranUser, Rank, Group, BloodGroup
from datetime import date
import random

@receiver(post_save, sender=State)
def setup_state_chat_functionality(sender, instance, created, **kwargs):
    """
    Automatically setup chat functionality when a new state is created
    by ensuring it has at least one approved veteran with user account
    """
    if created:
        # Get or create system user
        system_user, user_created = User.objects.get_or_create(
            username='system_auto',
            defaults={
                'is_staff': False,
                'is_superuser': False,
                'email': 'system_auto@example.com'
            }
        )
        if user_created:
            system_user.set_password('system123')
            system_user.save()
        
        # Check if we have master data
        default_rank = Rank.objects.first()
        default_group = Group.objects.first()
        default_blood_group = BloodGroup.objects.first()
        
        if default_rank and default_group and default_blood_group:
            # Generate unique service number
            service_number = f"{random.randint(10000, 99999)}-{random.choice(['A', 'B', 'C', 'D'])}"
            while VeteranMember.objects.filter(service_number=service_number).exists():
                service_number = f"{random.randint(10000, 99999)}-{random.choice(['A', 'B', 'C', 'D'])}"
            
            # Create veteran member for new state
            veteran = VeteranMember.objects.create(
                state=instance,
                enrolled_date=date.today(),
                name=f"Auto User {instance.code}",
                service_number=service_number,
                rank=default_rank,
                group=default_group,
                date_of_birth=date(1980, 1, 1),
                blood_group=default_blood_group,
                contact=f"+91{random.randint(6000000000, 9999999999)}",
                address=f"Auto Address, {instance.name}",
                date_of_joining=date(2000, 1, 1),
                retired_on=date(2020, 1, 1),
                unit_served=f"Auto Unit {instance.code}",
                nearest_dhq_text=f"DHQ {instance.name}",
                association_date=date.today(),
                spouse_name="Auto Spouse",
                approved=True,
                created_by=system_user
            )
            
            # Create user account
            username = f"auto_{instance.code.lower()}"
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'is_staff': False,
                    'is_superuser': False
                }
            )
            if user_created:
                user.set_password('auto123')
                user.save()
            
            # Create veteran user account
            VeteranUser.objects.get_or_create(
                user=user,
                veteran_member=veteran,
                defaults={
                    'approved': True,
                    'created_by_admin': True
                }
            )