from textwrap import dedent

import pytest

from conf_tree import ConfTree, ConfTreeParser, ConfTreeSearcher, ConfTreeSerializer, TaggingRulesDict, Vendor

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
def get_config_tree() -> ConfTree:
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
    parser = ConfTreeParser(vendor=Vendor.HUAWEI, tagging_rules=loader)
    root = parser.parse(config)
    return root


def test_string(get_config_tree: ConfTree) -> None:
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
    filtered_root = ConfTreeSearcher.search(root, string="ip address 1.1.1.1 255.255.255.252")
    assert filtered_root.config == filtered_config
    assert ConfTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_regex(get_config_tree: ConfTree) -> None:
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
    filtered_root = ConfTreeSearcher.search(root, string=r"(?:\d+\.){3}\d+")
    assert filtered_root.config == filtered_config
    assert ConfTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_tag(get_config_tree: ConfTree) -> None:
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
    filtered_root = ConfTreeSearcher.search(root, include_tags=["vpn"])
    assert filtered_root.config == filtered_config
    assert ConfTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_tags_or(get_config_tree: ConfTree) -> None:
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
    filtered_root = ConfTreeSearcher.search(root, include_tags=["vpn", "LAN", "MGMT"], include_mode="or")
    assert filtered_root.config == filtered_config
    assert ConfTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_tags_and(get_config_tree: ConfTree) -> None:
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
    filtered_root = ConfTreeSearcher.search(root, include_tags=["rd", "LAN"], include_mode="and")
    assert filtered_root.config == filtered_config
    assert ConfTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_tags_exclude(get_config_tree: ConfTree) -> None:
    filtered_config = dedent(
        """
        ip vpn-instance MGMT
         ipv4-family
        #
        """
    ).strip()

    root = get_config_tree
    filtered_root = ConfTreeSearcher.search(root, include_tags=["vpn"], exclude_tags=["LAN"])
    assert filtered_root.config == filtered_config


def test_string_tags_and(get_config_tree: ConfTree) -> None:
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
    filtered_root = ConfTreeSearcher.search(
        root, string="ip address", include_tags=["gi0/0/0", "ip"], include_mode="and"
    )
    assert filtered_root.config == filtered_config
    assert ConfTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_string_tags_or(get_config_tree: ConfTree) -> None:
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
    filtered_root = ConfTreeSearcher.search(
        root, string=r"(?:\d+\.){3}\d+", include_tags=["gi0/0/0", "gi0/0/1"], include_mode="or"
    )
    assert filtered_root.config == filtered_config
    assert ConfTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_null_tags(get_config_tree: ConfTree) -> None:
    filtered_config = ""
    filtered_dict = {"line": "", "tags": [], "children": {}}
    root = get_config_tree
    filtered_root = ConfTreeSearcher.search(root, include_tags=["gi0/0/0", "gi0/0/1"], include_mode="and")
    assert filtered_root.config == filtered_config
    assert ConfTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_null_string(get_config_tree: ConfTree) -> None:
    filtered_config = ""
    filtered_dict = {"line": "", "tags": [], "children": {}}
    root = get_config_tree
    filtered_root = ConfTreeSearcher.search(root, string="unknown")
    assert filtered_root.config == filtered_config
    assert ConfTreeSerializer.to_dict(filtered_root) == filtered_dict


def test_null_empty(get_config_tree: ConfTree) -> None:
    root = get_config_tree
    filtered_root = ConfTreeSearcher.search(root)
    assert filtered_root == root.__class__()
