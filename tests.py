import datetime
from itertools import zip_longest, islice
import unittest
from unittest.mock import patch


from redis import Redis
from backends import memory, redis
from ratelimiter import RateLimiter, SimpleRequest


SECOND = datetime.timedelta(seconds=1)
NOW = datetime.datetime(year=2018, month=1, day=1, hour=10)


def freeze_time():
    """ poor man's implementation of freezegun library """
    return patch('ratelimiter.datetime', spec=datetime.datetime)


def setup_redis():
    redis = Redis()
    redis.flushdb()
    return redis


try:
    setup_redis()
except:
    redis_available = False
else:
    redis_available = True


class BackendTestMixin(object):
    def setUp(self):
        self.maxsize = 5

    def fill_queue(self, uid, num, metadatas=[]):
        for _, metadata in zip_longest(range(num), islice(metadatas, num), fillvalue=NOW):
            head = self.backend.push(uid, metadata)
            self.assertIsNone(head)

    def test_push(self):
        head = self.backend.push('testuser', NOW)
        self.assertEqual(head, None)

    def test_push_overflow(self):
        self.fill_queue('testuser', self.maxsize, [NOW - 5*SECOND, NOW - 4*SECOND])

        head = self.backend.push('testuser', NOW)
        self.assertEqual(head, NOW - 5*SECOND)

        retrieved_head = self.backend.head('testuser')
        self.assertEqual(retrieved_head, NOW - 4*SECOND)

    def test_push_different_uid(self):
        self.fill_queue('user1', self.maxsize, [NOW - 5*SECOND])
        self.fill_queue('user2', self.maxsize, [NOW - 10*SECOND])

        head = self.backend.push('user2', NOW)
        self.assertEqual(head, NOW - 10*SECOND)

        head = self.backend.push('user1', NOW)
        self.assertEqual(head, NOW - 5*SECOND)

    def test_head(self):
        with self.subTest('not full'):
            self.fill_queue('testuser', self.maxsize - 1)

            head = self.backend.head('testuser')
            self.assertIsNone(head)

        with self.subTest('full'):
            self.fill_queue('testuser', 1)
            head = self.backend.head('testuser')
            self.assertIsNotNone(head)

    def test_head_empty(self):
        head = self.backend.head('testuser')
        self.assertIsNone(head)


class InMemoryBackendTest(BackendTestMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.backend = memory.InMemoryQueue(maxsize=self.maxsize)


@unittest.skipUnless(redis_available, "redis not available")
class RedisBackendTest(BackendTestMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.redis = setup_redis()
        self.backend = redis.RedisQueue(maxsize=self.maxsize, redis=self.redis)


class GetTimestampTest(unittest.TestCase):
    def test_use_timestamp(self):
        class CustomRequest:
            remote_user = 'user'
            timestamp = NOW - 15*SECOND

        self.limiter = RateLimiter()

        with freeze_time() as mock_datetime:
            ts = self.limiter.get_timestamp(CustomRequest())

        mock_datetime.utcnow.assert_called_once()
        self.assertEqual(ts, NOW - 15*SECOND)

    def test_optional_timestamp(self):
        class CustomRequest:
            remote_user = 'user'

        self.limiter = RateLimiter()

        with freeze_time() as mock_datetime:
            ts = self.limiter.get_timestamp(CustomRequest())

        mock_datetime.utcnow.assert_called_once()
        self.assertEqual(ts, mock_datetime.utcnow.return_value)


class RateLimiterTest(object):
    def setUp(self):
        self.maxsize = 5
        self.request = SimpleRequest('testuser', NOW)

    def fill_queue(self, num, requests=[]):
        for _, request in zip_longest(range(num), islice(requests, num), fillvalue=self.request):
            head = self.limiter.hit(request)
            self.assertIsNone(head)

    def test_hit(self):
        self.limiter.hit(self.request)

    def test_hit_limit_exceeded(self):
        self.fill_queue(self.maxsize)

        with freeze_time() as mock_datetime:
            mock_datetime.utcnow.return_value = NOW
            with self.assertRaises(RateLimiter.Exceeded):
                self.limiter.hit(self.request)

    def test_hit_oldest_has_expired(self):
        expired = SimpleRequest('testuser', NOW - self.limiter.period - 1*SECOND)
        self.fill_queue(self.maxsize, requests=[expired])

        with freeze_time() as mock_datetime:
            mock_datetime.utcnow.return_value = NOW

            self.limiter.hit(self.request)

    def test_hit_expiry_should_not_extend_when_exceeded(self):
        about_to_expire = SimpleRequest('testuser', NOW - self.limiter.period + 15*SECOND)
        self.fill_queue(self.maxsize, requests=[about_to_expire])

        with freeze_time() as mock_datetime:
            mock_datetime.utcnow.return_value = NOW
            with self.subTest("first hit fail since not expired"):
                with self.assertRaises(RateLimiter.Exceeded):
                    self.limiter.hit(self.request)

        with freeze_time() as mock_datetime:
            mock_datetime.utcnow.return_value = NOW
            with self.subTest("still not expired"):
                with self.assertRaises(RateLimiter.Exceeded):
                    self.limiter.hit(self.request)

        with freeze_time() as mock_datetime:
            mock_datetime.utcnow.return_value = NOW + 30*SECOND
            with self.subTest("now expired"):
                self.limiter.hit(self.request)


class InMemoryRateLimiterTest(RateLimiterTest, unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.limiter = RateLimiter(rate=self.maxsize)


@unittest.skipUnless(redis_available, "redis not available")
class RedisRateLimiterTest(RateLimiterTest, unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.redis = setup_redis()
        self.backend = redis.RedisQueue(self.maxsize, redis=self.redis)
        self.limiter = RateLimiter(rate=self.maxsize, backend=self.backend)
