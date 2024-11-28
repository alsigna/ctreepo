import re
from typing import Literal

from .abstract import ConfTree

__all__ = ("ConfTreeSearcher",)


class ConfTreeSearcher:
    @classmethod
    def _search(
        cls,
        ct: ConfTree,
        string: str,
        tags: list[str],
        mode: Literal["or", "and"],
        exclude_tags: list[str],
    ) -> list[ConfTree]:
        """рекурсивный поиск.

        Args:
            ct (ConfigTree): где ищем
            string (str): что ищем, может быть regex строкой
            tags (list[str]): список тегов, по которым можно выборку сделать
            mode (Literal["or", "and"]): логика объединения тегов для поиска
            exclude_tags (list[str]): список тегов-исключений, не должно быть на узле

        Returns:
            list[ConfTree]: список найденных нод
        """
        result = []

        if len(string) == 0:
            string_match = True
        else:
            string_match = re.search(string, ct.line) is not None

        if len(tags) == 0:
            tags_match = True
        elif mode == "or" and not set(tags).isdisjoint(set(ct.tags)):
            tags_match = True
        elif mode == "and" and set(tags).issubset(set(ct.tags)):
            tags_match = True
        else:
            tags_match = False

        if not set(exclude_tags).isdisjoint(set(ct.tags)):
            tags_match = False

        if all([string_match, tags_match]):
            result.append(ct.copy(children=False))
        for child in ct.children.values():
            result.extend(cls._search(ct=child, string=string, tags=tags, mode=mode, exclude_tags=exclude_tags))

        return result

    @classmethod
    def search(
        cls,
        ct: ConfTree,
        *,
        string: str = "",
        include_tags: list[str] | None = None,
        include_mode: Literal["or", "and"] = "or",
        exclude_tags: list[str] | None = None,
    ) -> ConfTree:
        """Поиск конфигурации в дереве.

        Args:
            ct (ConfigTree): где ищем
            string (str): что ищем, может быть regex строкой
            include_tags (list[str]): список тегов, по которым выборку делаем
            include_mode (Literal["or", "and"]): логика объединения критериев поиска
            exclude_tags (list[str]): список тегов-исключений, не должно быть на узле

        Returns:
            ConfigTree: новое дерево с отфильтрованным результатом
        """
        if include_tags is None:
            include_tags = []
        if exclude_tags is None:
            exclude_tags = []
        string = string.strip()
        root = ct.__class__()
        if len(string) == 0 and len(include_tags) == 0 and len(exclude_tags) == 0:
            return root
        filter_result = cls._search(
            ct=ct, string=string, tags=include_tags, mode=include_mode, exclude_tags=exclude_tags
        )
        for node in filter_result:
            root.merge(node)
        return root
