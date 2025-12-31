# Generated manually for Association ID Card functionality

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('veteran_app', '0025_alter_carouselslide_image_alter_child_child_photo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='veteranmember',
            name='association_number',
            field=models.CharField(blank=True, help_text='Unique association identity number', max_length=20, null=True, unique=True, verbose_name='Association Number'),
        ),
        migrations.AddField(
            model_name='veteranmember',
            name='renewal_due_date',
            field=models.DateField(blank=True, editable=False, help_text='ID card renewal due date (1 year from registration)', null=True),
        ),
    ]