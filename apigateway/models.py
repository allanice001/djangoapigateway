# -*- coding: utf-8 -*-
from datetime import datetime
from wsgiref.util import is_hop_by_hop
import json, re, os
import requests, logging
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.response import Response
from .cookies import StringMorsel
from . import settings


_logger = logging.getLogger('apigateway')


# Create your models here.
class Consumer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    apikey = models.CharField(max_length=32)

    def __unicode__(self):
        return self.user.username

    def __str__(self):
        return self.user.username


class Authenticator(models.Model):
    remote_url = models.URLField(max_length=255)
    headers = models.CharField(max_length=255,   # separated by ','
                            validators=[RegexValidator(regex='^[A-Z\-,]*$', message=_('Uppercase separated by ",".'))])

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
    AUTHED_HEADER_NAME = 'X-AUTHED'
    name = models.CharField(max_length=128, unique=True)
    request_path = models.CharField(max_length=255,
                                    validators=[RegexValidator(regex='^/', message=_('Should starts with "/".'))])
    upstream_url = models.URLField(max_length=255,
                                   validators=[RegexValidator(regex='^.+[^/]$', message=_('Should not ends with "/".'))])
    plugin = models.IntegerField(choices=PLUGIN_CHOICE_LIST, default=0)
    consumers = models.ManyToManyField(Consumer, blank=True)
    authenticators = models.ManyToManyField(Authenticator, blank=True)

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
            authenticator = self.authenticators.all()
            if not authenticator:
                return False, 'authorizer need'
            else:
                authenticator = authenticator[0]
                headers = dict()
                for key in authenticator.headers.split(','):
                    value = request.headers.get(key)
                    if value is not None:
                        headers[key] = value
                _logger.debug('Authenticating via: %s' % authenticator.remote_url)
                response = requests.post(authenticator.remote_url, headers=headers, timeout=self.TIME_OUT)
                authed = response.headers.get(self.AUTHED_HEADER_NAME)
                if authed is None:
                    return False, 'authorized header needed'
                elif authed:
                    # return {headers}
                    data = response.json()
                    data = data.get('ret') or data
                    return True, data
                else:
                    return False, self.to_rest_response(response)
        else:
            return False, Response("plugin %d not implemented" % self.plugin, status=status.HTTP_501_NOT_IMPLEMENTED)

    def send_request(self, request, prefix, params, extra={}):
        headers = request.headers.copy()

        strip_length = len(settings.SERVICE_PATH) + len(prefix)
        full_path = request.get_full_path()[strip_length:]
        if full_path and not full_path.startswith('/'):
            full_path = '/' + full_path
        url = self.upstream_url.format(**params) + full_path
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
        
        if request.content_type and request.content_type.lower() == 'application/json':
            data = json.dumps(request.data)
            headers['CONTENT-TYPE'] = request.content_type
        else:
            data = request.data
        headers.pop('ACCEPT')
        if 'headers' in extra:
            headers.update(extra['headers'])
        headers.pop('HOST', None)
        # print('url', url)
        _logger.debug('Forward request: %s' % url)
        response = method_map[method](url, headers=headers, data=data, files=request.FILES, timeout=self.TIME_OUT)
        response = self.to_rest_response(response)
        return response

    SET_COOKIE_NAME = 'Set-Cookie'
    regex = re.compile('Domain=[^;]*;?\s?')

    def to_rest_response(self, response):
        if response.headers.get('Content-Type', '').lower() == 'application/json':
            data = response.json()
        else:
            data = response.content
        headers = {key: response.headers[key] for key in response.headers if not is_hop_by_hop(key)}
        cookie_header = headers.pop(self.SET_COOKIE_NAME, None)
        raw_cookies = response.raw.headers.getlist(self.SET_COOKIE_NAME)
        response = Response(data=data, status=response.status_code, headers=headers)
        for raw_cookie in raw_cookies:
            raw_cookie = self.regex.sub('', raw_cookie)
            response.cookies[raw_cookie] = StringMorsel(raw_cookie)

        return response

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name