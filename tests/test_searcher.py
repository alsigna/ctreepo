from textwrap import dedent

import pytest

from ctreepo import CTree, CTreeParser, CTreeSearcher, CTreeSerializer, TaggingRulesDict, Vendor

config = dedent(
    """
    sflow collector 1 ip 100.64.0.1 vpn-instance MGMT
    #
    storm suppression statistics enable
    #
    ip vpn-instance MGMT
     ipv4-family
      route-distinguisher 192.168.0.1:123
    #
    ip vpn-instance LAN
     ipv4-family
      route-distinguisher 192.168.0.1:123
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
    ntp-service authentication-keyid 1 authentication-mode md5 cipher secret_password
    #
    radius-server template RADIUS_TEMPLATE
     radius-server shared-key cipher secret_password
     radius-server algorithm loading-share
    #
    """
).strip()


@pytest.fixture(scope="session")
def get_config_tree() -> CTree:
    tagging_rules_dict: dict[Vendor, list[dict[str, str | list[str]]]] = {
        Vendor.HUAWEI: [
            {"regex": r"^ip vpn-instance (\S+)$", "tags": ["vpn"]},
            {"regex": r"^ip vpn-instance (\S+) .* export-extcommunity evpn", "tags": ["rt"]},
            {"regex": r"^interface (\S+)$", "tags": ["interface"]},
            {"regex": r"^interface (gi0/0/0) .* ip address \S+ \S+$", "tags": ["ip", "interface-1"]},
            {"regex": r"^interface (gi0/0/1) .* ip address \S+ \S+$", "tags": ["ip", "interface-2"]},
            {"regex": r"^ip vpn-instance (\S+) .* route-distinguisher (\S+)", "tags": ["rd"]},
        ],
    }
    loader = TaggingRulesDict(tagging_rules_dict)
    parser = CTreeParser(vendor=Vendor.HUAWEI, tagging_rules=loader)
    root = parser.parse(config)
    return root


def test_string(get_config_tree: CTree) -> None:
    filtered_config = dedent(
        """
        interface gi0/0/0
         ip address 1.1.1.1 255.255.255.252
        #
        interface gi0/0/1
         ip address 1.1.1.1 255.255.255.252
        #
        """
    ).strip()
    filtered_dict = {
        "line": "",
        "tags": [],
        "children": {
            "interface gi0/0/0": {
                "line": "interface gi0/0/0",
                "tags": ["interface", "gi0/0/0"],
                "children": {
                    "ip address 1.1.1.1 255.255.255.252": {
                        "line": "ip address 1.1.1.1 255.255.255.252",
                        "tags": ["ip", "interface-1", "gi0/0/0"],
                        "children": {},
                    }
                },
            },
            "interface gi0/0/1": {
                "line": "interface gi0/0/1",
                "tags": ["interface", "gi0/0/1"],
                "children": {
                    "ip address 1.1.1.1 255.255.255.252": {
                        "line": "ip address 1.1.1.1 255.255.255.252",
                        "tags": ["ip", "interface-2", "gi0/0/1"],
                        "children": {},
                    }
                },
            },
        },
    }
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, string="ip address 1.1.1.1 255.255.255.252")
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_regex(get_config_tree: CTree) -> None:
    filtered_config = dedent(
        """
        sflow collector 1 ip 100.64.0.1 vpn-instance MGMT
        #
        ip vpn-instance MGMT
         ipv4-family
          route-distinguisher 192.168.0.1:123
        #
        ip vpn-instance LAN
         ipv4-family
          route-distinguisher 192.168.0.1:123
        #
        interface gi0/0/0
         ip address 1.1.1.1 255.255.255.252
        #
        interface gi0/0/1
         ip address 1.1.1.1 255.255.255.252
        #
        """
    ).strip()
    filtered_dict = {
        "line": "",
        "tags": [],
        "children": {
            "sflow collector 1 ip 100.64.0.1 vpn-instance MGMT": {
                "line": "sflow collector 1 ip 100.64.0.1 vpn-instance MGMT",
                "tags": [],
                "children": {},
            },
            "ip vpn-instance MGMT": {
                "line": "ip vpn-instance MGMT",
                "tags": ["vpn", "MGMT"],
                "children": {
                    "ipv4-family": {
                        "line": "ipv4-family",
                        "tags": ["vpn", "MGMT"],
                        "children": {
                            "route-distinguisher 192.168.0.1:123": {
                                "line": "route-distinguisher 192.168.0.1:123",
                                "tags": ["rd", "MGMT", "192.168.0.1:123"],
                                "children": {},
                            }
                        },
                    }
                },
            },
            "ip vpn-instance LAN": {
                "line": "ip vpn-instance LAN",
                "tags": ["vpn", "LAN"],
                "children": {
                    "ipv4-family": {
                        "line": "ipv4-family",
                        "tags": ["vpn", "LAN"],
                        "children": {
                            "route-distinguisher 192.168.0.1:123": {
                                "line": "route-distinguisher 192.168.0.1:123",
                                "tags": ["rd", "LAN", "192.168.0.1:123"],
                                "children": {},
                            }
                        },
                    }
                },
            },
            "interface gi0/0/0": {
                "line": "interface gi0/0/0",
                "tags": ["interface", "gi0/0/0"],
                "children": {
                    "ip address 1.1.1.1 255.255.255.252": {
                        "line": "ip address 1.1.1.1 255.255.255.252",
                        "tags": ["ip", "interface-1", "gi0/0/0"],
                        "children": {},
                    }
                },
            },
            "interface gi0/0/1": {
                "line": "interface gi0/0/1",
                "tags": ["interface", "gi0/0/1"],
                "children": {
                    "ip address 1.1.1.1 255.255.255.252": {
                        "line": "ip address 1.1.1.1 255.255.255.252",
                        "tags": ["ip", "interface-2", "gi0/0/1"],
                        "children": {},
                    }
                },
            },
        },
    }
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, string=r"(?:\d+\.){3}\d+")
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_tag(get_config_tree: CTree) -> None:
    filtered_config = dedent(
        """
        ip vpn-instance MGMT
         ipv4-family
        #
        ip vpn-instance LAN
         ipv4-family
          vpn-target 123:123 import-extcommunity evpn
         vxlan vni 123
        #
        """
    ).strip()
    filtered_dict = {
        "line": "",
        "tags": [],
        "children": {
            "ip vpn-instance MGMT": {
                "line": "ip vpn-instance MGMT",
                "tags": ["vpn", "MGMT"],
                "children": {
                    "ipv4-family": {
                        "line": "ipv4-family",
                        "tags": ["vpn", "MGMT"],
                        "children": {},
                    }
                },
            },
            "ip vpn-instance LAN": {
                "line": "ip vpn-instance LAN",
                "tags": ["vpn", "LAN"],
                "children": {
                    "ipv4-family": {
                        "line": "ipv4-family",
                        "tags": ["vpn", "LAN"],
                        "children": {
                            "vpn-target 123:123 import-extcommunity evpn": {
                                "line": "vpn-target 123:123 import-extcommunity evpn",
                                "tags": ["vpn", "LAN"],
                                "children": {},
                            },
                        },
                    },
                    "vxlan vni 123": {
                        "line": "vxlan vni 123",
                        "tags": ["vpn", "LAN"],
                        "children": {},
                    },
                },
            },
        },
    }
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, include_tags=["vpn"])
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_tags_or(get_config_tree: CTree) -> None:
    filtered_config = dedent(
        """
        ip vpn-instance MGMT
         ipv4-family
          route-distinguisher 192.168.0.1:123
        #
        ip vpn-instance LAN
         ipv4-family
          route-distinguisher 192.168.0.1:123
          vpn-target 123:123 export-extcommunity evpn
          vpn-target 123:123 import-extcommunity evpn
         vxlan vni 123
        #
        """
    ).strip()
    filtered_dict = {
        "line": "",
        "tags": [],
        "children": {
            "ip vpn-instance MGMT": {
                "line": "ip vpn-instance MGMT",
                "tags": ["vpn", "MGMT"],
                "children": {
                    "ipv4-family": {
                        "line": "ipv4-family",
                        "tags": ["vpn", "MGMT"],
                        "children": {
                            "route-distinguisher 192.168.0.1:123": {
                                "line": "route-distinguisher 192.168.0.1:123",
                                "tags": ["rd", "MGMT", "192.168.0.1:123"],
                                "children": {},
                            }
                        },
                    }
                },
            },
            "ip vpn-instance LAN": {
                "line": "ip vpn-instance LAN",
                "tags": ["vpn", "LAN"],
                "children": {
                    "ipv4-family": {
                        "line": "ipv4-family",
                        "tags": ["vpn", "LAN"],
                        "children": {
                            "route-distinguisher 192.168.0.1:123": {
                                "children": {},
                                "line": "route-distinguisher 192.168.0.1:123",
                                "tags": ["rd", "LAN", "192.168.0.1:123"],
                            },
                            "vpn-target 123:123 export-extcommunity evpn": {
                                "children": {},
                                "line": "vpn-target 123:123 export-extcommunity evpn",
                                "tags": ["rt", "LAN"],
                            },
                            "vpn-target 123:123 import-extcommunity evpn": {
                                "line": "vpn-target 123:123 import-extcommunity evpn",
                                "tags": ["vpn", "LAN"],
                                "children": {},
                            },
                        },
                    },
                    "vxlan vni 123": {
                        "line": "vxlan vni 123",
                        "tags": ["vpn", "LAN"],
                        "children": {},
                    },
                },
            },
        },
    }
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, include_tags=["vpn", "LAN", "MGMT"], include_mode="or")
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_tags_and(get_config_tree: CTree) -> None:
    filtered_config = dedent(
        """
        ip vpn-instance LAN
         ipv4-family
          route-distinguisher 192.168.0.1:123
        #
        """
    ).strip()
    filtered_dict = {
        "line": "",
        "tags": [],
        "children": {
            "ip vpn-instance LAN": {
                "line": "ip vpn-instance LAN",
                "tags": ["vpn", "LAN"],
                "children": {
                    "ipv4-family": {
                        "line": "ipv4-family",
                        "tags": ["vpn", "LAN"],
                        "children": {
                            "route-distinguisher 192.168.0.1:123": {
                                "children": {},
                                "line": "route-distinguisher 192.168.0.1:123",
                                "tags": ["rd", "LAN", "192.168.0.1:123"],
                            },
                        },
                    },
                },
            },
        },
    }
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, include_tags=["rd", "LAN"], include_mode="and")
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_tags_exclude(get_config_tree: CTree) -> None:
    filtered_config = dedent(
        """
        ip vpn-instance MGMT
         ipv4-family
        #
        """
    ).strip()

    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, include_tags=["vpn"], exclude_tags=["LAN"])
    assert filtered_root.config == filtered_config


def test_string_tags_and(get_config_tree: CTree) -> None:
    filtered_config = dedent(
        """
        interface gi0/0/0
         ip address 1.1.1.1 255.255.255.252
        #
        """
    ).strip()
    filtered_dict = {
        "line": "",
        "tags": [],
        "children": {
            "interface gi0/0/0": {
                "line": "interface gi0/0/0",
                "tags": ["interface", "gi0/0/0"],
                "children": {
                    "ip address 1.1.1.1 255.255.255.252": {
                        "line": "ip address 1.1.1.1 255.255.255.252",
                        "tags": ["ip", "interface-1", "gi0/0/0"],
                        "children": {},
                    }
                },
            },
        },
    }
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, string="ip address", include_tags=["gi0/0/0", "ip"], include_mode="and")
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_string_tags_or(get_config_tree: CTree) -> None:
    filtered_config = dedent(
        """
        interface gi0/0/0
         ip address 1.1.1.1 255.255.255.252
        #
        interface gi0/0/1
         ip address 1.1.1.1 255.255.255.252
        #
        """
    ).strip()
    filtered_dict = {
        "line": "",
        "tags": [],
        "children": {
            "interface gi0/0/0": {
                "line": "interface gi0/0/0",
                "tags": ["interface", "gi0/0/0"],
                "children": {
                    "ip address 1.1.1.1 255.255.255.252": {
                        "line": "ip address 1.1.1.1 255.255.255.252",
                        "tags": ["ip", "interface-1", "gi0/0/0"],
                        "children": {},
                    }
                },
            },
            "interface gi0/0/1": {
                "children": {
                    "ip address 1.1.1.1 255.255.255.252": {
                        "children": {},
                        "line": "ip address 1.1.1.1 255.255.255.252",
                        "tags": ["ip", "interface-2", "gi0/0/1"],
                    },
                },
                "line": "interface gi0/0/1",
                "tags": ["interface", "gi0/0/1"],
            },
        },
    }
    root = get_config_tree
    filtered_root = CTreeSearcher.search(
        root, string=r"(?:\d+\.){3}\d+", include_tags=["gi0/0/0", "gi0/0/1"], include_mode="or"
    )
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_null_tags(get_config_tree: CTree) -> None:
    filtered_config = ""
    filtered_dict = {"line": "", "tags": [], "children": {}}
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, include_tags=["gi0/0/0", "gi0/0/1"], include_mode="and")
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_null_string(get_config_tree: CTree) -> None:
    filtered_config = ""
    filtered_dict = {"line": "", "tags": [], "children": {}}
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root, string="unknown")
    assert filtered_root.config == filtered_config
    assert CTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_null_empty(get_config_tree: CTree) -> None:
    root = get_config_tree
    filtered_root = CTreeSearcher.search(root)
    assert filtered_root == root.__class__()


def test_children(get_config_tree: CTree) -> None:
    without_children_config = dedent(
        """
        ip vpn-instance MGMT
         ipv4-family
        #
        ip vpn-instance LAN
         ipv4-family
        #
        """
    ).strip()
    with_children_config = dedent(
        """
        ip vpn-instance MGMT
         ipv4-family
          route-distinguisher 192.168.0.1:123
        #
        ip vpn-instance LAN
         ipv4-family
          route-distinguisher 192.168.0.1:123
          vpn-target 123:123 export-extcommunity evpn
          vpn-target 123:123 import-extcommunity evpn
        #
        """
    ).strip()
    root = get_config_tree
    without_children = CTreeSearcher.search(ct=root, string="ipv4-family", include_children=False)
    with_children = CTreeSearcher.search(ct=root, string="ipv4-family", include_children=True)
    assert without_children.config == without_children_config
    assert with_children.config == with_children_config


def test_exclude_children_by_tag() -> None:
    config_str = dedent(
        """
        no platform punt-keepalive disable-kernel-core
        no service pad
        !
        router bgp 64512
         neighbor CSC peer-group
         neighbor CSC remote-as 12345
         !
         address-family ipv4
          neighbor CSC send-community both
          neighbor CSC route-map rm_CSC_PE_in in
         exit-address-family
        !
        """
    )
    bgp_all_str = dedent(
        """
        router bgp 64512
         neighbor CSC peer-group
         neighbor CSC remote-as 12345
         address-family ipv4
          neighbor CSC send-community both
          neighbor CSC route-map rm_CSC_PE_in in
        !
        """
    ).strip()
    bgp_rm_attach_str = dedent(
        """
        router bgp 64512
         address-family ipv4
          neighbor CSC route-map rm_CSC_PE_in in
        !
        """
    ).strip()
    bgp_no_rm_str = dedent(
        """
        router bgp 64512
         neighbor CSC peer-group
         neighbor CSC remote-as 12345
         address-family ipv4
          neighbor CSC send-community both
        !
        """
    ).strip()
    bgp_no_rm_exclude_str = dedent(
        """
        no platform punt-keepalive disable-kernel-core
        !
        no service pad
        !
        router bgp 64512
         neighbor CSC peer-group
         neighbor CSC remote-as 12345
         address-family ipv4
          neighbor CSC send-community both
        !
        """
    ).strip()
    tagging_rules: list[dict[str, str | list[str]]] = [
        {"regex": r"^router bgp .* neighbor (\S+) route-map (\S+) (?:in|out)", "tags": ["rm-attach"]},
        {"regex": r"^router bgp \d+$", "tags": ["bgp"]},
    ]
    parser = CTreeParser(Vendor.CISCO, TaggingRulesDict({Vendor.CISCO: tagging_rules}))
    root = parser.parse(config_str)

    # c "neighbor CSC route-map rm_CSC_PE_in in", встречаем bgp секцию и помещаем
    # этот узел в результат со всеми его потомками, без проверки на их теги
    bgp_all = CTreeSearcher.search(
        root,
        include_tags=["bgp"],
        include_children=True,
    )
    assert bgp_all.config == bgp_all_str

    # без "neighbor CSC route-map rm_CSC_PE_in in", а тут уже проверяем теги каждого
    # потомка, поэтому строка не попадает в результат
    bgp_no_rm = CTreeSearcher.search(
        root,
        include_tags=["bgp"],
    )
    assert bgp_no_rm.config == bgp_no_rm_str

    bgp_rm_attach = CTreeSearcher.search(
        root,
        include_tags=["rm-attach"],
    )
    assert bgp_rm_attach.config == bgp_rm_attach_str

    bgp_no_rm_exclude = CTreeSearcher.search(
        root,
        exclude_tags=["rm-attach"],
    )
    assert bgp_no_rm_exclude.config == bgp_no_rm_exclude_str
