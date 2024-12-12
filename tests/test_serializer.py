from textwrap import dedent

import pytest

from ctreepo import CTreeParser, CTreeSerializer, TaggingRules, TaggingRulesDict, Vendor

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

config_dict = {
    "line": "",
    "tags": [],
    "children": {
        "sflow collector 1 ip 100.64.0.1 vpn-instance MGMT": {
            "line": "sflow collector 1 ip 100.64.0.1 vpn-instance MGMT",
            "tags": [],
            "children": {},
        },
        "storm suppression statistics enable": {
            "line": "storm suppression statistics enable",
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
                            "tags": ["vpn", "MGMT"],
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
                        },
                        "vpn-target 123:123 export-extcommunity evpn": {
                            "line": "vpn-target 123:123 export-extcommunity evpn",
                            "tags": ["rt", "LAN"],
                            "children": {},
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
        "ntp-service authentication-keyid 1 authentication-mode md5 cipher secret_password": {
            "line": "ntp-service authentication-keyid 1 authentication-mode md5 cipher secret_password",
            "tags": [],
            "children": {},
        },
        "radius-server template RADIUS_TEMPLATE": {
            "line": "radius-server template RADIUS_TEMPLATE",
            "tags": [],
            "children": {
                "radius-server shared-key cipher secret_password": {
                    "line": "radius-server shared-key cipher secret_password",
                    "tags": [],
                    "children": {},
                },
                "radius-server algorithm loading-share": {
                    "line": "radius-server algorithm loading-share",
                    "tags": [],
                    "children": {},
                },
            },
        },
    },
}


@pytest.fixture(scope="session")
def get_dict_loader() -> TaggingRules:
    tagging_rules_dict: dict[Vendor, list[dict[str, str | list[str]]]] = {
        Vendor.HUAWEI: [
            {"regex": r"^ip vpn-instance (\S+)$", "tags": ["vpn"]},
            {"regex": r"^ip vpn-instance (\S+) .* export-extcommunity evpn", "tags": ["rt"]},
            {"regex": r"^interface (\S+)$", "tags": ["interface"]},
            {"regex": r"^interface (gi0/0/0) .* ip address \S+ \S+$", "tags": ["ip", "interface-1"]},
            {"regex": r"^interface (gi0/0/1) .* ip address \S+ \S+$", "tags": ["ip", "interface-2"]},
            {"regex": r"^ip vpn-instance (LAN) .* route-distinguisher (\S+)", "tags": ["rd"]},
        ],
    }
    loader = TaggingRulesDict(tagging_rules_dict)
    return loader


def test_to_dict(get_dict_loader: TaggingRules) -> None:
    parser = CTreeParser(vendor=Vendor.HUAWEI, tagging_rules=get_dict_loader)
    root = parser.parse(config)
    serialized_config = CTreeSerializer.to_dict(root)
    assert serialized_config == config_dict


def test_from_dict(get_dict_loader: TaggingRules) -> None:
    parser = CTreeParser(vendor=Vendor.HUAWEI, tagging_rules=get_dict_loader)
    root_from_config = parser.parse(config)

    root_from_dict = CTreeSerializer.from_dict(Vendor.HUAWEI, config_dict)
    assert root_from_config == root_from_dict
