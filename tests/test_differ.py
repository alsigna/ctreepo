from textwrap import dedent

import pytest

from conf_tree import AristaCT, ConfTreeDiffer, ConfTreeParser, HuaweiCT, Vendor
from conf_tree.postproc_huawei import HuaweiPostProcInterface, HuaweiPostProcRoutePolicy

config_interfaces_1 = """
interface 25GE1/0/1
 port link-type trunk
 undo port trunk allow-pass vlan 1
 stp edged-port enable
 storm suppression multicast packets 50
 storm suppression broadcast packets 200
 sflow sampling collector 1
 sflow sampling inbound
 device transceiver 25GBASE-COPPER
#
interface 25GE1/0/1.1234 mode l2
 encapsulation untag
 bridge-domain 1234
 statistics enable
#
interface 25GE1/0/2
 port link-type trunk
 undo port trunk allow-pass vlan 1
 stp edged-port enable
 storm suppression multicast packets 50
 storm suppression broadcast packets 200
 sflow sampling collector 1
 sflow sampling inbound
 device transceiver 25GBASE-COPPER
#
interface 25GE1/0/2.1234 mode l2
 encapsulation untag
 bridge-domain 1234
 statistics enable
#
""".strip()

config_interfaces_2 = """
#
interface 25GE1/0/2
 port link-type trunk
 undo port trunk allow-pass vlan 1
 stp edged-port enable
 storm suppression multicast packets 50
 storm suppression broadcast packets 200
 sflow sampling collector 1
 sflow sampling inbound
 description test
 device transceiver 25GBASE-COPPER
#
interface 25GE1/0/2.1234 mode l2
 encapsulation untag
 bridge-domain 1234
 statistics enable
#
""".strip()


def test_diff_wo_rules() -> None:
    diff_config = dedent(
        """
        interface 25GE1/0/2
         description test
        #
        undo interface 25GE1/0/1
        #
        undo interface 25GE1/0/1.1234 mode l2
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        interface 25GE1/0/2
        description test
        quit
        undo interface 25GE1/0/1
        undo interface 25GE1/0/1.1234 mode l2
        """
    ).strip()
    parser = ConfTreeParser(vendor=Vendor.HUAWEI)

    root1 = parser.parse(config_interfaces_1)
    root2 = parser.parse(config_interfaces_2)

    diff = ConfTreeDiffer.diff(root1, root2, post_proc_rules=[])
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_diff_w_rules() -> None:
    diff_config = dedent(
        """
        interface 25GE1/0/2
         description test
        #
        clear configuration interface 25GE1/0/1
        #
        clear configuration interface 25GE1/0/1.1234 mode l2
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        interface 25GE1/0/2
        description test
        quit
        clear configuration interface 25GE1/0/1
        clear configuration interface 25GE1/0/1.1234 mode l2
        """
    ).strip()
    parser = ConfTreeParser(vendor=Vendor.HUAWEI)

    root1 = parser.parse(config_interfaces_1)
    root2 = parser.parse(config_interfaces_2)

    diff = ConfTreeDiffer.diff(root1, root2)
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_vendor_mismatch() -> None:
    config = dedent(
        """
        ip community-list CL_NAME_1
         community 123:12345
        """
    )
    parser1 = ConfTreeParser(vendor=Vendor.HUAWEI)
    parser2 = ConfTreeParser(vendor=Vendor.ARISTA)
    root1 = parser1.parse(config)
    root2 = parser2.parse(config)
    assert root1.__class__ == HuaweiCT
    assert root2.__class__ == AristaCT

    with pytest.raises(RuntimeError) as exc:
        ConfTreeDiffer.diff(root1, root2)
    assert str(exc.value) == "a and b should be instances of the same class"


def test_processing_vendor_check() -> None:
    diff_config = dedent(
        """
        interface 25GE1/0/2
           description test
        !
        no interface 25GE1/0/1
        !
        no interface 25GE1/0/1.1234 mode l2
        !
        """
    ).strip()
    diff_patch = dedent(
        """
        interface 25GE1/0/2
        description test
        exit
        no interface 25GE1/0/1
        no interface 25GE1/0/1.1234 mode l2
        """
    ).strip()
    parser = ConfTreeParser(vendor=Vendor.ARISTA)

    root1 = parser.parse(config_interfaces_1)
    root2 = parser.parse(config_interfaces_2)

    diff = ConfTreeDiffer.diff(
        a=root1,
        b=root2,
        post_proc_rules=[
            HuaweiPostProcRoutePolicy,
            HuaweiPostProcInterface,
        ],
    )
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_reordered_config() -> None:
    config1 = dedent(
        """
        bgp 64512
         ipv4-family unicast
          import-route direct route-policy RP_CONNECTED
         ipv4-family vpn-instance LAN
          peer PEER_GROUP_1 route-policy RP_NAME_IN_1 import
          peer PEER_GROUP_1 route-policy RP_NAME_OUT export
          peer PEER_GROUP_2 route-policy RP_NAME_IN_2 import
          peer PEER_GROUP_2 route-policy RP_NAME_OUT export
          peer PEER_GROUP_3 route-policy RP_NAME_IN_3 import
          peer PEER_GROUP_3 route-policy RP_NAME_OUT export
        """
    ).strip()

    config2 = dedent(
        """
        bgp 64512
         ipv4-family vpn-instance LAN
          peer PEER_GROUP_1 route-policy RP_NAME_IN_1 import
          peer PEER_GROUP_2 route-policy RP_NAME_IN_2 import
          peer PEER_GROUP_3 route-policy RP_NAME_IN_3 import
          peer PEER_GROUP_1 route-policy RP_NAME_OUT export
          peer PEER_GROUP_2 route-policy RP_NAME_OUT export
          peer PEER_GROUP_3 route-policy RP_NAME_OUT export
         ipv4-family unicast
          import-route direct route-policy RP_CONNECTED
        """
    ).strip()

    parser = ConfTreeParser(vendor=Vendor.HUAWEI)
    root1 = parser.parse(config1)
    root2 = parser.parse(config2)

    print(ConfTreeDiffer.diff(root1, root2).config)
    assert len(ConfTreeDiffer.diff(root1, root2).config) == 0


def test_ordered_sections() -> None:
    current_config = dedent(
        """
        aaa accounting commands all default start-stop logging
        #
        section 1
         sub-line 1.2
         sub-line 1.1
         sub-line 1.3
         sub-section 2
          sub-line 2.2
          sub-line 2.1
        #
        aaa group server tacacs+ group_name
         server 10.1.0.2 vrf MGMT
         server 10.1.0.6 vrf MGMT
         server 10.1.0.4 vrf MGMT
         server 10.1.0.5 vrf MGMT
         server 10.1.0.3 vrf MGMT
        #
        """
    ).strip()
    target_config = dedent(
        """
        aaa accounting commands all default start-stop logging
        #
        aaa group server tacacs+ group_name
         server 10.1.0.6 vrf MGMT
         server 10.1.0.5 vrf MGMT
         server 10.1.0.4 vrf MGMT
         server 10.1.0.3 vrf MGMT
         server 10.1.0.7 vrf MGMT
        #
        section 1
         sub-line 1.1
         sub-section 2
          sub-line 2.1
          sub-line 2.2
          sub-line 2.3
         sub-line 1.2
         sub-line 1.3
        #
        some config
        """
    ).strip()
    diff_default = dedent(
        """
        aaa group server tacacs+ group_name
         undo server 10.1.0.2 vrf MGMT
         server 10.1.0.7 vrf MGMT
        #
        section 1
         sub-section 2
          sub-line 2.3
        #
        some config
        #
        """
    ).strip()
    diff_ordered_tacacs = dedent(
        """
        aaa group server tacacs+ group_name
         undo server 10.1.0.2 vrf MGMT
         undo server 10.1.0.4 vrf MGMT
         undo server 10.1.0.3 vrf MGMT
         server 10.1.0.4 vrf MGMT
         server 10.1.0.3 vrf MGMT
         server 10.1.0.7 vrf MGMT
        #
        section 1
         sub-section 2
          sub-line 2.3
        #
        some config
        #
        """
    ).strip()
    diff_ordered_tacacs_and_section = dedent(
        """
        section 1
         undo sub-line 1.2
         undo sub-line 1.3
         sub-section 2
          sub-line 2.3
         sub-line 1.2
         sub-line 1.3
        #
        aaa group server tacacs+ group_name
         undo server 10.1.0.2 vrf MGMT
         undo server 10.1.0.4 vrf MGMT
         undo server 10.1.0.3 vrf MGMT
         server 10.1.0.4 vrf MGMT
         server 10.1.0.3 vrf MGMT
         server 10.1.0.7 vrf MGMT
        #
        some config
        #
        """
    ).strip()
    diff_ordered_subsection = dedent(
        """
        section 1
         sub-section 2
          undo sub-line 2.2
          sub-line 2.2
          sub-line 2.3
        #
        aaa group server tacacs+ group_name
         undo server 10.1.0.2 vrf MGMT
         server 10.1.0.7 vrf MGMT
        #
        some config
        #
        """
    ).strip()
    diff_ordered_root = dedent(
        """
        aaa group server tacacs+ group_name
         undo server 10.1.0.2 vrf MGMT
         undo server 10.1.0.4 vrf MGMT
         undo server 10.1.0.3 vrf MGMT
         server 10.1.0.4 vrf MGMT
         server 10.1.0.3 vrf MGMT
         server 10.1.0.7 vrf MGMT
        #
        section 1
         sub-line 1.1
         sub-section 2
          sub-line 2.1
          sub-line 2.2
          sub-line 2.3
         sub-line 1.2
         sub-line 1.3
        #
        some config
        #
        undo section 1
        #
        """
    ).strip()
    diff_ordered_root_wo_reorder = dedent(
        """
        undo section 1
        #
        aaa group server tacacs+ group_name
         undo server 10.1.0.2 vrf MGMT
         undo server 10.1.0.4 vrf MGMT
         undo server 10.1.0.3 vrf MGMT
         server 10.1.0.4 vrf MGMT
         server 10.1.0.3 vrf MGMT
         server 10.1.0.7 vrf MGMT
        #
        section 1
         sub-line 1.1
         sub-section 2
          sub-line 2.1
          sub-line 2.2
          sub-line 2.3
         sub-line 1.2
         sub-line 1.3
        #
        some config
        #
        """
    ).strip()

    parser = ConfTreeParser(Vendor.HUAWEI)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff = ConfTreeDiffer.diff(current, target)
    assert diff.config == diff_default

    diff = ConfTreeDiffer.diff(
        current,
        target,
        ordered_sections=[r"^aaa group server tacacs\+"],
    )
    assert diff.config == diff_ordered_tacacs

    diff = ConfTreeDiffer.diff(
        current,
        target,
        ordered_sections=[r"^aaa group server tacacs\+", r"^section \d+$"],
    )
    assert diff.config == diff_ordered_tacacs_and_section

    diff = ConfTreeDiffer.diff(
        current,
        target,
        ordered_sections=[r"^section \d+ / sub-section \d+$"],
    )
    assert diff.config == diff_ordered_subsection

    diff = ConfTreeDiffer.diff(
        current,
        target,
        ordered_sections=[r".*"],
    )
    assert diff.config == diff_ordered_root

    diff = ConfTreeDiffer.diff(
        current,
        target,
        ordered_sections=[r".*"],
        reorder_root=False,
    )
    assert diff.config == diff_ordered_root_wo_reorder


def test_no_diff_sections() -> None:
    current_config = dedent(
        """
        interface Vbdif1234
         mtu 9000
         ip binding vpn-instance INTERNET
         ip address 1.2.3.4 255.255.255.0
        #
        route-policy RP_LEGACY_POLICY permit node 10
         if-match ip-prefix PL_PREFIX_LIST_NAME_OLD
        #
        xpl route-filter RP_XPL_POLICY
         if community matches-any CL_COMMUNITY_LIST_1 and community matches-any CL_COMMUNITY_LIST_2 then
          apply local-preference 150
          approve
         elseif community matches-any CL_COMMUNITY_LIST_OLD then
          approve
         endif
         end-filter
        #
        xpl route-filter RP_XPL_BLOCK
         refuse
         end-filter
        #
        """
    ).strip()
    target_config = dedent(
        """
        interface Vbdif1234
         mtu 9000
         description some svi
         ip binding vpn-instance INTERNET
         ip address 4.3.2.1 255.255.255.0
        #
        route-policy RP_LEGACY_POLICY permit node 10
         if-match ip-prefix PL_PREFIX_LIST_NAME_NEW
        #
        xpl route-filter RP_XPL_POLICY
         if community matches-any CL_COMMUNITY_LIST_1 and community matches-any CL_COMMUNITY_LIST_2 then
          apply local-preference 150
          approve
         elseif community matches-any CL_COMMUNITY_LIST_NEW then
          approve
         endif
         end-filter
        #
        route-policy RP_LEGACY_BLOCK deny node 10
        #
        xpl route-filter RP_XPL_BLOCK
         refuse
         end-filter
        #
        """
    ).strip()
    diff_raw_config = dedent(
        """
        interface Vbdif1234
         undo ip address 1.2.3.4 255.255.255.0
         description some svi
         ip address 4.3.2.1 255.255.255.0
        #
        route-policy RP_LEGACY_POLICY permit node 10
         undo if-match ip-prefix PL_PREFIX_LIST_NAME_OLD
         if-match ip-prefix PL_PREFIX_LIST_NAME_NEW
        #
        xpl route-filter RP_XPL_POLICY
         undo elseif community matches-any CL_COMMUNITY_LIST_OLD then
         elseif community matches-any CL_COMMUNITY_LIST_NEW then
          approve
        #
        route-policy RP_LEGACY_BLOCK deny node 10
        #
        """
    ).strip()
    diff_raw_patch = dedent(
        """
        interface Vbdif1234
        undo ip address 1.2.3.4 255.255.255.0
        description some svi
        ip address 4.3.2.1 255.255.255.0
        quit
        route-policy RP_LEGACY_POLICY permit node 10
        undo if-match ip-prefix PL_PREFIX_LIST_NAME_OLD
        if-match ip-prefix PL_PREFIX_LIST_NAME_NEW
        quit
        xpl route-filter RP_XPL_POLICY
        undo elseif community matches-any CL_COMMUNITY_LIST_OLD then
        elseif community matches-any CL_COMMUNITY_LIST_NEW then
        approve
        route-policy RP_LEGACY_BLOCK deny node 10
        quit
        """
    ).strip()
    diff_raw_empty_section_patch = dedent(
        """
        interface Vbdif1234
        undo ip address 1.2.3.4 255.255.255.0
        description some svi
        ip address 4.3.2.1 255.255.255.0
        quit
        route-policy RP_LEGACY_POLICY permit node 10
        undo if-match ip-prefix PL_PREFIX_LIST_NAME_OLD
        if-match ip-prefix PL_PREFIX_LIST_NAME_NEW
        quit
        xpl route-filter RP_XPL_POLICY
        undo elseif community matches-any CL_COMMUNITY_LIST_OLD then
        elseif community matches-any CL_COMMUNITY_LIST_NEW then
        approve
        route-policy RP_LEGACY_BLOCK deny node 10
        quit
        """
    ).strip()
    diff_no_diff_config = dedent(
        """
        interface Vbdif1234
         undo ip address 1.2.3.4 255.255.255.0
         description some svi
         ip address 4.3.2.1 255.255.255.0
        #
        route-policy RP_LEGACY_POLICY permit node 10
         undo if-match ip-prefix PL_PREFIX_LIST_NAME_OLD
         if-match ip-prefix PL_PREFIX_LIST_NAME_NEW
        #
        xpl route-filter RP_XPL_POLICY
         if community matches-any CL_COMMUNITY_LIST_1 and community matches-any CL_COMMUNITY_LIST_2 then
          apply local-preference 150
          approve
         elseif community matches-any CL_COMMUNITY_LIST_NEW then
          approve
         endif
         end-filter
        #
        route-policy RP_LEGACY_BLOCK deny node 10
        #
        """
    ).strip()
    diff_no_diff_patch = dedent(
        """
        interface Vbdif1234
        undo ip address 1.2.3.4 255.255.255.0
        description some svi
        ip address 4.3.2.1 255.255.255.0
        quit
        route-policy RP_LEGACY_POLICY permit node 10
        undo if-match ip-prefix PL_PREFIX_LIST_NAME_OLD
        if-match ip-prefix PL_PREFIX_LIST_NAME_NEW
        quit
        xpl route-filter RP_XPL_POLICY
        if community matches-any CL_COMMUNITY_LIST_1 and community matches-any CL_COMMUNITY_LIST_2 then
        apply local-preference 150
        approve
        elseif community matches-any CL_COMMUNITY_LIST_NEW then
        approve
        endif
        end-filter
        route-policy RP_LEGACY_BLOCK deny node 10
        quit
        """
    ).strip()

    parser = ConfTreeParser(Vendor.HUAWEI)
    target = parser.parse(target_config)
    current = parser.parse(current_config)

    diff_raw = ConfTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_raw_config
    assert diff_raw.patch == diff_raw_patch

    diff_raw_empty_section = ConfTreeDiffer.diff(current, target)
    assert diff_raw_empty_section.patch == diff_raw_empty_section_patch

    diff_no_diff = ConfTreeDiffer.diff(
        a=current,
        b=target,
        no_diff_sections=[r"^xpl \S+ \S+$"],
    )
    assert diff_no_diff.config == diff_no_diff_config
    assert diff_no_diff.patch == diff_no_diff_patch
