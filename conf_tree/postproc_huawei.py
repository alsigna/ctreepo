from .abstract import ConfTree
from .postproc import ConfTreePostProc, register_rule
from .vendors import HuaweiCT

__all__ = (
    "HuaweiPostProcAAA",
    "HuaweiPostProcBGP",
    "HuaweiPostProcInterface",
    "HuaweiPostProcPrefixList",
    "HuaweiPostProcRoutePolicy",
    "HuaweiPostProcTacacs",
)


@register_rule
class HuaweiPostProcAAA(ConfTreePostProc):
    @classmethod
    def process(cls, ct: ConfTree) -> None:
        """Пост-обработка секции aaa.

        - Для пустых секций добавляем заглушку, что бы корректно генерировался патч
        - Работаем с пользователями:
            - если пароль пустой в diff, значит он не меняется и этот узел и
                соответствующий ему undo нужно удалить
            - если пароль пустой (не задан в vars) и при этом нет undo узла, значит сейчас
                на устройстве нет пользователя и нужно уделить все узлы с его именем, иначе
                система будет выпадать с ошибкой
            - если в diff есть пароль, значит мы его меняем, и соответствующий undo
                узел нужно удалить (только его)
            - если есть undo пользователя, тогда нужно удалить все ноды с его настройками
                и оставить только undo username
            - правим настройки, типа privilege level и пр, что бы они системой принимались
        - Если после всех манипуляций секция aaa стала пустой (а такое может быть, если diff
            состоял только из узлов с паролями, которые были удалены алгоритмом), тогда и саму
            секцию aaa нужно удалить
        """
        if not isinstance(ct, HuaweiCT):
            return
        aaa = ct.children.get("aaa")
        if not isinstance(aaa, HuaweiCT):
            return

        lines_to_delete = []
        nodes_to_delete = set()
        for node in aaa.children.values():
            ### шаг 1
            # пустой пароль - значит во входных данных ничего не было и пароль не меняем, поэтому
            # эти узлы, и соответствующие им undo-узлы нужно удалить
            if node.line.endswith("password irreversible-cipher"):
                _, user, *_ = node.line.split()
                lines_to_delete.append(f"local-user {user} password irreversible-cipher")
                undo_line = f"undo local-user {user} password irreversible-cipher"
                lines_to_delete.append(undo_line)
                # проверяем, если ли undo нода, если есть, значит пользователь существует уже в системе
                # если нет - значит нужно удалить все ноды для настройки этого пользователя
                if len([node for node in aaa.children.values() if node.line.startswith(undo_line)]) == 0:
                    lines_to_delete.append(f"local-user {user}")
            ### шаг 2
            # undo-узел и обычный узел с password для одного и того же пользователя,
            # значит мы меняем пароль, поэтому нужно undo-узел удалить
            elif not node.line.startswith("undo ") and " password irreversible-cipher " in node.line:
                _, user, *_ = node.line.split()
                lines_to_delete.append(f"undo local-user {user} password irreversible-cipher")

        nodes_to_delete.update([node for node in aaa.children.values() if node.line.startswith(tuple(lines_to_delete))])
        for node in nodes_to_delete:
            node.delete()
        aaa.rebuild()

        ### шаг 3
        # теперь, если остались undo-узлы с password, значит удаляем пользователя целиком, а значит
        # нужно поменять строку на undo local-user {user}, и удалить остальные узлы с этим пользователем
        lines_to_delete = []
        nodes_to_delete = set()
        for node in aaa.children.values():
            if node.line.startswith("undo ") and " password irreversible-cipher " in node.line:
                _, _, user, *_ = node.line.split()
                lines_to_delete.append(f"undo local-user {user} ")  # с пробелом в конце
                node.line = f"undo local-user {user}"  # а тут без, что бы endswith не захватил эту строку
        nodes_to_delete.update([node for node in aaa.children.values() if node.line.startswith(tuple(lines_to_delete))])
        for node in nodes_to_delete:
            node.delete()
        aaa.rebuild()

        ### шаг 4
        # правим undo узлы, что бы они принимались устройством
        for child in aaa.children.values():
            if not child.line.startswith("undo "):
                continue
            # видимо придется вносить еще или переделывать эту часть, пока только о level и service-type знаю
            if " service-type " in child.line or " level " in child.line:
                child.line = " ".join(child.line.split()[:4])
        aaa.rebuild()
        if len(aaa.children) == 0:
            aaa.delete()


@register_rule
class HuaweiPostProcBGP(ConfTreePostProc):
    @classmethod
    def process(cls, ct: ConfTree) -> None:
        if not isinstance(ct, HuaweiCT):
            return
        filtered_bgp = [node for node in ct.children.values() if node.line.startswith("bgp")]
        if len(filtered_bgp) != 1:
            return
        else:
            bgp = filtered_bgp[0]
        bgp_global = {node.line: node for node in bgp.children.values() if len(node.children) == 0}
        bgp_af = {node.line: node for node in bgp.children.values() if len(node.children) != 0}
        bgp.children = bgp_global | bgp_af
        bgp.rebuild()


@register_rule
class HuaweiPostProcInterface(ConfTreePostProc):
    @classmethod
    def process(cls, ct: ConfTree) -> None:
        if not isinstance(ct, HuaweiCT):
            return

        for child in ct.children.values():
            if child.line.startswith("undo interface "):
                child.line = child.line.replace("undo interface ", "clear configuration interface ")
            elif child.line.startswith("interface "):
                nodes_to_delete = set()
                for sub_child in child.children.values():
                    if sub_child.line == "undo port link-type hybrid":
                        sub_child.line = "undo port link-type"
                        nodes_to_delete.update(
                            [node for node in child.children.values() if node.line.startswith("undo port hybrid ")]
                        )
                for node in nodes_to_delete:
                    node.delete()
                child.rebuild()

        ct.rebuild()


@register_rule
class HuaweiPostProcPrefixList(ConfTreePostProc):
    @classmethod
    def process(cls, ct: ConfTree) -> None:
        if not isinstance(ct, HuaweiCT):
            return
        pl_statements: dict[str, list[str]] = {}
        to_delete: list[ConfTree] = []
        for child in ct.children.values():
            if child.line.startswith("ip ip-prefix "):
                _, _, pl_name, _, pl_indx, *_ = child.line.split()
                if pl_name not in pl_statements:
                    pl_statements[pl_name] = []
                pl_statements[pl_name].append(pl_indx)
        for child in ct.children.values():
            if child.line.startswith("undo ip ip-prefix "):
                _, _, _, pl_name, _, pl_indx, *_ = child.line.split()
                if pl_indx in pl_statements.get(pl_name, []):
                    to_delete.append(child)
                else:
                    child.line = f"undo ip ip-prefix {pl_name} index {pl_indx}"
        for node in to_delete:
            node.delete()
        ct.rebuild()


@register_rule
class HuaweiPostProcRoutePolicy(ConfTreePostProc):
    @classmethod
    def process(cls, ct: ConfTree) -> None:
        if not isinstance(ct, HuaweiCT):
            return
        for child in ct.children.values():
            if child.line.startswith("undo route-policy "):
                child.line = child.line.replace("permit ", "")
                child.line = child.line.replace("deny ", "")
        ct.rebuild()


@register_rule
class HuaweiPostProcTacacs(ConfTreePostProc):
    @classmethod
    def process(cls, ct: ConfTree) -> None:
        if not isinstance(ct, HuaweiCT):
            return
        filtered_tacacs = [
            node
            for node in ct.children.values()
            if node.line.startswith(("hwtacacs-server template", "hwtacacs server template"))
        ]
        if len(filtered_tacacs) != 1:
            return
        else:
            tacacs = filtered_tacacs[0]

        lines_to_delete = []
        nodes_to_delete = set()
        for node in tacacs.children.values():
            ### шаг 1
            # пустой пароль - значит во входных данных ничего не было и пароль не меняем, поэтому
            # этот узел, и соответствующий ему undo-узел нужно удалить
            # ("shared-key cipher  secondary", "shared-key cipher  third")
            if node.line.endswith("shared-key cipher"):
                lines_to_delete.append(node.line)
                lines_to_delete.append(f"undo {node.line}")
            ### шаг 2
            # undo-узел и обычный узел с password, значит мы меняем пароль, нужно undo-узел удалить
            elif not node.line.startswith("undo ") and " shared-key cipher " in node.line:
                lines_to_delete.append(f"undo {node.line}")
        nodes_to_delete.update(
            [node for node in tacacs.children.values() if node.line.startswith(tuple(lines_to_delete))]
        )
        for node in nodes_to_delete:
            node.delete()
        tacacs.rebuild()

        ### шаг 3
        # теперь, если остались undo-узлы с password, значит их нужно поменять,
        # отрезав пароль, иначе система не примет команду
        lines_to_delete = []
        nodes_to_delete = set()
        for node in tacacs.children.values():
            if node.line.startswith("undo ") and " shared-key cipher " in node.line:
                lines_to_delete.append(" ".join(node.line.split()[:-2]))
        nodes_to_delete.update(
            [node for node in tacacs.children.values() if node.line.startswith(tuple(lines_to_delete))]
        )
        for node in nodes_to_delete:
            node.delete()
        tacacs.rebuild()
        if len(tacacs.children) == 0:
            tacacs.delete()
