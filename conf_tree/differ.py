import re
from typing import Type

from .abstract import ConfTree
from .postproc import _REGISTRY, ConfTreePostProc

__all__ = ("ConfTreeDiffer",)


class ConfTreeDiffer:
    @classmethod
    def _check_ordered(cls, a: ConfTree, ordered_sections: list[str] | None = None) -> bool:
        if ordered_sections is not None:
            for section in ordered_sections:
                formal_line = " / ".join(a._formal_path)
                if re.search(section, formal_line):
                    return True
        return False

    @classmethod
    def _check_no_diff(cls, a: ConfTree, no_diff_sections: list[str] | None = None) -> bool:
        if no_diff_sections is not None:
            for section in no_diff_sections:
                formal_line = " / ".join(a._formal_path)
                if re.search(section, formal_line):
                    return True
        return False

    @classmethod
    def _diff_list(
        cls,
        a: ConfTree,  # текущая конфигурация
        b: ConfTree,  # целевая
        *,
        existed_diff: ConfTree | None = None,
        ordered_sections: list[str] | None = None,
        no_diff_sections: list[str] | None = None,
        masked: bool = False,
        negative: bool = False,  # если True, то вычисляем, что нужно удалить, т.е. чего нет в целевой конфигурации
    ) -> list[ConfTree]:
        result = []
        _ordered = cls._check_ordered(a, ordered_sections)
        indx = 0
        if existed_diff is not None:
            b = b.apply(existed_diff)
        for child in a.children.values():
            # для секций, требующих полной перезаписи (без вычисления diff'a)
            _no_diff = cls._check_no_diff(child, no_diff_sections)
            if _no_diff:
                # делаем <undo> <section> (если она есть) когда negative=True
                #! upd: не делаем, потому что будет reordering и <undo> уедет в конец, если
                #! нужно удалять секцию, то это нужно добавлять через post-processing
                # if negative:
                #     if child.exists_in(b):
                #         root = child.copy(children=not negative)
                #         while len(node.children) == 1:
                #             node = list(node.children.values())[0]
                #         node.line = f"{node.undo} {node.line}"
                #         root.rebuild(deep=True)
                #         result.append(root)
                # целиком добавляем (negative=False)
                if not negative:
                    line = child.exists_in(b)
                    if len(line) == 0 or child != b.children.get(line):
                        root = child.copy(children=True)
                        result.append(root)
                continue
            if _ordered:
                if len(b.children) > indx and child.line == list(b.children.values())[indx].line:
                    line = child.line
                    indx += 1
                else:
                    line = ""
            else:
                line = child.exists_in(b, masked)
            if len(line) == 0:
                root = child.copy(children=not negative)
                if negative:
                    node = root
                    while len(node.children) == 1:
                        node = list(node.children.values())[0]
                    # добавить default? нужно кейс вспомнить
                    # _ = node.__class__(f"default {node.line}", node.parent, node.tags.copy())
                    node.line = f"{node.undo} {node.line}"
                    root.rebuild(deep=True)
                result.append(root)
            else:
                # todo тут если потомков нет, то нет смысла делать рекурсию, лишняя трата ресурсов
                nested_result = cls._diff_list(
                    child,
                    b.children[line],
                    existed_diff=None,
                    ordered_sections=ordered_sections,
                    no_diff_sections=no_diff_sections,
                    masked=masked,
                    negative=negative,
                )
                result.extend(nested_result)
        return result

    @classmethod
    def diff(
        cls,
        a: ConfTree,
        b: ConfTree,
        *,
        masked: bool = False,
        ordered_sections: list[str] | None = None,
        no_diff_sections: list[str] | None = None,
        reorder_root: bool = True,
        post_proc_rules: list[Type[ConfTreePostProc]] | None = None,
    ) -> ConfTree:
        # TODO тут подумать, что бы сразу в нужный parent крепить узел, а не делать merge списка потом

        if a.__class__ != b.__class__:
            raise RuntimeError("a and b should be instances of the same class")

        root = a.__class__()

        diff_list = cls._diff_list(
            a,
            b,
            existed_diff=None,
            ordered_sections=ordered_sections,
            no_diff_sections=no_diff_sections,
            masked=masked,
            negative=True,
        )
        for leaf in diff_list:
            root.merge(leaf)

        diff_list = cls._diff_list(
            b,
            a,
            existed_diff=root,
            ordered_sections=ordered_sections,
            no_diff_sections=no_diff_sections,
            masked=masked,
            negative=False,
        )
        for leaf in diff_list:
            root.merge(leaf)

        negative = {node.line: node for node in root.children.values() if node.line.startswith(node.undo)}
        for node in negative.values():
            node.tags.append("clear")
        if reorder_root:
            positive = {node.line: node for node in root.children.values() if not node.line.startswith(node.undo)}
            root.children = positive | negative

        if post_proc_rules is None:
            post_proc_rules = list(_REGISTRY.values())
        if isinstance(post_proc_rules, list):
            for rule in post_proc_rules:
                rule.process(root)

        return root
