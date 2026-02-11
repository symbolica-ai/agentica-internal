from typing import cast, overload

__all__ = ['bidict']


class bidict[K, V](dict[K, V]):
    """bijetive bidirectional dictionary"""

    inverse: dict[V, K]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inverse = {v: k for k, v in self.items()}

    def __setitem__(self, key: K, value: V) -> None:
        if value in self.inverse:
            other_key = self.inverse[value]
            raise ValueError(
                f"many to one ambiguity: the other key {other_key} already maps to {value}"
            )

        self.inverse[value] = key
        return super().__setitem__(key, value)

    def __delitem__(self, key: K):
        v = self[key]
        del self.inverse[v]
        return super().__delitem__(key)

    @overload
    def with_value(self, value: V, /) -> K:
        """get key with this value, raising KeyError if not found"""
        ...

    @overload
    def with_value(self, value: V, /, default: K) -> K:
        """get key with this value, falling back on default key if not found"""
        ...

    __sentinel = object()

    def with_value(self, value: V, /, default: K | object = __sentinel) -> K:
        """get key with this value"""
        if default is self.__sentinel:
            return self.inverse[value]
        return self.inverse.get(value, cast(K, default))
