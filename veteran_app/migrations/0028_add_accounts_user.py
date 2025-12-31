# Generated migration for AccountsUser model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import veteran_app.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('veteran_app', '0027_update_association_number_format'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountsUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('approved', models.BooleanField(default=False, help_text='Approved by superadmin to access accounts')),
                ('full_name', models.CharField(blank=True, help_text='Full name of accounts user', max_length=200)),
                ('designation', models.CharField(default='Accounts Manager', help_text='e.g., Treasurer, Accounts Manager', max_length=100)),
                ('contact_number', models.CharField(blank=True, help_text='Contact number', max_length=15, validators=[veteran_app.validators.validate_phone_number])),
                ('email', models.EmailField(blank=True, help_text='Official email', max_length=254)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='accounts_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Accounts User',
                'verbose_name_plural': 'Accounts Users',
            },
        ),
    ]