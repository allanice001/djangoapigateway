# Django API gateway

## Description
This is a simple apigateway for django to transmit restful api.


## Requirements
* Python(2.7)
* Django(1.8)
* requests
* djangorestframework

## Installation
Install using pip         
```
pip install django-api-gateway
```

Add 'apigateway' and 'rest_framework' to your INSTALLED_APPS setting.
```
    INSTALL_APPS = (
        ...
        'apigateway',
        'rest_framework',
    )
```

Add the following to your root urls.py file.
```
urlpatterns = [
    ...
    url(r'^service/', include('apigateway.urls', namespace='apigateway')),
]
```

Update database model
```
python manage.py migrate
python manage.py makemigrations
```

## example
visit ```http://yourhost/admin/apigateway/api/``` to add/edit/delete your restful apis


eg: 
if you add api like this:
```               
name         | construct              
request_path | /construct/                
upstream_url | http://constructhost/              
plugin       | Remote auth             
consumers    | null            
```
now when you visit ```http://yourhost/service/construct/...``` it will transfer to ```http://constructhost/...```

## Note
* api name must be unique
* plugin contain 3 types
    - Remote auth - apigateway not check auth, it will transfer the auth to the real server
    - Basic auth - you must get basic auth from apigateway
    - Key auth - you must get an apikey from apigateway

* when choose ```Key auth``` you should contain {'apikey': apikey} in headers     
```curl -i -X GET --url http://yourhost/service/... --header 'apikey: apikey'```
