from veteran_app.models import MedicalCategory

categories = [
    ("S1A1", "Fit for all duties"),
    ("S1A2", "Fit for all duties with minor restrictions"),
    ("S2A2", "Fit for limited duties"),
    ("S2A3", "Fit for limited duties with restrictions"),
    ("S3A3", "Temporarily unfit"),
    ("S4A4", "Permanently unfit for service")
]

for name, desc in categories:
    obj, created = MedicalCategory.objects.get_or_create(name=name, defaults={"description": desc})
    if created:
        print(f"Created: {name}")
    else:
        print(f"Exists: {name}")

print(f"Total medical categories: {MedicalCategory.objects.count()}")