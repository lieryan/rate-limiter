Task

The task is to produce a rate-limiting module that stops a particular requestor
from making too many requests within a particular period of time. The module
should expose a method that keeps track of requests and stops any requestor
from making more than 100 requests per hour.

Although you are only required to implement the strategy described above, it
should be easy to extend the rate limiting module to take on different
rate-limiting strategies.

Your solution should include appropriate testing.

Note that the task does not require implementing any networking calls; it is
restricted to implementing the module that keeps track of requests in order to
make rate-limiting decisions.
