
from typing import Any

from django.http import HttpRequest, HttpResponse, HttpResponseForbidden

from statelessauth.config import StatelessAuthConfig
from statelessauth.prometheus import RunningOnMetric, middleware_decorator, middleware_metrics

class AuthMiddleware:
    def __init__(self, get_response, config = None):
        self.get_response = get_response

        if config is None:
            config = StatelessAuthConfig()
        self.config = config
    @middleware_decorator
    def __call__(self, request: HttpRequest, *args: Any, **kwds: Any) -> HttpResponse:
        for name, middleware_config in self.config.middlewares:
            with RunningOnMetric(
                middleware_metrics.stateless_auth_middleware_run_per_config,
                middleware_metrics.stateless_auth_middleware_run_per_config_latency,
                [ name ]
            ):
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
                    else:
                        middleware_metrics.stateless_auth_middleware_run_per_config_no_type.labels( name ).inc()

                    if token is not None:
                        result = engine.decode( token, False )

                        if result is None:
                            middleware_metrics.stateless_auth_middleware_run_per_config_wrong_token.labels( name ).inc()
                        else:
                            middleware_metrics.stateless_auth_middleware_run_per_config_valid.labels( name ).inc()

                    if result is None:
                        return HttpResponseForbidden()
                else: 
                    middleware_metrics.stateless_auth_middleware_run_per_config_missing.labels( name ).inc()

                setattr(request, field, result)

        return self.get_response(request, *args, **kwds)
