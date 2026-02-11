from collections.abc import Iterable, Iterator
from typing import Self, cast


class chaindict[K, V](dict[K, V]):
    chain: list[dict[K, V]]
    _key_cache: list[K] | None

    __sentinel = object()

    def __init__(self, *chain: dict[K, V]):
        # only pretends to be a `dict`, but super().items() should be empty.
        super().__init__()
        self.chain = []
        self._key_cache = None

        for d in chain:
            if isinstance(d, chaindict):
                self.chain.extend(d.chain)
            else:
                self.chain.append(d)

    def __getitem__(self, key: K) -> V:
        for d in self.chain:
            if key in d:
                return d[key]
        raise KeyError(key)

    def __setitem__(self, key: K, value: V) -> None:
        if not self.chain:
            self.chain.append(dict())
        self.chain[0][key] = value
        self._key_cache = None

    def __delitem__(self, key: K) -> None:
        for d in self.chain:
            if key in d:
                del d[key]
                self._key_cache = None
                return
        raise KeyError(key)

    def __contains__(self, key: K) -> bool:
        return any(key in d for d in self.chain)

    def pop(self, key: K, default: V | object = __sentinel) -> V:
        for d in self.chain:
            if key in d:
                self._key_cache = None
                return d.pop(key)

        if default is self.__sentinel:
            raise KeyError(key)
        else:
            return cast(V, default)

    def copy(self) -> Self:
        """copy all chains, all referenced dictionaries are copied"""
        return type(self)(*(link.copy() for link in self.chain))

    def get[T](self, key: K, default: T = None) -> V | T:
        try:
            return self[key]
        except KeyError:
            return default

    def append_chain(self, link: dict[K, V]) -> None:
        if isinstance(link, chaindict):
            self.chain.extend(link.chain)
        else:
            self.chain.append(link)
        self._key_cache = None

    def prepend_chain(self, link: dict[K, V]):
        if isinstance(link, chaindict):
            self.chain[0:0] = link.chain
        else:
            self.chain.insert(0, link)
        self._key_cache = None

    def extend_chain(self, chain: Iterable[dict[K, V]]) -> None:
        for link in chain:
            self.append_chain(link)

    def pop_chain(self, index: int = -1) -> dict[K, V]:
        return self.chain.pop(index)

    def _compute_keys(self) -> list[K]:
        seen: set[K] = set()
        keys: list[K] = []

        for d in self.chain:
            for k in d:
                if k not in seen:
                    seen.add(k)
                    keys.append(k)

        return keys

    def keys(self) -> list[K]:
        if self._key_cache is None:
            self._key_cache = self._compute_keys()
        return list(self._key_cache)

    def values(self) -> list[V]:
        return [self[k] for k in self.keys()]

    def items(self) -> list[tuple[K, V]]:
        return [(k, self[k]) for k in self.keys()]

    def __len__(self) -> int:
        return len(self.keys())

    def flatten(self) -> dict[K, V]:
        return dict(self.items())

    def __iter__(self) -> Iterator[K]:
        return iter(self.keys())

    def __repr__(self):
        return f"{type(self).__name__}{tuple(self.chain)!r}"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, chaindict):
            return self.flatten() == other.flatten()
        if isinstance(other, dict):
            return self.flatten() == other
        return NotImplemented

    @staticmethod
    def top(dct: dict[K, V]) -> dict[K, V] | None:
        """get the top-most dictionary in the chain if dct is a chaindict"""
        if isinstance(dct, chaindict):
            if dct.chain:
                return dct.chain[0]
        return None
