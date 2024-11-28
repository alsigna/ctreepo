from textwrap import dedent

import pytest

from conf_tree import AristaCT, ConfTree, ConfTreeFactory, HuaweiCT, Vendor


def test_get_class() -> None:
    assert ConfTreeFactory.get_class(Vendor.ARISTA) == AristaCT
    assert ConfTreeFactory.get_class(Vendor.HUAWEI) == HuaweiCT


def test_new() -> None:
    huawei_config = dedent(
        """
        ip vpn-instance LAN
         ipv4-family
          vpn-target 123:123 export-extcommunity evpn
          vpn-target 123:123 import-extcommunity evpn
         vxlan vni 123
        #
        interface gi0/0/0
         ip address 1.1.1.1 255.255.255.252
        #
        interface gi0/0/1
         ip address 1.1.1.1 255.255.255.252
        #
        """
    ).strip()
    arista_config = dedent(
        """
        ip vpn-instance LAN
           ipv4-family
              vpn-target 123:123 export-extcommunity evpn
              vpn-target 123:123 import-extcommunity evpn
           vxlan vni 123
        !
        interface gi0/0/0
           ip address 1.1.1.1 255.255.255.252
        !
        interface gi0/0/1
           ip address 1.1.1.1 255.255.255.252
        !
        """
    ).strip()

    huawei_root: ConfTree = ConfTreeFactory(Vendor.HUAWEI)  # type: ignore[assignment]
    huawei_lan: ConfTree = ConfTreeFactory(Vendor.HUAWEI, "ip vpn-instance LAN", huawei_root)  # type: ignore[assignment]
    huawei_ipv4_af_lan: ConfTree = ConfTreeFactory(Vendor.HUAWEI, " ipv4-family", huawei_lan)  # type: ignore[assignment]
    _ = ConfTreeFactory(Vendor.HUAWEI, "  vpn-target 123:123 export-extcommunity evpn", huawei_ipv4_af_lan)
    _ = ConfTreeFactory(Vendor.HUAWEI, "  vpn-target 123:123 import-extcommunity evpn", huawei_ipv4_af_lan)
    _ = ConfTreeFactory(Vendor.HUAWEI, " vxlan vni 123", huawei_lan)
    huawei_intf_000: ConfTree = ConfTreeFactory(Vendor.HUAWEI, "interface gi0/0/0", huawei_root)  # type: ignore[assignment]
    _ = ConfTreeFactory(Vendor.HUAWEI, " ip address 1.1.1.1 255.255.255.252", huawei_intf_000)
    huawei_intf_001: ConfTree = ConfTreeFactory(Vendor.HUAWEI, "interface gi0/0/1", huawei_root)  # type: ignore[assignment]
    _ = ConfTreeFactory(Vendor.HUAWEI, " ip address 1.1.1.1 255.255.255.252", huawei_intf_001)
    assert huawei_root.config == huawei_config

    arista_root: ConfTree = ConfTreeFactory(Vendor.ARISTA)  # type: ignore[assignment]
    arista_lan: ConfTree = ConfTreeFactory(Vendor.ARISTA, "ip vpn-instance LAN", arista_root)  # type: ignore[assignment]
    arista_ipv4_af_lan: ConfTree = ConfTreeFactory(Vendor.ARISTA, " ipv4-family", arista_lan)  # type: ignore[assignment]
    _ = ConfTreeFactory(Vendor.ARISTA, "  vpn-target 123:123 export-extcommunity evpn", arista_ipv4_af_lan)
    _ = ConfTreeFactory(Vendor.ARISTA, "  vpn-target 123:123 import-extcommunity evpn", arista_ipv4_af_lan)
    _ = ConfTreeFactory(Vendor.ARISTA, " vxlan vni 123", arista_lan)
    arista_intf_000: ConfTree = ConfTreeFactory(Vendor.ARISTA, "interface gi0/0/0", arista_root)  # type: ignore[assignment]
    _ = ConfTreeFactory(Vendor.ARISTA, " ip address 1.1.1.1 255.255.255.252", arista_intf_000)
    arista_intf_001: ConfTree = ConfTreeFactory(Vendor.ARISTA, "interface gi0/0/1", arista_root)  # type: ignore[assignment]
    _ = ConfTreeFactory(Vendor.ARISTA, " ip address 1.1.1.1 255.255.255.252", arista_intf_001)
    assert arista_root.config == arista_config

    vendor = "incorrect"
    with pytest.raises(Exception) as exc:
        _ = ConfTreeFactory(vendor)  # type: ignore[arg-type]
    assert str(exc.value) == f"unknown vendor {vendor}"
