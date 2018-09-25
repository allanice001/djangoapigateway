# -*- coding: utf-8 -*-
import requests, logging
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import Api


_logger = logging.getLogger('apigateway')


class gateway(APIView):
    authentication_classes = ()

    def do_operation(self, request):
        path = request.path_info.split('/')
        if len(path) < 2:
            return Response('bad request', status=status.HTTP_400_BAD_REQUEST)

        apimodel = Api.objects.filter(name=path[2])
        if len(apimodel) != 1:
            print('path', path)
            return Response('bad request', status=status.HTTP_400_BAD_REQUEST)

        apimodel = apimodel[0]
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
        response = apimodel.send_request(request, extra)
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
