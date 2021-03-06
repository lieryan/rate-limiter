"""
Helper script to test rate limiter from the terminal.

Note, this requires using the Redis backend and requires Redis server to be set
up. If you have docker and docker-compose, you can use the included
docker-compose.yml file to set up a suitable redis server.

WARNING

For safety reasons, you must explicitly specify RATELIMITER_REDIS_DB as
environment variable, this is to prevent this script from accidentally screwing
some random redis server that you may already have running for something else.
"""

import datetime
import sys

from backends.redis import RedisQueue, redis_connect
import ratelimiter


class Request(object):
    def __init__(self, uid):
        self.remote_user = uid


redis = redis_connect()
if not redis:
    print("Read the warning in the documentation before running this script.")
    sys.exit(-1)


limiter = ratelimiter.RateLimiter(backend=RedisQueue(None, redis=redis))

if len(sys.argv) < 2:
    print('Usage: RATELIMITER_REDIS_DB=1 python ./hit.py [uid]')
    print(__doc__)
    sys.exit(-1)

uid = sys.argv[1]
try:
    limiter.hit(Request(uid))
except limiter.Exceeded:
    expiry = limiter.backend.head(uid) + limiter.period
    delta = int((expiry - datetime.datetime.utcnow()).total_seconds())
    print('Enhance your calm. Try again in {} seconds ({} UTC)'.format(delta, expiry))
    sys.exit(-1)
else:
    print('Allowed')
