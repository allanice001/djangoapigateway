# -*- coding: utf-8 -*-
import requests, logging, re
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import Api
from . import settings


_logger = logging.getLogger('apigateway')


class Gateway(APIView):
    authentication_classes = ()

    param_regex = re.compile(r'\{(.+?)\}')

    @classmethod
    def extract_params(cls, path, prefix):
        """
        :param path:
        :param prefix:
        :return: None if not match, otherwise {params, prefix}
        """
        pattern = cls.param_regex.sub('(.+?)', prefix)
        values_match = re.match(pattern, path)
        if values_match is None:
            return values_match
        params = dict()
        names = cls.param_regex.findall(prefix)
        for index, name in enumerate(names):
            params[name] = values_match.groups()[index]
        span = values_match.span()
        return dict(params=params, prefix=path[span[0]:span[1]])

    def do_operation(self, request):
        path = request.path_info.split('/')
        if len(path) < 3:
            return Response('bad path length', status=status.HTTP_400_BAD_REQUEST)

        apimodel = Api.objects.filter(name=path[2])
        if len(apimodel) != 1:
            return Response('bad service', status=status.HTTP_400_BAD_REQUEST)

        apimodel = apimodel[0]
        extract = self.extract_params(request.path_info[len(settings.SERVICE_PATH):], apimodel.request_path)
        if not extract:
            return Response('bad path pattern', status=status.HTTP_400_BAD_REQUEST)

        request.headers = {key[5:].replace('_', '-'): value for key, value in request.META.items() if key.startswith('HTTP_')}
        valid, message = apimodel.check_plugin(request)
        if not valid:
            if not isinstance(message, Response):
                response = Response(message, status=status.HTTP_400_BAD_REQUEST)
            else:
                response = message
            return response
        extra = {}
        if isinstance(message, dict):
            extra = message
        response = apimodel.send_request(request, extract['prefix'], extract['params'], extra)
        return response

    def operation(self, request):
        try:
            return self.do_operation(request)
        except Exception as e:
            logging.exception(e)
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        return self.operation(request)

    def post(self, request):
        return self.operation(request)

    def put(self, request):
        return self.operation(request)
    
    def patch(self, request):
        return self.operation(request)
    
    def delete(self, request):
        return self.operation(request)
