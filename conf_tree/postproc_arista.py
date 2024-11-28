from .abstract import ConfTree
from .postproc import ConfTreePostProc, register_rule
from .vendors import AristaCT

__all__ = (
    "AristaPostProcAAA",
    "AristaPostProcBGP",
    "AristaPostProcPrefixList",
    "AristaPostProcTacacsKey",
    "AristaPostProcUsers",
)


@register_rule
class AristaPostProcAAA(ConfTreePostProc):
    @classmethod
    def process(cls, ct: ConfTree) -> None:
        if not isinstance(ct, AristaCT):
            return

        lines_to_check = (
            "aaa authentication login default",
            "aaa authentication login console",
            "aaa authentication enable default",
        )
        lines_to_delete = [
            f"no {' '.join(node.line.split()[:4])}"
            for node in ct.children.values()
            if node.line.startswith(lines_to_check)
        ]
        nodes_to_delete = set([node for node in ct.children.values() if node.line.startswith(tuple(lines_to_delete))])
        for node in nodes_to_delete:
            node.delete()
        ct.rebuild()


@register_rule
class AristaPostProcBGP(ConfTreePostProc):
    @classmethod
    def process(cls, ct: ConfTree) -> None:
        def _delete_nodes(ct: ConfTree) -> None:
            nodes_to_delete: list[ConfTree] = []
            for node in ct.children.values():
                if len(node.children) != 0:
                    _delete_nodes(node)
                    if len(node.children) == 0:
                        nodes_to_delete.append(node)
                else:
                    if node.line.startswith(tuple(lines_to_delete)) and not node.line.endswith(" peer group"):
                        nodes_to_delete.append(node)
            for node in nodes_to_delete:
                node.delete()

            ct.rebuild()

        if not isinstance(ct, AristaCT):
            return
        bgp_nodes = [node for node in ct.children.values() if node.line.startswith("router bgp ")]
        if len(bgp_nodes) != 1:
            return
        else:
            bgp = bgp_nodes[0]
        bgp_global = {node.line: node for node in bgp.children.values() if len(node.children) == 0}
        bgp_af = {node.line: node for node in bgp.children.values() if len(node.children) != 0}
        bgp.children = bgp_global | bgp_af
        bgp.rebuild()

        lines_to_delete = set()
        for node in bgp.children.values():
            if node.line.startswith("no neighbor ") and node.line.endswith(" peer group"):
                # no neighbor GROUP-PEER peer group
                _, _, peer_name, _, _ = node.line.split()
                lines_to_delete.add(f"no neighbor {peer_name}")
        _delete_nodes(bgp)
        bgp.rebuild()


@register_rule
class AristaPostProcPrefixList(ConfTreePostProc):
    @classmethod
    def process(cls, ct: ConfTree) -> None:
        if not isinstance(ct, AristaCT):
            return
        pl_statements: dict[str, list[str]] = {}
        to_change: list[ConfTree] = []
        # в pl_statements записываем pl и seq, которые будем настраивать
        for child in ct.children.values():
            if child.line.startswith("ip prefix-list "):
                _, _, pl_name, _, pl_indx, *_ = child.line.split()
                if pl_name not in pl_statements:
                    pl_statements[pl_name] = []
                pl_statements[pl_name].append(pl_indx)

        # проверяем, если no опция для комбинации pl+seq есть в pl_statements
        # значит мы меняем запись, если нет - значит просто удаляем
        for child in ct.children.values():
            if child.line.startswith("no ip prefix-list "):
                _, _, _, pl_name, _, pl_indx, *_ = child.line.split()
                if pl_indx in pl_statements.get(pl_name, []):
                    to_change.append(child)
                # и если просто удаляем, тогда меняем line у узла на тот формат, который принимается устройством
                else:
                    child.line = f"no ip prefix-list {pl_name} seq {pl_indx}"

        # те записи, которые меняем, нужно удалить перед тем, как настраивать
        clear_before_configure: dict[str, ConfTree] = {}
        for node in to_change:
            _, _, _, pl_name, _, pl_indx, *_ = node.line.split()
            new_node = node.__class__(
                line=f"no ip prefix-list {pl_name} seq {pl_indx}",
                parent=node.parent,
                tags=[tag for tag in node.tags if tag != "clear"],
            )
            clear_before_configure |= {new_node.line: new_node}
            node.delete()

        ct.children = clear_before_configure | ct.children
        ct.rebuild()


@register_rule
class AristaPostProcTacacsKey(ConfTreePostProc):
    @classmethod
    def process(cls, ct: ConfTree) -> None:
        if not isinstance(ct, AristaCT):
            return

        # если строка без пароля то удаляем этот и undo узлы
        if "tacacs-server key" in ct.children:
            lines_to_delete = ["tacacs-server key", "no tacacs-server key"]
        # если есть новый пароль, то удаляем только undo узел
        elif len([node for node in ct.children.values() if node.line.startswith("tacacs-server key ")]) == 1:
            lines_to_delete = ["no tacacs-server key"]
        else:
            lines_to_delete = []

        nodes_to_delete = set([node for node in ct.children.values() if node.line.startswith(tuple(lines_to_delete))])
        for node in nodes_to_delete:
            node.delete()
        ct.rebuild()


@register_rule
class AristaPostProcUsers(ConfTreePostProc):
    @classmethod
    def process(cls, ct: ConfTree) -> None:
        if not isinstance(ct, AristaCT):
            return

        lines_to_delete = []
        nodes_to_delete = set()
        for node in ct.children.values():
            if not node.line.startswith("username "):
                continue
            ### шаг 1
            # пустой пароль - значит во входных данных ничего не было и пароль не меняем, поэтому
            # эти узлы, и соответствующие им no-узлы нужно удалить
            if node.line.endswith("privilege 15 role network-admin secret"):
                _, user, *_ = node.line.split()
                lines_to_delete.append(f"username {user} privilege 15 role network-admin secret")
                lines_to_delete.append(f"no username {user} privilege 15 role network-admin secret sha512 ")
            ### шаг 2
            # обычный узел с password, значит мы меняем пароль, поэтому нужно no-узел удалить
            elif not node.line.startswith("no ") and " privilege 15 role network-admin secret " in node.line:
                _, user, *_ = node.line.split()
                lines_to_delete.append(f"no username {user} privilege 15 role network-admin secret sha512 ")
        nodes_to_delete.update([node for node in ct.children.values() if node.line.startswith(tuple(lines_to_delete))])
        for node in nodes_to_delete:
            node.delete()
        ct.rebuild()

        ### шаг 3
        # теперь, если остались no-узлы с password, значит удаляем пользователя целиком, а значит
        # нужно поменять строку на no username {user}
        lines_to_delete = []
        nodes_to_delete = set()
        for node in ct.children.values():
            if node.line.startswith("no ") and " privilege 15 role network-admin secret sha512 " in node.line:
                _, _, user, *_ = node.line.split()
                lines_to_delete.append(f"no username {user} ")  # с пробелом в конце
                node.line = f"no username {user}"  # а тут без, что бы endswith не захватил эту строку
        nodes_to_delete.update([node for node in ct.children.values() if node.line.startswith(tuple(lines_to_delete))])
        for node in nodes_to_delete:
            node.delete()
        ct.rebuild()
