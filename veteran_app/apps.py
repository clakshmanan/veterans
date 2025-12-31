from django.apps import AppConfig


class VeteranAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'veteran_app'
    
    def ready(self):
        import veteran_app.signals
