from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from veteran_app.models import *

class Command(BaseCommand):
    help = 'Clear all table data except superuser'

    def handle(self, *args, **options):
        # Clear all veteran app models
        VeteranUser.objects.all().delete()
        VeteranMember.objects.all().delete()
        UserState.objects.all().delete()
        Child.objects.all().delete()
        JobPortal.objects.all().delete()
        Matrimonial.objects.all().delete()
        ChatRequest.objects.all().delete()
        ChatMessage.objects.all().delete()
        Document.objects.all().delete()
        Notification.objects.all().delete()
        CarouselSlide.objects.all().delete()
        Message.objects.all().delete()
        
        # Clear non-superuser accounts
        User.objects.filter(is_superuser=False).delete()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully cleared all data except superuser')
        )