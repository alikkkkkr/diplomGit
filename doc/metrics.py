from prometheus_client import Counter, Gauge, Histogram

# Примеры метрик
REQUEST_COUNT = Counter(
    'django_http_requests_total',
    'Total HTTP Requests',
    ['method', 'path', 'status']
)

RESPONSE_TIME = Histogram(
    'django_http_response_time_seconds',
    'HTTP Response Time',
    ['method', 'path']
)

ACTIVE_USERS = Gauge(
    'django_active_users',
    'Number of active users'
)