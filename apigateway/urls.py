# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'.*', views.Gateway.as_view())
]