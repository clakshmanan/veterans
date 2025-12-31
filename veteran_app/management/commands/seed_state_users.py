from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from veteran_app.models import State, UserState


class Command(BaseCommand):
    help = "Create one regular login user per State with deterministic credentials. Passwords are reset each run."

    def handle(self, *args, **options):
        states = State.objects.order_by('name')
        if not states.exists():
            self.stdout.write(self.style.ERROR(
                "No states found. Run 'python manage.py seed_data' first."
            ))
            return

        self.stdout.write("\nState-wise Credentials (users created or updated):\n")
        self.stdout.write("Username, Password, State Name, State Code")
        for s in states:
            username = f"state_{s.code.lower()}"
            password = f"State{s.code.upper()}!123"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'is_active': True,
                    'is_staff': False,
                    'is_superuser': False,
                    'email': f'{username}@example.com',
                }
            )
            # Reset password deterministically so we can share credentials
            user.set_password(password)
            user.save()
            # Ensure UserState mapping exists and is correct
            mapping, _ = UserState.objects.get_or_create(
                user=user, 
                defaults={'state': s, 'approved': True}  # Auto-approve seeded users
            )
            if mapping.state_id != s.id:
                mapping.state = s
                mapping.save(update_fields=["state"])
            # Ensure seeded users are approved
            if not mapping.approved:
                mapping.approved = True
                mapping.save(update_fields=["approved"])

            self.stdout.write(f"{username}, {password}, {s.name}, {s.code}")

        self.stdout.write(self.style.SUCCESS("\nState users created/updated successfully."))
