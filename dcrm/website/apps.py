from django.apps import AppConfig
from mongoengine import connect

class WebsiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'website'
    
    def ready(self):
        from .scheduler import start
        start()
        connect(
            db='testingDB',
            host='localhost',
            port=27017,
         )
    
    
    