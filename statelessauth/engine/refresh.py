
import math
from typing import Callable, Generic, TypeVar

from django.http import HttpRequest, JsonResponse
from django.urls import path
from statelessauth.engine.abstract import AuthEngine
from statelessauth.prometheus import engine_view_decorator, refresh_engine_acquire_metrics, refresh_engine_refresh_metrics
from statelessauth.wire import AuthWire

import time

T = TypeVar("T")

class RefreshEngine(Generic[T], AuthEngine[T]):
    __acquire_view: "Callable[[HttpRequest], T | None]"

    __short_timeout: int
    __long_timeout : int

    __scheme : AuthWire[T]

    def __init__(
            self, 
            keyname: str,
            scheme: AuthWire[T],
            acquire_view: "Callable[[HttpRequest], T | None]",
            short_timeout = 5 * 60, # 5 minutes short timeout
            long_timeout  = 14 * 24 * 60 * 60, # 14 days long timeout
            *args, **kwargs
            ):
        super().__init__(keyname, scheme, *args, **kwargs)

        self.__acquire_view = acquire_view

        self.__scheme = scheme

        self.__short_timeout = short_timeout
        self.__long_timeout  = long_timeout

    def payload_from_wired(self, wired):
        start = time.time_ns()

        return {
            "wired": wired,
            "alt": start + math.floor(1_000_000_000 * self.__short_timeout),
            "rlt": start + math.floor(1_000_000_000 * self.__long_timeout)
        }
    def wired_from_payload(self, payload):
        return payload["wired"]
    def validate_payload(self, payload):
        return time.time_ns() <= payload['alt']

    @engine_view_decorator(refresh_engine_acquire_metrics)
    def acquire_view (self, request: HttpRequest, *args, **kwargs):
        result = self.__acquire_view(request, *args, **kwargs)

        if result is None:
            return JsonResponse({
                "valid": False,
                "token": ""
            }, status=401)
        
        return JsonResponse({
            "valid": True,
            "token": self.encode(result)
        }, status=200)
    def refresh_view (self, request: HttpRequest, *args, **kwargs):
        metrics = refresh_engine_refresh_metrics
        metrics._init()

        start = time.time()
        
        refresh_header = request.headers.get("Refresh")
        if refresh_header is None:
            metrics.total_counter  .run( self.name, time.time() - start )
            metrics.missing_counter.run( self.name, time.time() - start )
            return JsonResponse({
                "valid": False,
                "token": ""
            }, status=400)

        payload = self.decode(refresh_header, verify=False, return_payload=True)
        if payload is None:
            metrics.total_counter.run( self.name, time.time() - start )
            metrics.wrong_counter.run( self.name, time.time() - start )
            return JsonResponse({
                "valid": False,
                "token": ""
            }, status=401)
        if time.time_ns() > payload['rlt']:
            metrics.total_counter.run( self.name, time.time() - start )
            metrics.expired_counter.run( self.name, time.time() - start )
            return JsonResponse({
                "valid": False,
                "token": ""
            }, status=401)

        new_payload = self.__scheme.decode( self.wired_from_payload( payload ) )

        metrics.total_counter.run( self.name, time.time() - start )
        metrics.success_counter.run( self.name, time.time() - start )
        return JsonResponse({
            "valid": True,
            "token": self.encode(new_payload)
        }, status=200)
    
    @property
    def urlpatterns (self):
        return [
            path('acquire/', lambda *args, **kwargs: self.acquire_view(*args, **kwargs)),
            path('refresh/', lambda *args, **kwargs: self.refresh_view(*args, **kwargs))
        ]
