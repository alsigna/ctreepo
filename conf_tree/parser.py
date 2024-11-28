from __future__ import annotations

import abc
import re
from pathlib import Path
from typing import Type

import yaml

from .abstract import ConfTree
from .factory import ConfTreeFactory
from .models import TaggingRule, Vendor

__all__ = (
    "ConfTreeParser",
    "TaggingRules",
    "TaggingRulesFile",
    "TaggingRulesDict",
)


class TaggingRules(abc.ABC):
    @property
    def rules(self) -> dict[Vendor, list[TaggingRule]]:
        """Правила для расстановки тегов в на строки конфигурации.

        Формат следующий:

        {
            "huawei": [ParsingRule-1, ParsingRule-2],
            "arista": [ParsingRule-N],
            "other_vendor": [],
        }

        ParsingRule это модель вида
        {
            "regex": "^ssl policy my_policy",
            "tags": ["ssl", "my_policy"],
        }
        """
        if not hasattr(self, "_rules"):
            self.load_rules()
        return self._rules

    @rules.setter
    def rules(self, rules: dict[Vendor, list[TaggingRule]]) -> None:
        self._rules = rules

    @abc.abstractmethod
    def load_rules(self) -> None:
        """Загрузка правил.

        Описывается конкретной реализацией класса
        """


class TaggingRulesFile(TaggingRules):
    _instances: dict[Path, TaggingRulesFile] = {}

    def __new__(cls, filename: Path | str) -> TaggingRulesFile:
        if isinstance(filename, str):
            filename = Path(Path.cwd(), filename)
        if filename not in cls._instances:
            cls._instances[filename] = super().__new__(cls)
        return cls._instances[filename]

    def __init__(self, filename: Path | str) -> None:
        if isinstance(filename, str):
            filename = Path(Path.cwd(), filename)
        self.filename = filename

    def load_rules(self) -> None:
        result = {}
        with open(self.filename, "r") as f:
            data = yaml.safe_load(f)
        for vendor, rules in (data.get("tagging-rules") or {}).items():
            if vendor not in [e.value for e in Vendor]:
                continue
            result[Vendor(vendor)] = [TaggingRule(**rule) for rule in rules]  # type: ignore[arg-type]

        self.rules = result


class TaggingRulesDict(TaggingRules):

    def __init__(self, rules_dict: dict[Vendor, list[dict[str, str | list[str]]]]) -> None:
        self.rules_dict = rules_dict

    def load_rules(self) -> None:
        result = {}
        for vendor, rules in self.rules_dict.items():
            if vendor not in [e.value for e in Vendor]:
                continue
            result[Vendor(vendor)] = [TaggingRule(**rule) for rule in rules]  # type: ignore[arg-type]

        self.rules = result


class ConfTreeParser:
    def __init__(self, vendor: Vendor, tagging_rules: TaggingRules | None = None) -> None:
        self._class = ConfTreeFactory.get_class(vendor)
        if tagging_rules is None:
            self.tagging_rules = []
        else:
            self.tagging_rules = tagging_rules.rules.get(vendor, [])

    def _get_tags(self, line: str) -> list[str] | None:
        for rule in self.tagging_rules:
            if m := re.search(rule.regex, line):
                return [*rule.tags, *m.groups()]
        return None

    def _parse(self, ct: Type[ConfTree], config: str) -> ConfTree:
        root = ct()
        section = [root]
        spaces = [0]
        previous_node: ConfTree = root
        for line in config.splitlines():
            if len(line.strip()) == 0:
                continue
            skip_pattern = "|".join(ct.junk_lines)  # type: ignore[arg-type]
            if re.fullmatch(skip_pattern, line):
                continue

            # число пробелов у текущей строки
            current_space = len(line) - len(line.lstrip())
            line = line.lstrip()

            # мы вошли в секцию
            if current_space > spaces[-1]:
                section.append(previous_node)
                spaces.append(current_space)
            # мы вышли из секции
            elif current_space < spaces[-1]:
                while current_space != spaces[-1]:
                    _ = section.pop()
                    _ = spaces.pop()

            parent = section[-1]
            if len(self.tagging_rules) != 0:
                full_line = parent._formal_path
                full_line.append(line)
                tags = self._get_tags(" / ".join(full_line))
            else:
                tags = None

            if line in parent.children:
                previous_node = parent.children[line]
            else:
                previous_node = ct(line=line, parent=parent, tags=tags)

        return root

    def parse(self, config: str) -> ConfTree:
        config = self._class.pre_run(config)
        root = self._parse(self._class, config)
        root.post_run()
        return root
