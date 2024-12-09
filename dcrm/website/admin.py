from django.contrib import admin
from .models import Company, User, Emailserver
# Register your models here.
admin.site.register(Company)
admin.site.register(User)
admin.site.register(Emailserver)