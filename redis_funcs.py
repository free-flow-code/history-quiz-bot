import redis as r


def init_redis(redis_uri):
    redis = r.StrictRedis(
        host=redis_uri.hostname,
        port=int(redis_uri.port),
        password=redis_uri.password,
        charset='utf-8',
        decode_responses=True
    )
    redis.ping()
    return redis
