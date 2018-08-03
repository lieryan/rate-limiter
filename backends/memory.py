"""
In-process bounded queue, mostly useful for single-threaded system and testing.

This implementation uses collections.deque, so if you have multiple worker
processes/machines the rate limit will be per-process, this is usually not what
you want.  If you have multiple workers or distributed system, use the redis
backend instead.

Note that this implementation is not thread safe.
"""


from collections import deque


class InMemoryQueue(object):
    def __init__(self, maxsize):
        self.queues = {}
        self.maxsize = maxsize

    def push(self, uid, metadata):
        if uid not in self.queues:
            self.queues[uid] = deque(maxlen=self.maxsize)

        queue = self.queues[uid]

        head = None
        if len(queue) >= self.maxsize:
            head = queue.popleft()

        queue.append(metadata)

        return head
