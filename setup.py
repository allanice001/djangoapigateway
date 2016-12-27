# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name = 'djangoapigateway',
    version = '0.0.1',
    keywords = ('django', 'apigateway', 'dataproxy'),
    description = 'apigateway for django',
    license = 'MIT License',

    url = '',
    author = 'sarar04',
    author = 'sarar04@163.com',

    packages = find_packages(),
    include_package_data = True,
    platforms = 'linux',
    install_requires = ['django', 'rest_framework', 'requests']
)