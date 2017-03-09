# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name = 'django-api-gateway',
    version = '0.0.5',
    keywords = ('django', 'apigateway', 'dataproxy'),
    description = 'apigateway for django',
    license = 'MIT License',

    url = 'https://github.com/sarar04/djangoapigateway',
    author = 'sarar04',
    author_email = 'sarar04@163.com',

    packages = find_packages(),
    include_package_data = True,
    platforms = 'unix like',
    install_requires = []
)