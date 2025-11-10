from django.contrib import admin

# Register your models here.
from .models import Organization, Usuario

admin.site.register(Organization)
admin.site.register(Usuario)