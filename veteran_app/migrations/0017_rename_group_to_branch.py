# Generated migration to rename Group model to Branch

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('veteran_app', '0016_event_eventcategory_eventregistration_paymentgateway_and_more'),
    ]

    operations = [
        # Rename the model
        migrations.RenameModel(
            old_name='Group',
            new_name='Branch',
        ),
        # Rename the field in VeteranMember
        migrations.RenameField(
            model_name='veteranmember',
            old_name='group',
            new_name='branch',
        ),
    ]
