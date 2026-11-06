import os
import redis
from redis.exceptions import RedisError
import logging
logger = logging.getLogger(__name__)
REDIS_URL = os.getenv("REDIS_URL")

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2
)


# 安全读取缓存
def cache_get(key):
    try:
        return redis_client.get(key)
    except RedisError as e:
        logger.warning("Redis缓存读取失败:%s",e)
        return None


# 安全写入缓存
def cache_set(key, value, expire=60):
    try:
        redis_client.set(key, value, ex=expire)
    except RedisError as e:
        logger.warning("Redis缓存写入失败：%s",e)


# 安全删除缓存
def cache_delete(key):
    try:
        redis_client.delete(key)
    except RedisError as e:
        logger.warning("Redis缓存删除失败:%s",e)
