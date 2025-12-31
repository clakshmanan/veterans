# Generated manually for updated Association ID Card number format

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('veteran_app', '0026_add_association_id_card_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='veteranmember',
            name='association_number',
            field=models.CharField(blank=True, help_text='Unique association identity number', max_length=30, null=True, unique=True, verbose_name='Association Number'),
        ),
    ]