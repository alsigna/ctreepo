from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections import deque

__all__ = ("ConfTree",)


class ConfTree(ABC):
    __slots__ = ["line", "parent", "children", "tags"]

    @property
    @abstractmethod
    def spaces(self) -> str:
        """количество пробелов для нового уровня."""

    @property
    @abstractmethod
    def section_exit(self) -> str:
        """как выходим из секции: exit/quit/..."""

    @property
    @abstractmethod
    def section_separator(self) -> str:
        """Чем разделяем блоки конфига между собой: !/#/..."""

    @property
    @abstractmethod
    def sections_without_exit(self) -> list[str]:
        """Список секций, из которых не нужно выходить.

        Некоторые секции не работают если явно выходить из них,
        например сертификаты в cisco, xpl в huawei.
        """

    @property
    @abstractmethod
    def sections_require_exit(self) -> list[str]:
        """Секции, которые могут быть пустыми.

        И для них необходимо явно прописывать выход,
        например route-map rm_DENY deny 10.
        """

    @property
    @abstractmethod
    def junk_lines(self) -> list[str]:
        """список линий, которые нужно игнорировать при анализе конфигурации."""

    @property
    @abstractmethod
    def undo(self) -> str:
        """как убираем конфигурацию, в общем случае: no/undo/..."""

    @property
    @abstractmethod
    def mask_patterns(self) -> list[str]:
        """паттерны для маскирования строк, указываем текст перед тем, что нужно заменить."""

    masking_string: str = "******"
    # empty_section_placeholder = "<-empty-section->"

    def __init__(self, line: str = "", parent: ConfTree | None = None, tags: list[str] | None = None) -> None:
        self.line = line.strip()

        # pattern = "|".join(self.mask_lines)
        # self.masked_line = re.sub(rf"({pattern}) \S+", rf"\1 {self.mask_pattern}", self.line)

        self.parent = parent
        self.children: dict[str, ConfTree] = {}

        if tags is not None:
            self.tags = tags
        elif parent is not None:
            self.tags = parent.tags
        else:
            self.tags = []

        if parent is not None:
            parent.children[line.strip()] = self

    @classmethod
    def mask_line(cls, line: str) -> str:
        # if len(cls.mask_patterns) == 0:
        #     return line
        pattern = "|".join(cls.mask_patterns)  # type: ignore [arg-type]
        if (m := re.fullmatch(pattern, line)) is not None:
            secret = [g for g in m.groups() if g is not None][0]
            return line.replace(secret, cls.masking_string)
        else:
            return line
        # return re.sub(rf"({pattern}) \S+", rf"\1 {cls.hidden_chars}", line)
        # return re.sub(pattern, rf"\g<before>{cls.masking_string}\g<after>", line)

    @property
    def masked_line(self) -> str:
        return self.mask_line(self.line)

    def __str__(self) -> str:
        """строковое представление: сама строка или 'root', если для корня вызываем."""
        return self.line or "root"

    def __repr__(self) -> str:
        """формальное представление объекта."""
        return f"({id(self)}) '{str(self)}'"

    def delete(self) -> None:
        to_delete = [self]
        stack = deque(self.children.values())
        while len(stack) > 0:
            node = stack.popleft()
            to_delete.append(node)
            if len(node.children) != 0:
                stack.extendleft(list(node.children.values())[::-1])
        for node in to_delete[::-1]:
            if node.parent is not None:
                _ = node.parent.children.pop(node.line)
                del node

    def __hash__(self) -> int:
        """вычисление hash."""
        return hash(self.formal_path)

    # todo добавить сравнение, с учетом порядка команд, как в differ сделано
    def __eq__(self, other: object) -> bool:
        """сравниваем два объекта.

        считаем узлы равными, если у них равны между собой:
        - строки настройки
        - одинаковые родители
        - одинаковые потомки

        Args:
            other (object): с чем сравниваем

        Returns:
            bool: равны или нет узлы
        """
        if not isinstance(other, ConfTree):
            return NotImplemented
        # возможно стоит сравнивать маскированные строки, что бы исключить разницу из-за хешей
        if self.line != other.line:
            return False
        if len(self.children) != len(other.children):
            return False

        self_parents = self._formal_path
        other_parents = other._formal_path

        if self_parents != other_parents:
            return False

        if set(self.tags) != set(other.tags):
            return False

        children_eq = []
        for line, node in self.children.items():
            other_node = other.children.get(line)
            if other_node is None:
                return False
            children_eq.append(node == other_node)
        return all(children_eq)

    @property
    def _formal_path(self) -> list[str]:
        result = []
        node = self
        while node.parent is not None:
            result.append(node.line)
            node = node.parent
        result.reverse()
        return result

    @property
    def formal_path(self) -> str:
        return " / ".join(self._formal_path)

    def _config(self, symbol: str, level: int, masked: bool) -> list[str]:
        line = self.masked_line if masked else self.line
        # if line == self.empty_section_placeholder:
        #     return []
        result = [symbol * level + line]
        for child in self.children.values():
            result.extend(child._config(symbol=symbol, level=level + 1, masked=masked))
        return result

    def _build_config(self, masked: bool) -> str:
        result = []
        level = 0
        node = self
        while node.parent is not None:
            result.append(node.masked_line if masked else node.line)
            level += 1
            node = node.parent
        result.reverse()
        result = [self.spaces * indx + line for indx, line in enumerate(result)]
        for child in self.children.values():
            result.extend(child._config(symbol=self.spaces, level=level, masked=masked))
            if self.parent is None:
                result.append(self.section_separator)
        return "\n".join(result)

    @property
    def config(self) -> str:
        return self._build_config(masked=False)

    @property
    def masked_config(self) -> str:
        return self._build_config(masked=True)

    @property
    def _formal_config(self) -> list[list[str]]:
        result = []
        for node in self.children.values():
            if len(node.children) == 0:
                result.append(node._formal_path)
            else:
                result.extend(node._formal_config)
        return result

    @property
    def formal_config(self) -> str:
        result = []

        node = self
        if len(self.children) == 0:
            return self.formal_path
        for node in self.children.values():
            if len(node.children) == 0:
                result.append(node._formal_path)
            else:
                result.extend(node._formal_config)

        return "\n".join([" / ".join(config) for config in result])

    def _build_patch(self, masked: bool) -> str:
        nodes = deque(self.children.values())
        result = []
        path_to_root = []

        node = self
        while node.parent is not None:
            path_to_root.append(node.masked_line if masked else node.line)
            node = node.parent
        path_to_root.reverse()

        while len(nodes) > 0:
            node = nodes.popleft()
            # if node.line == node.empty_section_placeholder:
            #     continue
            result.append(node.masked_line if masked else node.line)
            if len(node.children) != 0:
                if not re.fullmatch("|".join(self.sections_without_exit), node.formal_path):
                    nodes.appendleft(self.__class__(line=self.section_exit))
                nodes.extendleft(list(node.children.values())[::-1])
            elif len(self.sections_require_exit) != 0 and re.fullmatch(
                "|".join(self.sections_require_exit), node.formal_path
            ):
                nodes.appendleft(self.__class__(line=self.section_exit))
        result = path_to_root + result + [self.section_exit] * len(path_to_root)
        return "\n".join(result)

    @property
    def patch(self) -> str:
        return self._build_patch(masked=False)

    @property
    def masked_patch(self) -> str:
        return self._build_patch(masked=True)

    def _copy(self, children: bool, parent: ConfTree | None) -> ConfTree:
        if self.parent is not None and parent is None:
            parent = self.parent._copy(children=False, parent=None)

        new_obj = self.__class__(line=self.line, parent=parent, tags=self.tags.copy())
        if children:
            for child in self.children.values():
                _ = child._copy(children, new_obj)
        return new_obj

    def copy(self, children: bool = True) -> ConfTree:
        root = self._copy(children=children, parent=None)
        while root.parent is not None:
            root = root.parent
        return root

    def merge(self, other: ConfTree) -> None:
        for line, node in other.children.items():
            if line not in self.children:
                _ = node._copy(children=True, parent=self)
            else:
                self.children[line].merge(node)

    def _subtract(self, other: ConfTree, masked: bool = False) -> None:
        nodes_to_delete = []
        for child in self.children.values():
            line = child.exists_in(other, masked)
            if len(line) != 0:
                if len(child.children) != 0:
                    child._subtract(other.children[line])
                if len(child.children) == 0:
                    nodes_to_delete.append(child)
        for node in nodes_to_delete:
            node.delete()

    def subtract(self, other: ConfTree) -> ConfTree:
        result = self.copy()
        result._subtract(other=other)
        return result

    def _apply(self, other: ConfTree) -> None:
        for child in other.children.values():
            if child.line.startswith(child.undo):
                line = child.line.replace(child.undo, "").strip()
                if line in self.children:
                    self.children[line].delete()
            else:
                if child.exists_in(self):
                    self.children[child.line]._apply(other=child)
                else:
                    child._copy(children=True, parent=self)

    def apply(self, other: ConfTree) -> ConfTree:
        result = self.copy()
        result._apply(other=other)
        return result

    def rebuild(self, deep: bool = False) -> None:
        new_children = {child.line: child for child in self.children.values()}
        self.children = new_children
        if deep:
            for child in self.children.values():
                child.rebuild(deep)

    def exists_in(self, other: ConfTree, masked: bool = False) -> str:
        if masked:
            for line, node in other.children.items():
                if self.masked_line == node.masked_line:
                    return line
            return ""
        else:
            if self.line in other.children:
                return self.line
            else:
                return ""

    def reorder(self, tags: list[str], *, reverse: bool = False) -> None:
        def _get_children_tags(node: ConfTree) -> list[str]:
            tags = node.tags
            for child in node.children.values():
                tags.extend(_get_children_tags(child))
            return list(set(tags))

        if len(tags) == 0:
            return

        no_tags = "_no_tags_nodes"
        children: dict[str, list[ConfTree]]

        if not reverse:
            children = {tag: [] for tag in tags}
        else:
            children = {tag: [] for tag in reversed(tags)}
        children[no_tags] = []

        for child in self.children.values():
            child_tags = _get_children_tags(child)
            common_tags = set(tags).intersection(set(child_tags))
            if len(common_tags) == 0:
                children[no_tags].append(child)
            else:
                tag = common_tags.pop()
                children[tag].append(child)

        self.children = {}
        for child_list in children.values():
            for child in child_list:
                self.children[child.line] = child

    @classmethod
    def pre_run(cls, config: str) -> str:
        return config

    def post_run(self) -> None:
        return
