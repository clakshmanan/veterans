from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from veteran_app.models import State, VeteranMember, VeteranUser, Rank, Group, BloodGroup
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Fix chat portal functionality across all states by ensuring approved veterans with user accounts exist'

    def handle(self, *args, **options):
        # Get all states
        states = State.objects.all()
        
        # Ensure we have master data
        if not Rank.objects.exists() or not Group.objects.exists() or not BloodGroup.objects.exists():
            self.stdout.write(self.style.ERROR('Master data missing. Run seed_data command first.'))
            return
        
        default_rank = Rank.objects.first()
        default_group = Group.objects.first()
        default_blood_group = BloodGroup.objects.first()
        
        # Create a system user for creating veterans if needed
        system_user, created = User.objects.get_or_create(
            username='system_chat',
            defaults={
                'is_staff': False,
                'is_superuser': False,
                'email': 'system@example.com'
            }
        )
        if created:
            system_user.set_password('system123')
            system_user.save()
        
        fixed_states = []
        
        for state in states:
            # Check if state has approved veterans with user accounts
            approved_veterans_with_accounts = VeteranUser.objects.filter(
                veteran_member__state=state,
                veteran_member__approved=True,
                approved=True
            ).count()
            
            if approved_veterans_with_accounts == 0:
                # Create at least one approved veteran with user account for this state
                service_number = f"{random.randint(10000, 99999)}-{random.choice(['A', 'B', 'C', 'D'])}"
                
                # Check if service number already exists
                while VeteranMember.objects.filter(service_number=service_number).exists():
                    service_number = f"{random.randint(10000, 99999)}-{random.choice(['A', 'B', 'C', 'D'])}"
                
                # Create veteran member
                veteran = VeteranMember.objects.create(
                    state=state,
                    enrolled_date=date.today(),
                    name=f"Chat User {state.code}",
                    service_number=service_number,
                    rank=default_rank,
                    group=default_group,
                    date_of_birth=date(1980, 1, 1),
                    blood_group=default_blood_group,
                    contact=f"+91{random.randint(6000000000, 9999999999)}",
                    address=f"Address, {state.name}",
                    date_of_joining=date(2000, 1, 1),
                    retired_on=date(2020, 1, 1),
                    unit_served=f"Unit {state.code}",
                    nearest_dhq_text=f"DHQ {state.name}",
                    association_date=date.today(),
                    spouse_name="Spouse Name",
                    approved=True,
                    created_by=system_user
                )
                
                # Create user account for veteran
                username = f"veteran_{state.code.lower()}"
                user, user_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': f'{username}@example.com',
                        'is_staff': False,
                        'is_superuser': False
                    }
                )
                if user_created:
                    user.set_password('veteran123')
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
                
                fixed_states.append(state.name)
                self.stdout.write(f"Fixed chat portal for {state.name} - created veteran user: {username}")
        
        if fixed_states:
            self.stdout.write(self.style.SUCCESS(f"Chat portal fixed for {len(fixed_states)} states: {', '.join(fixed_states)}"))
        else:
            self.stdout.write(self.style.SUCCESS("All states already have chat portal functionality enabled"))
        
        # Summary
        total_veterans = VeteranMember.objects.filter(approved=True).count()
        veterans_with_accounts = VeteranUser.objects.filter(approved=True).count()
        
        self.stdout.write(f"\nSummary:")
        self.stdout.write(f"Total approved veterans: {total_veterans}")
        self.stdout.write(f"Veterans with user accounts: {veterans_with_accounts}")
        self.stdout.write(f"States with chat functionality: {states.count()}")