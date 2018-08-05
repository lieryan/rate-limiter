"""
Redis-backed queue.

Caveats and missing features

The current implementation is not safe for concurrent access. The rate limiter
code will need to run this in a MULTI transaction and add some WATCH to
correctly handle concurrent hits, essentially acquiring an exclusive write lock
for the uid.

An alternative implementation which may be more efficient in a distributed
system is to relax the rate limiting mechanism and allow approximate rate limit
where a few extra requests may be accepted but allows the application to handle
rate limiting without consulting a central Redis server all the time. Instead
the application should periodically retrieve a blocked uid list that are cached
and consulted locally and submit the hit request asynchronously or in a
separate thread so it does not block main request processing.

For production readiness, the backend should EXPIRE the keys so that Redis will
delete old keys that are no longer relevant. Currently, Redis will keep all
data forever so the Redis disk space will grow indefinitely.
"""


import os
from datetime import datetime

import redis


datefmt = "%Y-%m-%d %H:%M:%S"


class RedisQueue(object):
    def __init__(self, maxsize, redis):
        self.maxsize = maxsize
        self.redis = redis

    def push(self, uid, metadata):
        head = self.head(uid)
        self.redis.lpush(uid, metadata.strftime(datefmt))
        self.redis.ltrim(uid, 0, self.maxsize - 1)
        return head

    def head(self, uid):
        if self.redis.llen(uid) >= self.maxsize:
            return datetime.strptime(self.redis.lindex(uid, -1).decode(), datefmt)


def redis_connect():
    port = os.environ.get('RATELIMITER_REDIS_PORT', 6379)

    try:
        db = os.environ['RATELIMITER_REDIS_DB']
    except KeyError:
        print("RATELIMITER_REDIS_DB is not set.")
    else:
        return redis.Redis(port=port, db=db)
