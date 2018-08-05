"""
Example usage:

    >>> class CustomRequest(object):
    ...    def __init__(self, user):
    ...        self.remote_user = user
    ...
    ...    @property
    ...    def timestamp(self):
    ...        return datetime.datetime.utcnow()
    ...
    >>> limiter = RateLimiter()
    >>> def handle_request():
    ...     try:
    ...         limiter.hit(CustomRequest('user'))
    ...     except limiter.Exceeded:
    ...         print("Request not permitted. Rate limit exceeded.")
    ...     else:
    ...         print("Request permitted.")
    ...
    >>> handle_request()
    Request permitted.
    >>> for _ in range(110): handle_request() # doctest: +ELLIPSIS
    Request permitted.
    ...
    Request not permitted. Rate limit exceeded.

"""

from collections import namedtuple
from datetime import datetime, timedelta


from backends import memory


class AbstractRequest(object):
    # required. Note that remote_user attribute corresponds to the REMOTE_USER
    # header field accessor that is used in the Request classes of many WSGI
    # frameworks, like Werkzeug and WebOb, so you can just pass those request
    # objects when using web frameworks that uses the request classes of those
    # libraries and you are using remote_user to identify users
    remote_user: str = None

    # optional. If not set, RateLimiter will use current time.
    timestamp: datetime = None


SimpleRequest = namedtuple('SimpleRequest', ['remote_user', 'timestamp'])


class RateLimiter(object):
    class Exceeded(Exception):
        """ this exception is raised when rate limit is exceeded """
        pass

    def __init__(self, rate=100, period=timedelta(hours=1), backend=None):
        self.rate = rate
        self.period = period

        if backend is None:
            backend = memory.InMemoryQueue(maxsize=rate)
        self.backend = backend

    def hit(self, request):
        user = self.get_user(request)
        timestamp = self.get_timestamp(request)

        oldest_request_timestamp = self.backend.head(user)

        if oldest_request_timestamp is not None and not self.is_expired(oldest_request_timestamp):
            raise RateLimiter.Exceeded()
        else:
            self.backend.push(user, timestamp)

    def get_user(self, request):
        return request.remote_user

    def get_timestamp(self, request):
        return getattr(request, 'timestamp', datetime.utcnow())

    def is_expired(self, timestamp):
        return timestamp < datetime.utcnow() - self.period
