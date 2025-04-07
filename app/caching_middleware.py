from cachetools import TTLCache, cached

cache = TTLCache(maxsize=100, ttl=300)  # Cache with a max size of 100 and time-to-live of 300 seconds

@cached(cache)
def get_cached_response(url, method, headers, data, cookies):
    return requests.request(
        method=method,
        url=url,
        headers=headers,
        data=data,
        cookies=cookies,
        allow_redirects=False
    )