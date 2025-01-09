# -*- coding: utf-8 -*-

"""
The dns_cache module handles DNS lookups and answers them from a cache
instead of making an actual request.
"""

import socket
import time

DEFAULT_EXPIRATION_S = 3600  # Default expiration time in s (1 hour)

dns_cache = {}
dns_expiration_s = DEFAULT_EXPIRATION_S
cache_enabled = True

# Save original function pointer fopr later use
prv_getaddrinfo = socket.getaddrinfo


def set_cache_expiration_time(expiration_s: int):
    """
    Set expiration time of DNS cache entries in seconds

    Args:
        timeout (int): expiration time in seconds
    """
    global dns_expiration_s
    dns_expiration_s = expiration_s


def enable():
    """
    Enable DNS Caching
    """
    global cache_enabled
    cache_enabled = True


def disable():
    """
    Disable DNS Caching
    """
    global cache_enabled
    cache_enabled = False


def clear():
    """
    Clears the dns cache
    """
    dns_cache.clear()


def cached_getaddrinfo(*args):
    """
    Replacement function for socket.getaddrinfo
    Checks if current DNS Query is already in cache and return it if the entry is not expired.
    Otherwise does a DNS lookup and saves the entry in the cache

    Returns:
        addrinfo
    """
        
    current_time = time.time()

    if cache_enabled:
        try:
            cached_result = dns_cache[args[:2]]
            if current_time < cached_result[0] + dns_expiration_s:
                return cached_result[1]
            else:
                del dns_cache[args[:2]]
                print(f"DNS Cache for {args[0]} entry removed because of timeout")
                raise KeyError
            
        except KeyError:
            dns_resolve = prv_getaddrinfo(*args)
            
            dns_cache[args[:2]] = [current_time, dns_resolve]  # Add DNS resolution to cache

            return dns_resolve
    else:
        return prv_getaddrinfo(*args)


# Override socket function to use the cached getaddrinfo
socket.getaddrinfo = cached_getaddrinfo
