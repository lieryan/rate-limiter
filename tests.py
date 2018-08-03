import datetime
from itertools import zip_longest, islice
import unittest


from backends import memory


SECOND = datetime.timedelta(seconds=1)
NOW = datetime.datetime(year=2018, month=1, day=1, hour=10)


class BackendTest(unittest.TestCase):
    def setUp(self):
        self.maxsize = 5
        self.backend = memory.InMemoryQueue(maxsize=self.maxsize)

    def fill_queue(self, uid, num, metadatas=[]):
        for _, metadata in zip_longest(range(num), islice(metadatas, num), fillvalue=NOW):
            head = self.backend.push(uid, metadata)
            self.assertIsNone(head)

    def test_push(self):
        head = self.backend.push('testuser', NOW)
        self.assertEqual(head, None)

    def test_push_overflow(self):
        self.fill_queue('testuser', self.maxsize, [NOW - 5*SECOND])

        head = self.backend.push('testuser', NOW)
        self.assertEqual(head, NOW - 5*SECOND)

    def test_push_different_uid(self):
        self.fill_queue('user1', self.maxsize, [NOW - 5*SECOND])
        self.fill_queue('user2', self.maxsize, [NOW - 10*SECOND])

        head = self.backend.push('user2', NOW)
        self.assertEqual(head, NOW - 10*SECOND)

        head = self.backend.push('user1', NOW)
        self.assertEqual(head, NOW - 5*SECOND)
