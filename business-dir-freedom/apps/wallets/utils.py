# wallets/utils.py
from functools import wraps
from django.core.cache import cache
from django.http import HttpResponseBadRequest

def throttle(key: str, limit=5, ttl=60):
    def deco(fn):
        @wraps(fn)
        def inner(request, *a, **kw):
            user_id = getattr(request.user, "id", "anon")
            k = f"throttle:{key}:{user_id}"
            c = cache.get(k, 0)
            if c >= limit:
                return HttpResponseBadRequest("rate limited")
            cache.set(k, c+1, ttl)
            return fn(request, *a, **kw)
        return inner
    return deco
