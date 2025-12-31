
from typing import Callable, Generic, TypeVar

from django.http import HttpRequest, JsonResponse
from django.urls import path
from statelessauth.engine.abstract import AuthEngine
from statelessauth.prometheus import engine_view_decorator, acquire_engine_acquire_metrics
from statelessauth.wire import AuthWire

T = TypeVar("T")

class AcquireEngine(Generic[T], AuthEngine[T]):
    __acquire_view: "Callable[[HttpRequest], T | None]"

    def __init__(
            self, 
            keyname: str,
            scheme: AuthWire[T],
            acquire_view: "Callable[[HttpRequest], T | None]",
            *args, **kwargs
            ):
        super().__init__(keyname, scheme, *args, **kwargs)

        self.__acquire_view = acquire_view

    @engine_view_decorator(acquire_engine_acquire_metrics)
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

    @property
    def urlpatterns (self):
        return [
            path('acquire/', lambda *args, **kwargs: self.acquire_view(*args, **kwargs))
        ]
