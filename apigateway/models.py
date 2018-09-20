# -*- coding: utf-8 -*-
import requests, json
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from rest_framework.authentication import get_authorization_header, BasicAuthentication
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework.response import Response
from rest_framework import status

# Create your models here.
class Consumer(models.Model):
    user = models.OneToOneField(User)
    apikey = models.CharField(max_length=32)

    def __unicode__(self):
        return self.user.username

    def __str__(self):
        return self.user.username


class Authorizer(models.Model):
    remote_url = models.URLField(max_length=255)
    headers = models.CharField(max_length=255)  # separated by ','

    def __unicode__(self):
        return self.remote_url

    def __str__(self):
        return self.remote_url


class Api(models.Model):
    PLUGIN_CHOICE_LIST = (
        (0, _('Remote auth')),
        (1, _('Basic auth')),
        (2, _('Key auth')),
        (3, _('Server auth')),
        (4, _('Middle auth')),
    )
    TIME_OUT = 30
    name = models.CharField(max_length=128, unique=True)
    request_path = models.CharField(max_length=255)
    upstream_url = models.URLField(max_length=255)
    plugin = models.IntegerField(choices=PLUGIN_CHOICE_LIST, default=0)
    consumers = models.ManyToManyField(Consumer, blank=True)
    authorizers = models.ManyToManyField(Authorizer, blank=True)

    def check_plugin(self, request):
        if self.plugin == 0:
            return True, ''
            
        elif self.plugin == 1:
            auth = BasicAuthentication()
            try:
                user, password = auth.authenticate(request)
            except:
                return False, 'Authentication credentials were not provided'

            if self.consumers.filter(user=user):
                return True, ''
            else:
                return False, Response('permission not allowed', status.HTTP_403_FORBIDDEN)
        elif self.plugin == 2:
            apikey = request.META.get('HTTP_APIKEY')
            consumers = self.consumers.all()
            for consumer in consumers:
                if apikey == consumer.apikey:
                    return True, ''
            return False, 'apikey need'
        elif self.plugin == 3:
            consumer = self.consumers.all()
            if not consumer:
                return False, 'consumer need'
            request.META['HTTP_AUTHORIZATION'] = requests.auth._basic_auth_str(consumer[0].user.username, consumer[0].apikey)
            return True, ''
        elif self.plugin == 4:
            authorizer = self.authorizers.all()
            if not authorizer:
                return False, 'authorizer need'
            else:
                authorizer = authorizer[0]
                headers = dict()
                for key in authorizer.headers.split(','):
                    value = request.headers.get(key)
                    if value is None:
                        return False, 'header %s needed' % key
                    else:
                        headers[key] = value
                return True, request.post(authorizer.remote_url, headers=headers, timeout=self.TIME_OUT)
        else:
            return False, Response("plugin %d not implemented" % self.plugin, status=status.HTTP_501_NOT_IMPLEMENTED)

    def send_request(self, request):
        headers = {}
        if self.plugin != 1 and request.META.get('HTTP_AUTHORIZATION'):
            headers['authorization'] = request.META.get('HTTP_AUTHORIZATION')
        # headers['content-type'] = request.content_type

        strip = '/service' + self.request_path
        full_path = request.get_full_path()[len(strip):]
        url = self.upstream_url + full_path
        method = request.method.lower()
        method_map = {
            'get': requests.get,
            'post': requests.post,
            'put': requests.put,
            'patch': requests.patch,
            'delete': requests.delete
        }

        for k,v in request.FILES.items():
            request.data.pop(k)
        
        if request.content_type and request.content_type.lower()=='application/json':
            data = json.dumps(request.data)
            headers['content-type'] = request.content_type
        else:
            data = request.data

        return method_map[method](url, headers=headers, data=data, files=request.FILES, timeout=self.TIME_OUT)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name