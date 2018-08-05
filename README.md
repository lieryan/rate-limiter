-------------
Prerequisites
-------------

1. Python>=3.6


-----
Setup
-----

1. Checkout code:

    $ git clone XXX ## TODO: insert Github clone link
    $ cd airtasker

-----
Redis
-----

This rate limiter module optionally supports a Redis backend, to use:

1. Create and activate virtualenv

    $ python3.6 -m venv env
    $ source env/bin/activate
    (env) $ 

2. Install requirements

    (env) $ pip install -r requirements.txt

3. Install Redis using your system's Redis install steps or use the supplied
   docker-compose.yml:

    (env) $ docker-compose up -d


-------------
Running tests
-------------

Run tests:

    (env) $ python -m unittest


-----------------------
Running test with Redis
-----------------------

For safety reasons, you must explicitly specify RATELIMITER_REDIS_DB as
environment variable, this is to prevent the test from accidentally screwing
some random redis server that you may already have running for something else.

    (env) $ RATELIMITER_REDIS_DB=0 python -m unittest

=======
WARNING
=======

Running unittest with Redis will destroy all data in that Redis database. Make
sure you don't have anything valuable there.
