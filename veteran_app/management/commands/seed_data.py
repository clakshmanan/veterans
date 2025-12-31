from django.core.management.base import BaseCommand
from veteran_app.models import State, Rank, Branch, BloodGroup, Message, MedicalCategory


class Command(BaseCommand):
    help = "Seed initial master data: States, Ranks, Branches, BloodGroups, and a sample Message."

    def handle(self, *args, **options):
        created_counts = {
            'states': 0,
            'ranks': 0,
            'branches': 0,
            'blood_groups': 0,
            'medical_categories': 0,
            'messages': 0,
        }

        # States (complete set including all 27 states)
        states = [
            ("Andaman & Nicobar", "A&N"),
            ("Andhra Pradesh", "AP"),
            ("Assam", "AS"),
            ("Bihar", "BR"),
            ("Delhi", "DL"),
            ("Diu & Daman", "DMN"),
            ("Goa", "GOA"),
            ("Gujarat", "GJ"),
            ("Himachal Pradesh", "HP"),
            ("Karnataka", "KA"),
            ("Kerala", "KL"),
            ("Madhya Pradesh", "MP"),
            ("Maharashtra", "MH"),
            ("Manipur", "MPR"),
            ("Mizoram", "MIZ"),
            ("Nagaland", "NGL"),
            ("Odisha", "ODI"),
            ("Pondicherry", "PY"),
            ("Punjab", "PB"),
            ("Rajasthan", "RJ"),
            ("Sikkim", "SKM"),
            ("Tamil Nadu", "TN"),
            ("Telangana", "TS"),
            ("Tripura", "TPA"),
            ("Uttar Pradesh", "UP"),
            ("Uttarakhand", "UKD"),
            ("West Bengal", "WB"),
        ]
        for name, code in states:
            obj, created = State.objects.get_or_create(name=name, defaults={'code': code})
            # If state with same name exists but code differs, update code for consistency
            if not created and obj.code != code:
                obj.code = code
                obj.save(update_fields=["code"])
            created_counts['states'] += 1 if created else 0

        # Ranks (sample)
        ranks = [
           "Family Pensioner", "Honorable Meber",  "Pradhan Adhikari", "Pradhan Sahayak Engineer", "Uttham Adhikari",  "Uttham Sahayak Engineer", "Adhikari",
            "Sahayak Engineer", "Pradhan Navik", "Pradhan Yantrik", "Uttham Navik", "Uttham Yantrik", "Navik", "yantrik", 
        ]
        for r in ranks:
            _, created = Rank.objects.get_or_create(name=r)
            created_counts['ranks'] += 1 if created else 0

        # Branches (sample)
        branches = [
            "QA", "RP", "RO", "SA", "RO", "AL", "SE", "ACD", 'AH', "Radio",
            "AP", "AE", "AR", "ERA", "Power","MET","STD", "ME", 'CK'
        ]
        for g in branches:
            _, created = Branch.objects.get_or_create(name=g)
            created_counts['branches'] += 1 if created else 0

        # Blood groups (standard set)
        blood_groups = [
            "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-",
        ]
        for b in blood_groups:
            _, created = BloodGroup.objects.get_or_create(name=b)
            created_counts['blood_groups'] += 1 if created else 0

        # Medical categories (standard military medical categories)
        medical_categories = [
            ("S1A1", "Fit for all duties"),
            ("S1A2", "Fit for all duties with minor restrictions"),
            ("S2A2", "Fit for limited duties"),
            ("S2A3", "Fit for limited duties with restrictions"),
            ("S3A3", "Temporarily unfit"),
            ("S4A4", "Permanently unfit for service"),
        ]
        for name, desc in medical_categories:
            _, created = MedicalCategory.objects.get_or_create(name=name, defaults={'description': desc})
            created_counts['medical_categories'] += 1 if created else 0

        # Sample active message (only create if none exists)
        if not Message.objects.exists():
            Message.objects.create(
                title="Welcome to the Veteran Association Portal",
                content=(
                    "Use the Services page to choose a state and manage veteran members. "
                    "Admins can approve pending members and download CSV reports."
                ),
                is_active=True,
            )
            created_counts['messages'] += 1

        self.stdout.write(self.style.SUCCESS("Seeding completed."))
        self.stdout.write(
            "Created (if not existed): States=%d, Ranks=%d, Branches=%d, BloodGroups=%d, MedicalCategories=%d, Messages=%d"
            % (
                created_counts['states'],
                created_counts['ranks'],
                created_counts['branches'],
                created_counts['blood_groups'],
                created_counts['medical_categories'],
                created_counts['messages'],
            )
        )
