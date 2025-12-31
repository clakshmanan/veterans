from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
import random

from veteran_app.models import (
    State,
    Rank,
    Branch, 
    # Group,
    BloodGroup,
    VeteranMember,
)


class Command(BaseCommand):
    help = "Seed a few sample VeteranMember rows per state to demonstrate the UI. Creates a regular demo user if none exists."

    def add_arguments(self, parser):
        parser.add_argument(
            "--per-state",
            type=int,
            default=5,
            help="Number of members to create per state (default: 5)",
        )

    def handle(self, *args, **options):
        per_state = options["per_state"]

        # Ensure there is at least one regular user to attribute created_by
        demo_username = "demo"
        demo_password = "demo12345"
        demo_user, created_user = User.objects.get_or_create(
            username=demo_username,
            defaults={
                "is_staff": False,
                "is_superuser": False,
                "email": "demo@example.com",
            },
        )
        if created_user:
            demo_user.set_password(demo_password)
            demo_user.save()
            self.stdout.write(self.style.WARNING(
                f"Created demo user -> username: {demo_username}, password: {demo_password}"
            ))

        # Collections
        ranks = list(Rank.objects.all())
        branches = list(Branch.objects.all())
        blood_branches = list(BloodGroup.objects.all())
        states = list(State.objects.all())

        # If any of the master data sets are empty, bail with instruction
        if not ranks or not branches or not blood_branches or not states:
            self.stdout.write(self.style.ERROR(
                "Missing master data. Run 'python manage.py seed_data' first to create States, Ranks, branches, and Bloodbranches."
            ))
            return

        first_names = [
            "Arjun", "Ravi", "Rahul", "Sanjay", "Vivek", "Amit", "Rakesh", "Suresh", "Manoj", "Vikram",
            "Karan", "Deepak", "Rohit", "Vikas", "Naveen", "Sunil", "Harish", "Anil", "Pawan", "Prakash",
        ]
        last_names = [
            "Singh", "Kumar", "Sharma", "Patel", "Gupta", "Yadav", "Reddy", "Das", "Nair", "Bose",
            "Chauhan", "Verma", "Mishra", "Ghosh", "Mehta", "Jain", "Agarwal", "Thakur", "Bhat", "Shetty",
        ]

        created_total = 0
        today = date.today()

        for state in states:
            existing = VeteranMember.objects.filter(state=state).count()
            to_create = max(0, per_state - existing)
            if to_create == 0:
                continue

            for i in range(to_create):
                name = f"{random.choice(first_names)} {random.choice(last_names)}"
                rank = random.choice(ranks)
                branch = random.choice(branches)
                bgroup = random.choice(blood_branches)

                # Generate plausible dates
                dob = today - timedelta(days=365 * random.randint(35, 60))
                enrolled = dob + timedelta(days=365 * random.randint(18, 25))
                joined = enrolled + timedelta(days=random.randint(30, 365))
                retired = joined + timedelta(days=365 * random.randint(10, 25))
                assoc_date = retired + timedelta(days=random.randint(1, 365))
                sub_paid = assoc_date + timedelta(days=random.randint(0, 365))

                # Unique-ish P number
                p_number = f"{state.code}-{random.randint(10000, 99999)}{random.randint(100, 999)}"
                
                # Generate unique service number
                service_num = f"{random.randint(10000, 99999)}-{random.choice(['A', 'B', 'C', 'D', 'E'])}"

                contact = f"+91{random.randint(6000000000, 9999999999)}"
                address = f"{random.randint(10, 299)}, MG Road, {state.name}"

                member = VeteranMember(
                    state=state,
                    enrolled_date=enrolled,
                    name=name,
                    rank=rank,
                    branch=branch,
                    service_number=service_num,
                    p_number=p_number,
                    date_of_birth=dob,
                    blood_group=bgroup,
                    contact=contact,
                    address=address,
                    date_of_joining=joined,
                    retired_on=retired,
                    unit_served=f"INS {random.choice(['Vikrant', 'Vikramaditya', 'Shivalik', 'Kolkata', 'Chennai'])}",
                    nearest_dhq_text=f"DHQ {state.name}",
                    association_date=assoc_date,
                    membership=random.choice([True, False]),
                    subscription_paid_on=sub_paid,
                    spouse_name=f"{random.choice(['Priya', 'Anjali', 'Kavita', 'Sunita', 'Meera'])} {random.choice(last_names)}",
                    created_by=demo_user,
                    approved=random.choice([True, False]),
                )
                member.save()
                created_total += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeded sample veteran members. Newly created: {created_total}"
        ))
