import abc
from typing import Type

from .abstract import ConfTree

__all__ = (
    "register_rule",
    "ConfTreePostProc",
    "_REGISTRY",
)


class ConfTreePostProc(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def process(cls, ct: ConfTree) -> None:
        """Пост-обработка конфигурации, например изменение, добавление, удаление команд."""


_REGISTRY: dict[str, Type[ConfTreePostProc]] = {}


def register_rule(cls: Type[ConfTreePostProc]) -> Type[ConfTreePostProc]:
    if cls.__class__.__name__ not in _REGISTRY:
        _REGISTRY[cls.__name__] = cls

    return cls
