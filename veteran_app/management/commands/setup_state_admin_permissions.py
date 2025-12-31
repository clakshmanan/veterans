from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from veteran_app.models import VeteranMember, UserState, State


class Command(BaseCommand):
    help = 'Set up State Admins group with proper permissions and add all state users to it'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        # Get or create State Admins group
        group_name = 'State Admins'
        if dry_run:
            try:
                group = Group.objects.get(name=group_name)
                self.stdout.write(f'Found existing group: {group_name}')
            except Group.DoesNotExist:
                self.stdout.write(f'Would create group: {group_name}')
                group = None
        else:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created group: {group_name}')
                )
            else:
                self.stdout.write(f'Using existing group: {group_name}')

        # Define required permissions for state admins
        permission_codenames = [
            'add_veteranmember',
            'change_veteranmember', 
            'view_veteranmember',
            'delete_veteranmember',
        ]
        
        # Get VeteranMember content type
        try:
            veteran_content_type = ContentType.objects.get_for_model(VeteranMember)
        except ContentType.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('VeteranMember content type not found')
            )
            return

        # Get permissions
        permissions = []
        for codename in permission_codenames:
            try:
                perm = Permission.objects.get(
                    codename=codename, 
                    content_type=veteran_content_type
                )
                permissions.append(perm)
                if dry_run:
                    self.stdout.write(f'Found permission: {perm.name}')
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Permission not found: {codename}')
                )

        # Add permissions to group
        if not dry_run and group and permissions:
            group.permissions.set(permissions)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Added {len(permissions)} permissions to {group_name} group'
                )
            )
        elif dry_run:
            self.stdout.write(
                f'Would add {len(permissions)} permissions to {group_name} group'
            )

        # Find all state users (users with UserState profile)
        state_users = User.objects.filter(
            state_profile__isnull=False
        ).select_related('state_profile', 'state_profile__state')
        
        if not state_users.exists():
            self.stdout.write(
                self.style.WARNING('No state users found with UserState profiles')
            )
            return

        self.stdout.write(f'Found {state_users.count()} state users:')
        
        # Add each state user to the group
        added_count = 0
        for user in state_users:
            state_name = user.state_profile.state.name if user.state_profile.state else 'Unknown'
            approved_status = 'Approved' if user.state_profile.approved else 'Pending'
            
            if dry_run:
                in_group = group and user.groups.filter(name=group_name).exists() if group else False
                status = 'Already in group' if in_group else 'Would be added to group'
                self.stdout.write(
                    f'  - {user.username} ({state_name}) [{approved_status}] - {status}'
                )
            else:
                user.groups.add(group)
                added_count += 1
                self.stdout.write(
                    f'  - {user.username} ({state_name}) [{approved_status}] - Added to group'
                )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully added {added_count} state users to {group_name} group'
                )
            )

        # Show summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('SUMMARY:')
        self.stdout.write(f'Group: {group_name}')
        self.stdout.write(f'Permissions: {len(permissions)} veteran management permissions')
        self.stdout.write(f'Users: {state_users.count()} state users')
        
        if dry_run:
            self.stdout.write('\nTo apply these changes, run:')
            self.stdout.write('python manage.py setup_state_admin_permissions')
        else:
            self.stdout.write(
                self.style.SUCCESS('\nState admin permissions setup complete!')
            )
            self.stdout.write('\nState users can now:')
            self.stdout.write('  - Add new veteran members')
            self.stdout.write('  - Edit existing veteran members')
            self.stdout.write('  - View veteran member details')
            self.stdout.write('  - Delete veteran members (if needed)')
            
        self.stdout.write('='*50)