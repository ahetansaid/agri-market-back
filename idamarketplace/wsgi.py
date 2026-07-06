"""
WSGI config for idamarketplace project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "idamarketplace.settings.production")

application = get_wsgi_application()

# def process_http_request(environ, start_response):
#     status = '200 OK'
#     response_headers = [
#         ('Content-type', 'text/plain; charset=utf-8'),
#     ]
#     start_response(status, response_headers)
#     text = 'Hello World'.encode('utf-8')
#     return [text]
