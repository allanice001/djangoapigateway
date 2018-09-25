from django.contrib import admin
from .models import Api, Consumer, Authenticator

# Register your models here.
admin.site.register(Api)
admin.site.register(Consumer)
admin.site.register(Authenticator)
