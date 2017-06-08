# -*- coding: utf-8 -*-


#################
#
#
#
#
####################


class XXCacheStrategy:

    def __init__(self):
        pass

    def clean_cache(self, xxcache):
        if not isinstance(xxcache, XXCache):
            return False
        if len(xxcache._cache_list) == 0:
            return True
        del_key = xxcache._cache_list[0]
        del xxcache._cache_dict[del_key]
        del xxcache._cache_list[0]
        xxcache._cur_count -= 1
        return True


###############
#
#
#
#
#
################


class XXCache:

    def __init__(self, strategy=XXCacheStrategy(), limit=100):
        self._cache_list = []
        self._cache_dict = {}
        self._strategy = strategy
        self._limit = limit
        self._cur_count = 0

    def add(self, key, value):
        if self._cur_count > self._limit:
            self._check_list()
        self._cache_dict[key] = value
        self._cache_list.append(key)
        self._cur_count += 1

    def get(self, key):
        return self._cache_dict.get(key, None)

    def _check_list(self):
        self._strategy.clean_cache(self)
        pass
