from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from veteran_app.models import AccountsUser

class Command(BaseCommand):
    help = 'Create accounts user for financial management'

    def handle(self, *args, **options):
        # Create accounts user
        username = 'accounts'
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                password='accounts123',  # Default password - superadmin should change
                email='accounts@icgvwa.org',
                first_name='Accounts',
                last_name='Manager'
            )
            
            # Create AccountsUser profile
            AccountsUser.objects.create(
                user=user,
                approved=True,  # Auto-approved
                full_name='Accounts Manager',
                designation='Treasurer',
                email='accounts@icgvwa.org'
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created accounts user: {username}\n'
                    f'Password: accounts123 (Please change this immediately)\n'
                    f'This user can only access Accounts menu (Reports & Treasurer)'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Accounts user "{username}" already exists')
            )