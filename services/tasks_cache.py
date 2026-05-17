import json

from redis.exceptions import RedisError

from redis_client import redis_client

CACHE_TTL_SECONDS = 60  

def user_tasks_stats_key(user_id: int) -> str:
    return f"user:{user_id}:tasks_stats"

async def get_cached_task_stats(user_id: int):
    try:
        raw = await redis_client.get(user_tasks_stats_key(user_id))
    except RedisError:
        return None

    if raw is None:
        return None
    
    return json.loads(raw)

async def set_cached_task_stats(user_id: int, stats: dict):
    try:
        await redis_client.set(
            user_tasks_stats_key(user_id),
            json.dumps(stats),
            ex=CACHE_TTL_SECONDS,
        )
    except RedisError:
        return None

async def invalidate_task_stats(user_id: int):
    try:
        await redis_client.delete(user_tasks_stats_key(user_id))
    except RedisError:
        return None
