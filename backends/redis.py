"""
Redis-backed queue.
"""


from datetime import datetime


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
