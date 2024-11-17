
from typing import Any

from django.http import HttpRequest, HttpResponse, HttpResponseForbidden

from rest_framework_statelessauth.config import StatelessAuthConfig

class AuthMiddleware:
    def __init__(self, get_response, config = None):
        self.get_response = get_response

        if config is None:
            config = StatelessAuthConfig()
        self.config = config
    def __call__(self, request: HttpRequest, *args: Any, **kwds: Any) -> HttpResponse:
        for name, middleware_config in self.config.middlewares:
            engine = middleware_config.get_engine()
            field  = middleware_config.field
            
            header, type = middleware_config.header

            header_value = request.headers.get( header, None )

            result = None
            
            if header_value is not None:
                token = None

                if type == "" or type == None:
                    token = header_value
                elif header_value.startswith(type + " "):
                    token = header_value[len(type) + 1:]

                if token is not None:
                    result = engine.decode( token, False )

                if result is None:
                    return HttpResponseForbidden()

            setattr(request, field, result)

        return self.get_response(request, *args, **kwds)
