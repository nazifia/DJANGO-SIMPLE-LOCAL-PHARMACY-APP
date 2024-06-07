from django.apps import AppConfig


class PharmappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pharmapp'



class pharmappConfig(AppConfig):
    name = 'pharmapp'

    def ready(self):
        import pharmapp.signals