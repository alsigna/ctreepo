from pathlib import Path
from typing import Any, Literal

from .abstract import ConfTree
from .differ import ConfTreeDiffer
from .models import Vendor
from .parser import ConfTreeParser, TaggingRulesDict, TaggingRulesFile
from .postproc import ConfTreePostProc
from .searcher import ConfTreeSearcher
from .serializer import ConfTreeSerializer

__all__ = ("ConfTreeEnv",)


class ConfTreeEnv:
    def __init__(
        self,
        vendor: Vendor,
        *,
        tagging_rules: Path | str | list[dict[str, str | list[str]]] | None = None,
        ordered_sections: list[str] | None = None,
        no_diff_sections: list[str] | None = None,
        post_proc_rules: list[type[ConfTreePostProc]] | None = None,
    ):
        if isinstance(tagging_rules, str) or isinstance(tagging_rules, Path):
            _tr_file = TaggingRulesFile(tagging_rules)
        else:
            _tr_file = None
        if isinstance(tagging_rules, list):
            _tr_dict = TaggingRulesDict({vendor: tagging_rules})
        else:
            _tr_dict = None

        self.vendor = vendor
        self._parser = ConfTreeParser(vendor=self.vendor, tagging_rules=_tr_file or _tr_dict)
        self._ordered_sections = ordered_sections
        self._no_diff_sections = no_diff_sections
        self._post_proc_rules = post_proc_rules

    def parse(
        self,
        config: str,
    ) -> ConfTree:
        return self._parser.parse(
            config=config,
        )

    def diff(
        self,
        a: ConfTree,
        b: ConfTree,
        masked: bool = False,
        reorder_root: bool = True,
    ) -> ConfTree:
        return ConfTreeDiffer.diff(
            a=a,
            b=b,
            masked=masked,
            reorder_root=reorder_root,
            ordered_sections=self._ordered_sections,
            no_diff_sections=self._no_diff_sections,
            post_proc_rules=self._post_proc_rules,
        )

    def to_dict(
        self,
        ct: ConfTree,
    ) -> dict[str, Any]:
        return ConfTreeSerializer.to_dict(root=ct)

    def from_dict(
        self,
        data: dict[str, Any],
    ) -> ConfTree:
        return ConfTreeSerializer.from_dict(
            vendor=self.vendor,
            data=data,
        )

    def search(
        self,
        ct: ConfTree,
        *,
        string: str = "",
        include_tags: list[str] | None = None,
        include_mode: Literal["or", "and"] = "or",
        exclude_tags: list[str] | None = None,
    ) -> ConfTree:
        return ConfTreeSearcher.search(
            ct=ct,
            string=string,
            include_tags=include_tags,
            include_mode=include_mode,
            exclude_tags=exclude_tags,
        )
