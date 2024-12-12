from typing import Any

from .abstract import CTree
from .factory import CTreeFactory
from .models import Vendor

__all__ = ("CTreeSerializer",)


class CTreeSerializer:
    @classmethod
    def to_dict(cls, root: CTree) -> dict[str, Any]:
        children: dict[str, dict[str, Any]] = {}
        result = {
            "line": root.line,
            "tags": root.tags,
        }
        for child in root.children.values():
            children |= {child.line: cls.to_dict(child)}
        return result | {"children": children}

    @classmethod
    def from_dict(cls, vendor: Vendor, data: dict[str, Any], parent: CTree | None = None) -> CTree:
        _ct_class = CTreeFactory.get_class(vendor)
        node = _ct_class(line=data.get("line", ""), parent=parent, tags=data.get("tags", []))
        for child in data.get("children", {}).values():
            cls.from_dict(vendor, child, node)
        return node
