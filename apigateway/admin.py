from django.contrib import admin
from .models import Api, Consumer, Authorizer

# Register your models here.
admin.site.register(Api)
admin.site.register(Consumer)
admin.site.register(Authorizer)
