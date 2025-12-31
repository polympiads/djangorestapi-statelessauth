
import time
import json
from typing import TYPE_CHECKING, Any, Callable, List, Type, TypeVar
from django.conf import settings
from django.http import JsonResponse
from prometheus_client      import REGISTRY, Counter, Histogram
from prometheus_client.metrics import MetricWrapperBase

stateless_auth_metrics_generated = False

class EngineMetric:
    __metric_fnc : "Callable[[Any]]"

    def __init__(self, metric_cls: Type[MetricWrapperBase], metric_fnc, name: str, help: str, labels: List[str] = [], *args, **kwargs):
        from django_prometheus.conf import NAMESPACE
        self.name = name
        self.help = help

        self.__metric_fnc = metric_fnc

        self.metric_total = metric_cls(
            name,
            help,
            *args, 
            namespace = NAMESPACE,
            **({ "labelnames" : labels, **kwargs } if len(labels) != 0 else kwargs)
        )
        self.metric_per_engine = metric_cls(
            name + "_per_engine",
            help + " per authentication engine",
            [ 'engine' ] + labels,
            *args, 
            namespace = NAMESPACE,
            **kwargs
        )
    def run_on (self, engine: str, ob_args: List = [],  lbl_args: List = []):
        self.__metric_fnc(
            self.metric_total.labels(*lbl_args) if len(lbl_args) != 0 else self.metric_total,
            *ob_args
        )
        self.__metric_fnc(
            self.metric_per_engine.labels(engine, *lbl_args),
            *ob_args
        )
class TotalAndLatencyMetric:
    def __init__(self, name: str, help1: str, help2: str):
        from django_prometheus.conf import PROMETHEUS_LATENCY_BUCKETS, NAMESPACE
        self.total = EngineMetric(
            Counter,
            Counter.inc,
            name + "_total",
            help1
        )
        self.latency = EngineMetric(
            Histogram,
            Histogram.observe,
            name + "_latency",
            help2,
            buckets=PROMETHEUS_LATENCY_BUCKETS
        )
    def run (self, name: str, latency: float):
        self.total.run_on(name)
        self.latency.run_on(name, [ latency ])

class MiddlewareMetrics:
    _was_init = False
    def _init (self):
        if self._was_init: return
        self._was_init = True
        from django_prometheus.conf import PROMETHEUS_LATENCY_BUCKETS, NAMESPACE

        self.stateless_auth_middleware_run = Counter(
            "stateless_auth_middleware_run",
            "Number of runs of the middleware",
            namespace=NAMESPACE
        )
        self.stateless_auth_middleware_run_latency = Histogram(
            "stateless_auth_middleware_run_latency",
            "Latency of the stateless auth middleware",
            buckets=PROMETHEUS_LATENCY_BUCKETS,
            namespace=NAMESPACE
        )

        self.stateless_auth_middleware_run_per_config = Counter(
            "stateless_auth_middleware_run_per_config",
            "Number of runs per sub middleware configured",
            [ "middleware" ],
            namespace=NAMESPACE
        )
        self.stateless_auth_middleware_run_per_config_latency = Histogram(
            "stateless_auth_middleware_run_latency_per_config",
            "Latency of the stateless auth middleware",
            [ "middleware" ],
            buckets=PROMETHEUS_LATENCY_BUCKETS,
            namespace=NAMESPACE
        )
        self.stateless_auth_middleware_run_per_config_missing = Counter(
            "stateless_auth_middleware_run_per_config_missing",
            "Number of runs per sub middleware configured where header is missing",
            [ "middleware" ],
            namespace=NAMESPACE
        )
        self.stateless_auth_middleware_run_per_config_wrong_token = Counter(
            "stateless_auth_middleware_run_per_config_wrong_token",
            "Number of runs per sub middleware configured where the token is invalid",
            [ "middleware" ],
            namespace=NAMESPACE
        )
        self.stateless_auth_middleware_run_per_config_no_type = Counter(
            "stateless_auth_middleware_run_per_config_no_type",
            "Number of runs per sub middleware configured where header has no type",
            [ "middleware" ],
            namespace=NAMESPACE
        )
        self.stateless_auth_middleware_run_per_config_valid = Counter(
            "stateless_auth_middleware_run_per_config_valid",
            "Number of runs per sub middleware configured where header is valid",
            [ "middleware" ],
            namespace=NAMESPACE
        )
    def clear (self):
        self._was_init = False
        self._init()

middleware_metrics = MiddlewareMetrics()

class TokenBasedViewMetrics:
    _was_init = False
    def __init__(self, name: str, qname: str):
        self.name = name
        self.qname = qname
    def _init(self):
        if self._was_init: return
        self._was_init = True
        from django_prometheus.conf import PROMETHEUS_LATENCY_BUCKETS, NAMESPACE
        self.total_counter = TotalAndLatencyMetric(
            self.qname,
            f"Total number of calls to {self.name}",
            f"Latency of calls to {self.name}"
        )
        self.success_counter = TotalAndLatencyMetric(
            self.qname + "_success",
            f"Total number of successful calls to {self.name}",
            f"Latency of successful calls to {self.name}"
        )
        self.failed_counter = TotalAndLatencyMetric(
            self.qname + "_failed",
            f"Total number of failed calls to {self.name}",
            f"Latency of failed calls to {self.name}"
        )
    def observe (self, engine: str, latency: float, valid: bool):
        self.total_counter.run( engine, latency )
        
        if valid:
            self.success_counter.run( engine, latency )
        else:
            self.failed_counter.run( engine, latency )

    def clear (self):
        self._was_init = False
        self._init()

acquire_engine_acquire_metrics = TokenBasedViewMetrics(
    "AcquireEngine.acquire_view",
    "stateless_auth_acquire_engine_acquire_view"
)
refresh_engine_acquire_metrics = TokenBasedViewMetrics(
    "RefreshEngine.acquire_view",
    "stateless_auth_refresh_engine_acquire_view"
)

class RefreshViewMetrics:
    _was_init = False
    def __init__(self, name: str, qname: str):
        self.name = name
        self.qname = qname
    def _init(self):
        if self._was_init: return
        self._was_init = True
        from django_prometheus.conf import PROMETHEUS_LATENCY_BUCKETS, NAMESPACE
        self.total_counter = TotalAndLatencyMetric(
            self.qname,
            f"Total number of calls to {self.name}",
            f"Latency of calls to {self.name}"
        )
        self.success_counter = TotalAndLatencyMetric(
            self.qname + "_success",
            f"Total number of successful calls to {self.name}",
            f"Latency of successful calls to {self.name}"
        )
        self.wrong_counter = TotalAndLatencyMetric(
            self.qname + "_wrong",
            f"Total number of calls with wrong tokens to {self.name}",
            f"Latency of calls with wrong tokens to {self.name}"
        )
        self.expired_counter = TotalAndLatencyMetric(
            self.qname + "_expired",
            f"Total number of calls with expired tokens to {self.name}",
            f"Latency of calls with expired tokens to {self.name}"
        )
        self.missing_counter = TotalAndLatencyMetric(
            self.qname + "_missing",
            f"Total number of calls where refresh token is missing to {self.name}",
            f"Latency of calls where refresh token is missing to {self.name}"
        )
    def clear (self):
        self._was_init = False
        self._init()

refresh_engine_refresh_metrics = RefreshViewMetrics(
    "RefreshEngine.refresh_view",
    "stateless_auth_refresh_engine_refresh_view"
)

class RunningOnMetric:
    start: int
    m1   : Counter
    m2   : Histogram
    def __init__(self, m1: Counter, m2: Histogram, labels: List[str] = []) -> None:
        if len(labels) != 0:
            m1 = m1.labels( *labels )
            m2 = m2.labels( *labels )
        self.m1 = m1
        self.m2 = m2

    def __enter__(self):
        self.m1.inc()
        self.start = time.time()
        return self
    def __exit__(self, *args):
        self.m2.observe( time.time() - self.start )

def generate_metrics ():
    global stateless_auth_encode

    global stateless_auth_decode
    global stateless_auth_decode_failed
    global stateless_auth_decode_success

    global stateless_auth_metrics_generated
    if stateless_auth_metrics_generated: return
    stateless_auth_metrics_generated = True

    stateless_auth_encode = TotalAndLatencyMetric(
        "stateless_auth_encode",
        "Total number of authentication encodes",
        "Latency during encoding of authentication data"
    )
    stateless_auth_decode = TotalAndLatencyMetric(
        "stateless_auth_decode",
        "Total number of authentication decodes",
        "Latency during encoding of authentication data"
    )
    stateless_auth_decode_success = TotalAndLatencyMetric(
        "stateless_auth_decode_success",
        "Total number of successful authentication decodes",
        "Latency during encoding of valid authentication data"
    )
    stateless_auth_decode_failed  = TotalAndLatencyMetric(
        "stateless_auth_decode_failed",
        "Total number of failed authentication decodes",
        "Latency during decoding of wrong authentication data"
    )

def uses_metrics (f):
    def wrapped (*args, **kwargs):
        generate_metrics()
        return f(*args, **kwargs)
    wrapped.__name__ = f.__name__
    return wrapped

def stateless_auth_encode_decorator (f):
    @uses_metrics
    def wrapped (self, *args, **kwargs):
        start = time.time()
        result = f(self, *args, **kwargs)
        end = time.time()

        delta = end - start
        
        stateless_auth_encode.run( self.name, delta )

        return result
    wrapped.__name__ = f.__name__
    return wrapped
def stateless_auth_decode_decorator (f):
    @uses_metrics
    def wrapped (self, *args, **kwargs):
        start = time.time()

        result = None
        exception = None
        try:
            result = f(self, *args, **kwargs)
        except Exception as exc:
            exception = exc
        end = time.time()

        delta = end - start
        
        stateless_auth_decode.run( self.name, delta )

        if exception is not None or result is None:
            if exception is not None: raise exception

            stateless_auth_decode_failed.run(self.name, delta)
        else:
            stateless_auth_decode_success.run(self.name, delta)

        return result
    wrapped.__name__ = f.__name__
    return wrapped
def middleware_decorator (f):
    def wrapped (self, *args, **kwargs):
        middleware_metrics._init()
        with RunningOnMetric(
            middleware_metrics.stateless_auth_middleware_run,
            middleware_metrics.stateless_auth_middleware_run_latency
        ):
            return f(self, *args, **kwargs)
    wrapped.__name__ = f.__name__
    return wrapped

def engine_view_decorator (engine_metrics: TokenBasedViewMetrics):
    def decorator (f):
        def wrapped (self, *args, **kwargs):
            start = time.time()
            result: JsonResponse = f(self, *args, **kwargs)
            end = time.time()

            engine_metrics._init()
            content = result.content
            data = json.loads( content.decode() )
            engine_metrics.observe( self.name, end - start, data["valid"] )
            return result
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator

def clear_metrics ():
    collectors = list( REGISTRY._collector_to_names.keys() )
    for collector in collectors:
        REGISTRY.unregister(collector)
    global stateless_auth_metrics_generated
    stateless_auth_metrics_generated = False

    generate_metrics()
    
    middleware_metrics.clear()
    acquire_engine_acquire_metrics.clear()
    refresh_engine_acquire_metrics.clear()
    refresh_engine_refresh_metrics.clear()
