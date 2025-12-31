from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from veteran_app.models import UserState, VeteranMember

class Command(BaseCommand):
    help = 'Fix permissions for state admin users'

    def handle(self, *args, **options):
        # Get VeteranMember content type
        veteran_content_type = ContentType.objects.get_for_model(VeteranMember)
        
        # Get or create permissions
        permissions = []
        permission_codenames = [
            'view_veteranmember',
            'add_veteranmember', 
            'change_veteranmember',
            'delete_veteranmember'
        ]
        
        for codename in permission_codenames:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=veteran_content_type,
                defaults={'name': f'Can {codename.split("_")[0]} veteran member'}
            )
            permissions.append(permission)
            if created:
                self.stdout.write(f'Created permission: {permission.name}')
        
        # Assign permissions to all state admin users
        state_users = UserState.objects.filter(approved=True)
        
        for user_state in state_users:
            user = user_state.user
            # Add permissions to user
            for permission in permissions:
                user.user_permissions.add(permission)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Added permissions to state admin: {user.username} ({user_state.state.name})'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated permissions for {state_users.count()} state admin users'
            )
        )