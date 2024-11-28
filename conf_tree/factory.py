from __future__ import annotations

from typing import Type, cast

from .abstract import ConfTree
from .models import Vendor
from .vendors import AristaCT, CiscoCT, HuaweiCT

__all__ = ("ConfTreeFactory",)


class ConfTreeFactory:
    VENDOR_MAP = {
        Vendor.ARISTA: AristaCT,
        Vendor.CISCO: CiscoCT,
        Vendor.HUAWEI: HuaweiCT,
    }

    def __new__(cls, vendor: Vendor, line: str = "", parent: ConfTree | None = None) -> ConfTree:  # type: ignore[misc]
        _ct_class: Type[ConfTree] = cls.get_class(vendor)
        node = _ct_class(line=line, parent=parent)
        node = cast(ConfTree, node)
        return node

    @classmethod
    def get_class(cls, vendor: Vendor) -> Type[ConfTree]:
        _ct_class = cls.VENDOR_MAP.get(vendor)
        if _ct_class is None:
            raise NotImplementedError(f"unknown vendor {vendor}")
        return _ct_class
