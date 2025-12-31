#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veteran_project.settings')
django.setup()

from veteran_app.models import MedicalCategory

# Medical categories data
medical_categories = [
    ("S1A1", "Fit for all duties"),
    ("S1A2", "Fit for all duties with minor restrictions"),
    ("S2A2", "Fit for limited duties"),
    ("S2A3", "Fit for limited duties with restrictions"),
    ("S3A3", "Temporarily unfit"),
    ("S4A4", "Permanently unfit for service"),
]

print("Adding medical categories...")
for name, desc in medical_categories:
    obj, created = MedicalCategory.objects.get_or_create(name=name, defaults={'description': desc})
    if created:
        print(f"✓ Created: {name} - {desc}")
    else:
        print(f"- Exists: {name}")

print(f"\nTotal medical categories: {MedicalCategory.objects.count()}")