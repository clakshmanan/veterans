from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create a superuser automatically'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='lakshmanan',
                email='clakshmanan2023@gmail.com',
                password='clak#123'
            )
            self.stdout.write(
                self.style.SUCCESS('Superuser "admin" created successfully!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Superuser "admin" already exists.')
            )