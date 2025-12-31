# Association ID Card Feature Setup

## Overview
The Association ID Card feature allows approved veterans to view and download their official ICGVWA membership identity cards. The ID card includes all essential member information and can be downloaded as a PDF.

## Features Added
1. **Association Number Generation**: Automatic generation of unique association numbers in format: STATE_CODE-YYYY-NNNN
2. **ID Card Display**: Web-based ID card with front and back sides
3. **PDF Download**: Professional PDF generation with member details and terms & conditions
4. **Renewal Tracking**: Automatic calculation of renewal due dates (1 year from association date)
5. **Access Control**: Only approved veterans can access their ID cards

## Installation Steps

### 1. Install New Dependencies
```bash
pip install reportlab==4.0.7
```

### 2. Run Database Migration
```bash
python manage.py migrate
```

### 3. Update Existing Members (Optional)
Run this in Django shell to generate association numbers for existing members:
```python
python manage.py shell

from veteran_app.models import VeteranMember
for member in VeteranMember.objects.filter(association_number__isnull=True):
    member.generate_association_number()
    member.save()
    print(f"Generated association number for {member.name}: {member.association_number}")
```

## Usage

### For Veterans
1. Login to the veteran dashboard
2. Navigate to Veterans Portal → Identity Card
3. View the ID card online or download as PDF
4. Check renewal status and due dates

### For Admins
- Association numbers are automatically generated when veterans are created
- Admins can view and manage member association numbers through the admin interface
- Renewal tracking helps identify members who need to renew their cards

## Technical Details

### New Model Fields
- `association_number`: Unique identifier in format STATE_CODE-YYYY-NNNN
- `renewal_due_date`: Calculated as association_date + 1 year

### New Methods
- `generate_association_number()`: Creates unique association number
- `get_renewal_due_date()`: Calculates renewal due date
- `is_id_card_valid()`: Checks if card is still valid

### URL Patterns
- `/association-id-card/`: View ID card online
- `/download-id-card/`: Download ID card as PDF

### Templates
- `association_id_card.html`: ID card display template

## Security Features
- Only approved veterans can access ID cards
- Association numbers are unique and auto-generated
- PDF includes security features and official formatting
- Access control through Django authentication

## Customization
The ID card design, terms & conditions, and issuing authority information can be customized in the views.py file in the `association_id_card` view function.

## Troubleshooting

### Common Issues
1. **ReportLab Import Error**: Install reportlab using `pip install reportlab==4.0.7`
2. **Migration Error**: Run `python manage.py migrate` to apply database changes
3. **Access Denied**: Ensure veteran account is approved by state admin
4. **Missing Association Number**: Run the shell script above to generate numbers for existing members

### Support
For technical support or customization requests, contact the system administrator.