from django.core.management.base import BaseCommand
from veteran_app.models import Rank, Branch
import os

class Command(BaseCommand):
    help = 'Load initial data from text file'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, default='initial_data.txt', help='Path to the text file containing data')

    def handle(self, *args, **options):
        file_path = options['file']
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = [line.strip() for line in file.readlines()]
                
            current_section = None
            ranks_added = 0
            groups_added = 0
            
            for line in lines:
                if not line:
                    continue
                    
                if line.upper() == 'RANKS':
                    current_section = 'RANKS'
                    continue
                elif line.upper() == 'BRANCHES':
                    current_section = 'BRANCHES'
                    continue
                elif line.upper() == 'PERSONNEL_NUMBERS':
                    current_section = 'PERSONNEL_NUMBERS'
                    continue
                
                if current_section == 'RANKS':
                    rank, created = Rank.objects.get_or_create(name=line)
                    if created:
                        ranks_added += 1
                        self.stdout.write(f'Added rank: {line}')
                
                elif current_section == 'BRANCHES':
                    branch, created = Branch.objects.get_or_create(name=line)
                    if created:
                        branches_added += 1
                        self.stdout.write(f'Added branch: {line}')
                        
                elif current_section == 'PERSONNEL_NUMBERS':
                    self.stdout.write(f'Personnel number noted: {line}')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully loaded {ranks_added} ranks and {branches_added} groups'
                )
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading data: {str(e)}'))