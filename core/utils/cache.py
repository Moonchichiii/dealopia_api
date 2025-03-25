from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json


def generate_cache_key(prefix, *args, **kwargs):
    """Generate a unique cache key based on function arguments"""
    key_parts = [prefix]
    
    if args:
        for arg in args:
            if hasattr(arg, 'id'):
                key_parts.append(f"id:{arg.id}")
            elif isinstance(arg, (list, tuple, set)):
                key_parts.append(f"list:{len(arg)}")
            else:
                key_parts.append(str(arg))
    
    if kwargs:
        for key, value in sorted(kwargs.items()):
            if hasattr(value, 'id'):
                key_parts.append(f"{key}:id:{value.id}")
            elif isinstance(value, (dict, list, tuple, set)):
                hash_input = json.dumps(value, sort_keys=True)
                hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
                key_parts.append(f"{key}:hash:{hash_value}")
            else:
                key_parts.append(f"{key}:{value}")
    
    key = ":".join(key_parts)
    if len(key) > 200:
        hashed_part = hashlib.md5(":".join(key_parts[1:]).encode()).hexdigest()
        key = f"{prefix}:hash:{hashed_part}"
    
    return key


def cache_result(timeout=300, prefix=None, condition=None):
    """Cache decorator for functions and methods"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if settings.DEBUG and not getattr(settings, 'CACHE_IN_DEBUG', False):
                return func(*args, **kwargs)
            
            if condition and not condition(*args, **kwargs):
                return func(*args, **kwargs)
            
            func_prefix = prefix or f"{func.__module__}.{func.__name__}"
            cache_key = generate_cache_key(func_prefix, *args, **kwargs)
            
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def invalidate_cache_prefix(prefix):
    """Invalidate all cache keys with a specific prefix"""
    if hasattr(cache, 'delete_pattern'):
        cache.delete_pattern(f"{prefix}:*")
    else:
        if hasattr(cache, 'keys'):
            keys = cache.keys(f"{prefix}:*")
            if keys:
                cache.delete_many(keys)


class CacheGroup:
    """Helper class for managing related cache keys that should be invalidated together"""
    def __init__(self, group_name):
        self.group_name = group_name
        self._keys = set()
        self._load_keys()
    
    def _load_keys(self):
        group_key = f"cache_group:{self.group_name}"
        keys = cache.get(group_key)
        if keys:
            self._keys = set(keys)
    
    def _save_keys(self):
        group_key = f"cache_group:{self.group_name}"
        cache.set(group_key, list(self._keys), timeout=86400*30)
    
    def add_key(self, key):
        self._keys.add(key)
        self._save_keys()
    
    def invalidate(self):
        if not self._keys:
            return
        
        cache.delete_many(self._keys)
        self._keys = set()
        self._save_keys()


def cached_property(timeout=None):
    """Decorator for making a property cached on the instance"""
    def decorator(func):
        @property
        @wraps(func)
        def wrapper(self):
            cache_key = f"cached_prop:{self.__class__.__name__}:{id(self)}:{func.__name__}"
            
            value = cache.get(cache_key)
            if value is None:
                value = func(self)
                if timeout:
                    cache.set(cache_key, value, timeout)
                else:
                    cache.set(cache_key, value)
            
            return value
        return wrapper
    return decorator


@cache_result(timeout=3600, prefix="featured_deals")
def get_featured_deals(limit=6):
    return DealService.get_active_deals().filter(
        is_featured=True
    ).order_by('-created_at')[:limit]
