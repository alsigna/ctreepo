import abc
from typing import Type

from .abstract import CTree

__all__ = (
    "register_rule",
    "CTreePostProc",
    "_REGISTRY",
)


class CTreePostProc(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def process(cls, ct: CTree) -> None:
        """Пост-обработка конфигурации, например изменение, добавление, удаление команд."""


_REGISTRY: dict[str, Type[CTreePostProc]] = {}


def register_rule(cls: Type[CTreePostProc]) -> Type[CTreePostProc]:
    if cls.__class__.__name__ not in _REGISTRY:
        _REGISTRY[cls.__name__] = cls

    return cls
