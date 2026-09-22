from __future__ import annotations
import time
class FeedCache:
    def __init__(self,ttl_seconds:float): self._ttl=ttl_seconds; self._items={}
    def get(self,key):
        item=self._items.get(key)
        if item is None or time.monotonic()-item[0]>=self._ttl: self._items.pop(key,None); return None
        return item[1]
    def set(self,key,value): self._items[key]=(time.monotonic(),value)
    def clear(self): self._items.clear()
