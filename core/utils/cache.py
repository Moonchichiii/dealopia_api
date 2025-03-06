from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json


def generate_cache_key(prefix, *args, **kwargs):
    """Generate a unique cache key based on function arguments"""
    key_parts = [prefix]
    
    # Add positional args to key
    if args:
        for arg in args:
            if hasattr(arg, 'id'):  # Handle model instances
                key_parts.append(f"id:{arg.id}")
            elif isinstance(arg, (list, tuple, set)):
                key_parts.append(f"list:{len(arg)}")
            else:
                key_parts.append(str(arg))
    
    # Add keyword args to key
    if kwargs:
        # Sort kwargs by key for consistent ordering
        for key, value in sorted(kwargs.items()):
            if hasattr(value, 'id'):  # Handle model instances
                key_parts.append(f"{key}:id:{value.id}")
            elif isinstance(value, (dict, list, tuple, set)):
                # Hash complex objects to create a deterministic key segment
                hash_input = json.dumps(value, sort_keys=True)
                hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
                key_parts.append(f"{key}:hash:{hash_value}")
            else:
                key_parts.append(f"{key}:{value}")
    
    # Join parts and hash if necessary to stay within Redis key length limits
    key = ":".join(key_parts)
    if len(key) > 200:  # Redis keys can be up to 512MB, but we'll keep it reasonable
        # Hash everything except the prefix for consistent lookup
        hashed_part = hashlib.md5(":".join(key_parts[1:]).encode()).hexdigest()
        key = f"{prefix}:hash:{hashed_part}"
    
    return key


def cache_result(timeout=300, prefix=None, condition=None):
    """
    Cache decorator for functions and methods
    
    Args:
        timeout: Cache expiration time in seconds
        prefix: Optional prefix for the cache key
        condition: Function that determines whether to cache based on args/kwargs
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip caching if DEBUG is True and CACHE_IN_DEBUG is False
            if settings.DEBUG and not getattr(settings, 'CACHE_IN_DEBUG', False):
                return func(*args, **kwargs)
            
            # Skip caching if the condition function returns False
            if condition and not condition(*args, **kwargs):
                return func(*args, **kwargs)
            
            # Generate the cache key
            func_prefix = prefix or f"{func.__module__}.{func.__name__}"
            cache_key = generate_cache_key(func_prefix, *args, **kwargs)
            
            # Try to get cached result
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call the function and cache the result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def invalidate_cache_prefix(prefix):
    """
    Invalidate all cache keys with a specific prefix. This requires
    a cache backend that supports wildcard deletion.
    """
    if hasattr(cache, 'delete_pattern'):
        # Redis cache backend supports pattern-based deletion
        cache.delete_pattern(f"{prefix}:*")
    else:
        # Fallback to individual key deletion if supported
        if hasattr(cache, 'keys'):
            keys = cache.keys(f"{prefix}:*")
            if keys:
                cache.delete_many(keys)


class CacheGroup:
    """
    Helper class for managing related cache keys that should be invalidated together.
    """
    def __init__(self, group_name):
        self.group_name = group_name
        self._keys = set()
        self._load_keys()
    
    def _load_keys(self):
        """Load existing keys from the cache"""
        group_key = f"cache_group:{self.group_name}"
        keys = cache.get(group_key)
        if keys:
            self._keys = set(keys)
    
    def _save_keys(self):
        """Save the current keys to the cache"""
        group_key = f"cache_group:{self.group_name}"
        cache.set(group_key, list(self._keys), timeout=86400*30)  # 30 days
    
    def add_key(self, key):
        """Add a key to the group"""
        self._keys.add(key)
        self._save_keys()
    
    def invalidate(self):
        """Invalidate all keys in the group"""
        if not self._keys:
            return
        
        cache.delete_many(self._keys)
        self._keys = set()
        self._save_keys()


def cached_property(timeout=None):
    """
    Decorator for making a property cached on the instance.
    Similar to Django's cached_property but with a timeout.
    """
    def decorator(func):
        @property
        @wraps(func)
        def wrapper(self):
            # Create a key unique to this instance and method
            cache_key = f"cached_prop:{self.__class__.__name__}:{id(self)}:{func.__name__}"
            
            # Try to get from cache
            value = cache.get(cache_key)
            if value is None:
                # If not found, compute and cache with timeout
                value = func(self)
                if timeout:
                    cache.set(cache_key, value, timeout)
                else:
                    cache.set(cache_key, value)
            
            return value
        return wrapper
    return decorator