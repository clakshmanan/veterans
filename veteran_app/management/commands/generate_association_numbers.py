from django.core.management.base import BaseCommand
from veteran_app.models import VeteranMember

class Command(BaseCommand):
    help = 'Generate association numbers for existing veterans who do not have one'

    def handle(self, *args, **options):
        veterans_without_numbers = VeteranMember.objects.filter(association_number__isnull=True)
        count = 0
        
        for veteran in veterans_without_numbers:
            if veteran.state:  # Only generate if veteran has a state
                veteran.generate_association_number()
                veteran.save(update_fields=['association_number'])
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Generated association number {veteran.association_number} for {veteran.name}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated association numbers for {count} veterans'
            )
        )