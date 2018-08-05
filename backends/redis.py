"""
Redis-backed queue.
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
