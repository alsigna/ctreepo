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
        include_tags: list[str],
        include_mode: Literal["or", "and"],
        exclude_tags: list[str],
        include_children: bool,
    ) -> list[ConfTree]:
        """рекурсивный поиск."""
        result = []

        if len(string) == 0:
            string_match = True
        else:
            string_match = re.search(string, ct.line) is not None

        if len(include_tags) == 0:
            tags_match = True
        elif include_mode == "or" and not set(include_tags).isdisjoint(set(ct.tags)):
            tags_match = True
        elif include_mode == "and" and set(include_tags).issubset(set(ct.tags)):
            tags_match = True
        else:
            tags_match = False

        if not set(exclude_tags).isdisjoint(set(ct.tags)):
            tags_match = False

        match_result = all([string_match, tags_match])
        if match_result:
            result.append(ct.copy(children=include_children))
        if not match_result or not include_children:
            for child in ct.children.values():
                result.extend(
                    cls._search(
                        ct=child,
                        string=string,
                        include_tags=include_tags,
                        include_mode=include_mode,
                        exclude_tags=exclude_tags,
                        include_children=include_children,
                    )
                )

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
        include_children: bool = False,
    ) -> ConfTree:
        """Поиск конфигурации в дереве.

        Args:
            ct (ConfigTree): где ищем
            string (str): что ищем, может быть regex строкой
            include_tags (list[str]): список тегов, по которым выборку делаем
            include_mode (Literal["or", "and"]): логика объединения критериев поиска
            exclude_tags (list[str]): список тегов-исключений, не должно быть на узле
            include_children (bool): включать потомков найденной секции или нет

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
            ct=ct,
            string=string,
            include_tags=include_tags,
            include_mode=include_mode,
            exclude_tags=exclude_tags,
            include_children=include_children,
        )
        for node in filter_result:
            root.merge(node)
        return root
