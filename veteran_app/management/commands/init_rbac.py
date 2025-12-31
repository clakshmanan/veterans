from django.core.management.base import BaseCommand
from veteran_app.rbac_utils import create_default_permissions, create_default_roles

class Command(BaseCommand):
    help = 'Initialize RBAC system with default permissions and roles'

    def handle(self, *args, **options):
        self.stdout.write('Initializing RBAC system...')
        
        # Create permissions
        permissions = create_default_permissions()
        self.stdout.write(f'Created {len(permissions)} permissions')
        
        # Create roles
        roles = create_default_roles()
        self.stdout.write(f'Created {len(roles)} roles')
        
        self.stdout.write(
            self.style.SUCCESS('RBAC system initialized successfully!')
        )