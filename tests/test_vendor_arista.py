from textwrap import dedent
from typing import cast

import pytest

from ctreepo import AristaCT, CTree, CTreeParser, CTreeSearcher, CTreeSerializer, TaggingRulesDict, Vendor


@pytest.fixture(scope="function")
def root() -> AristaCT:
    config_str = dedent(
        """
        logging buffered 16000
        logging vrf MGMT host 4.3.2.1 514
        logging format hostname fqdn
        !
        hostname arista-switch
        !
        interface Ethernet1
           switchport trunk native vlan 123
           switchport mode trunk
           qos trust dscp
           !
           tx-queue 0
              no priority
              bandwidth percent 10
           !
           tx-queue 1
              no priority
              bandwidth percent 20
           !
           tx-queue 2
              no priority
              bandwidth percent 30
           !
           tx-queue 3
              no priority
              bandwidth percent 40
           !
           tx-queue 4
              no priority
              bandwidth percent 50
           !
           tx-queue 5
              shape rate 60 percent
           !
           tx-queue 6
              shape rate 70 percent
           sflow enable
           storm-control broadcast level 0.1
           storm-control multicast level 0.1
           spanning-tree portfast
           spanning-tree bpduguard enable
        !
        route-map RM_LOOPBACKS permit 10
           match ip address prefix-list PL_LOOPBACKS
        !
        route-map RM_DENY deny 10
        !
        ntp authentication-key 1 md5 7 ntp-secret-key
        !
        tacacs-server 1.2.3.4 vrf MGMT key 7 tacacs-secret-key
        !
        enable password sha512 enable-secret-key
        !
        username admin privilege 15 role network-admin secret sha512 admin-secret-key
        !
        qos map traffic-class 0 to cos 0
        qos map traffic-class 1 to cos 1
        management ssh
           idle-timeout 30
           shutdown
           !
           vrf MGMT
              no shutdown
        !
        end
        """
    )
    tagging_rules_dict = {
        Vendor.ARISTA: [
            {"regex": r"^interface (\S+)$", "tags": ["interface"]},
            {"regex": r"^qos .*", "tags": ["qos"]},
            {"regex": r"^management ssh$", "tags": ["mgmt"]},
            {"regex": r"^(ntp) .*", "tags": ["mgmt"]},
            {"regex": r"^(logging) .*", "tags": ["mgmt"]},
            {"regex": r"^username (\S+) .*", "tags": ["mgmt", "user"]},
            {"regex": r"^enable password .*", "tags": ["mgmt"]},
            {"regex": r"^route-map (\S+) \d+", "tags": ["mgmt"]},
            {"regex": r"^interface (\S+) / qos .*", "tags": ["interface", "qos"]},
            {"regex": r"^interface (\S+) / tx-queue \d+$", "tags": ["interface", "qos"]},
        ],
    }
    loader = TaggingRulesDict(tagging_rules_dict)  # type: ignore[arg-type]
    parser = CTreeParser(
        vendor=Vendor.ARISTA,
        tagging_rules=loader,
    )
    root: CTree = parser.parse(config_str)
    root = cast(AristaCT, root)
    return root


def test_config(root: AristaCT) -> None:
    config = dedent(
        """
        logging buffered 16000
        !
        logging vrf MGMT host 4.3.2.1 514
        !
        logging format hostname fqdn
        !
        hostname arista-switch
        !
        interface Ethernet1
           switchport trunk native vlan 123
           switchport mode trunk
           qos trust dscp
           tx-queue 0
              no priority
              bandwidth percent 10
           tx-queue 1
              no priority
              bandwidth percent 20
           tx-queue 2
              no priority
              bandwidth percent 30
           tx-queue 3
              no priority
              bandwidth percent 40
           tx-queue 4
              no priority
              bandwidth percent 50
           tx-queue 5
              shape rate 60 percent
           tx-queue 6
              shape rate 70 percent
           sflow enable
           storm-control broadcast level 0.1
           storm-control multicast level 0.1
           spanning-tree portfast
           spanning-tree bpduguard enable
        !
        route-map RM_LOOPBACKS permit 10
           match ip address prefix-list PL_LOOPBACKS
        !
        route-map RM_DENY deny 10
        !
        ntp authentication-key 1 md5 7 ntp-secret-key
        !
        tacacs-server 1.2.3.4 vrf MGMT key 7 tacacs-secret-key
        !
        enable password sha512 enable-secret-key
        !
        username admin privilege 15 role network-admin secret sha512 admin-secret-key
        !
        qos map traffic-class 0 to cos 0
        !
        qos map traffic-class 1 to cos 1
        !
        management ssh
           idle-timeout 30
           shutdown
           vrf MGMT
              no shutdown
        !
        """
    ).strip()
    assert root.config == config


def test_patch(root: AristaCT) -> None:
    patch = dedent(
        """
        logging buffered 16000
        logging vrf MGMT host 4.3.2.1 514
        logging format hostname fqdn
        hostname arista-switch
        interface Ethernet1
        switchport trunk native vlan 123
        switchport mode trunk
        qos trust dscp
        tx-queue 0
        no priority
        bandwidth percent 10
        exit
        tx-queue 1
        no priority
        bandwidth percent 20
        exit
        tx-queue 2
        no priority
        bandwidth percent 30
        exit
        tx-queue 3
        no priority
        bandwidth percent 40
        exit
        tx-queue 4
        no priority
        bandwidth percent 50
        exit
        tx-queue 5
        shape rate 60 percent
        exit
        tx-queue 6
        shape rate 70 percent
        exit
        sflow enable
        storm-control broadcast level 0.1
        storm-control multicast level 0.1
        spanning-tree portfast
        spanning-tree bpduguard enable
        exit
        route-map RM_LOOPBACKS permit 10
        match ip address prefix-list PL_LOOPBACKS
        exit
        route-map RM_DENY deny 10
        exit
        ntp authentication-key 1 md5 7 ntp-secret-key
        tacacs-server 1.2.3.4 vrf MGMT key 7 tacacs-secret-key
        enable password sha512 enable-secret-key
        username admin privilege 15 role network-admin secret sha512 admin-secret-key
        qos map traffic-class 0 to cos 0
        qos map traffic-class 1 to cos 1
        management ssh
        idle-timeout 30
        shutdown
        vrf MGMT
        no shutdown
        exit
        exit
        """
    ).strip()
    assert root.patch == patch


def test_to_dict(root: AristaCT) -> None:
    dst = {
        "line": "",
        "tags": [],
        "children": {
            "logging buffered 16000": {"line": "logging buffered 16000", "tags": ["mgmt", "logging"], "children": {}},
            "logging vrf MGMT host 4.3.2.1 514": {
                "line": "logging vrf MGMT host 4.3.2.1 514",
                "tags": ["mgmt", "logging"],
                "children": {},
            },
            "logging format hostname fqdn": {
                "line": "logging format hostname fqdn",
                "tags": ["mgmt", "logging"],
                "children": {},
            },
            "hostname arista-switch": {"line": "hostname arista-switch", "tags": [], "children": {}},
            "interface Ethernet1": {
                "line": "interface Ethernet1",
                "tags": ["interface", "Ethernet1"],
                "children": {
                    "switchport trunk native vlan 123": {
                        "line": "switchport trunk native vlan 123",
                        "tags": ["interface", "Ethernet1"],
                        "children": {},
                    },
                    "switchport mode trunk": {
                        "line": "switchport mode trunk",
                        "tags": ["interface", "Ethernet1"],
                        "children": {},
                    },
                    "qos trust dscp": {
                        "line": "qos trust dscp",
                        "tags": ["interface", "qos", "Ethernet1"],
                        "children": {},
                    },
                    "tx-queue 0": {
                        "line": "tx-queue 0",
                        "tags": ["interface", "qos", "Ethernet1"],
                        "children": {
                            "no priority": {
                                "line": "no priority",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                            "bandwidth percent 10": {
                                "line": "bandwidth percent 10",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                        },
                    },
                    "tx-queue 1": {
                        "line": "tx-queue 1",
                        "tags": ["interface", "qos", "Ethernet1"],
                        "children": {
                            "no priority": {
                                "line": "no priority",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                            "bandwidth percent 20": {
                                "line": "bandwidth percent 20",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                        },
                    },
                    "tx-queue 2": {
                        "line": "tx-queue 2",
                        "tags": ["interface", "qos", "Ethernet1"],
                        "children": {
                            "no priority": {
                                "line": "no priority",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                            "bandwidth percent 30": {
                                "line": "bandwidth percent 30",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                        },
                    },
                    "tx-queue 3": {
                        "line": "tx-queue 3",
                        "tags": ["interface", "qos", "Ethernet1"],
                        "children": {
                            "no priority": {
                                "line": "no priority",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                            "bandwidth percent 40": {
                                "line": "bandwidth percent 40",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                        },
                    },
                    "tx-queue 4": {
                        "line": "tx-queue 4",
                        "tags": ["interface", "qos", "Ethernet1"],
                        "children": {
                            "no priority": {
                                "line": "no priority",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                            "bandwidth percent 50": {
                                "line": "bandwidth percent 50",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                        },
                    },
                    "tx-queue 5": {
                        "line": "tx-queue 5",
                        "tags": ["interface", "qos", "Ethernet1"],
                        "children": {
                            "shape rate 60 percent": {
                                "line": "shape rate 60 percent",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            }
                        },
                    },
                    "tx-queue 6": {
                        "line": "tx-queue 6",
                        "tags": ["interface", "qos", "Ethernet1"],
                        "children": {
                            "shape rate 70 percent": {
                                "line": "shape rate 70 percent",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            }
                        },
                    },
                    "sflow enable": {"line": "sflow enable", "tags": ["interface", "Ethernet1"], "children": {}},
                    "storm-control broadcast level 0.1": {
                        "line": "storm-control broadcast level 0.1",
                        "tags": ["interface", "Ethernet1"],
                        "children": {},
                    },
                    "storm-control multicast level 0.1": {
                        "line": "storm-control multicast level 0.1",
                        "tags": ["interface", "Ethernet1"],
                        "children": {},
                    },
                    "spanning-tree portfast": {
                        "line": "spanning-tree portfast",
                        "tags": ["interface", "Ethernet1"],
                        "children": {},
                    },
                    "spanning-tree bpduguard enable": {
                        "line": "spanning-tree bpduguard enable",
                        "tags": ["interface", "Ethernet1"],
                        "children": {},
                    },
                },
            },
            "route-map RM_LOOPBACKS permit 10": {
                "line": "route-map RM_LOOPBACKS permit 10",
                "tags": [],
                "children": {
                    "match ip address prefix-list PL_LOOPBACKS": {
                        "line": "match ip address prefix-list PL_LOOPBACKS",
                        "tags": [],
                        "children": {},
                    }
                },
            },
            "route-map RM_DENY deny 10": {"line": "route-map RM_DENY deny 10", "tags": [], "children": {}},
            "ntp authentication-key 1 md5 7 ntp-secret-key": {
                "line": "ntp authentication-key 1 md5 7 ntp-secret-key",
                "tags": ["mgmt", "ntp"],
                "children": {},
            },
            "tacacs-server 1.2.3.4 vrf MGMT key 7 tacacs-secret-key": {
                "line": "tacacs-server 1.2.3.4 vrf MGMT key 7 tacacs-secret-key",
                "tags": [],
                "children": {},
            },
            "enable password sha512 enable-secret-key": {
                "line": "enable password sha512 enable-secret-key",
                "tags": ["mgmt"],
                "children": {},
            },
            "username admin privilege 15 role network-admin secret sha512 admin-secret-key": {
                "line": "username admin privilege 15 role network-admin secret sha512 admin-secret-key",
                "tags": ["mgmt", "user", "admin"],
                "children": {},
            },
            "qos map traffic-class 0 to cos 0": {
                "line": "qos map traffic-class 0 to cos 0",
                "tags": ["qos"],
                "children": {},
            },
            "qos map traffic-class 1 to cos 1": {
                "line": "qos map traffic-class 1 to cos 1",
                "tags": ["qos"],
                "children": {},
            },
            "management ssh": {
                "line": "management ssh",
                "tags": ["mgmt"],
                "children": {
                    "idle-timeout 30": {"line": "idle-timeout 30", "tags": ["mgmt"], "children": {}},
                    "shutdown": {"line": "shutdown", "tags": ["mgmt"], "children": {}},
                    "vrf MGMT": {
                        "line": "vrf MGMT",
                        "tags": ["mgmt"],
                        "children": {"no shutdown": {"line": "no shutdown", "tags": ["mgmt"], "children": {}}},
                    },
                },
            },
        },
    }
    serialized = CTreeSerializer.to_dict(root)
    assert dst == serialized


def test_from_dict(root: AristaCT) -> None:
    src = {
        "line": "",
        "tags": [],
        "children": {
            "logging buffered 16000": {"line": "logging buffered 16000", "tags": ["mgmt", "logging"], "children": {}},
            "logging vrf MGMT host 4.3.2.1 514": {
                "line": "logging vrf MGMT host 4.3.2.1 514",
                "tags": ["mgmt", "logging"],
                "children": {},
            },
            "logging format hostname fqdn": {
                "line": "logging format hostname fqdn",
                "tags": ["mgmt", "logging"],
                "children": {},
            },
            "hostname arista-switch": {"line": "hostname arista-switch", "tags": [], "children": {}},
            "interface Ethernet1": {
                "line": "interface Ethernet1",
                "tags": ["interface", "Ethernet1"],
                "children": {
                    "switchport trunk native vlan 123": {
                        "line": "switchport trunk native vlan 123",
                        "tags": ["interface", "Ethernet1"],
                        "children": {},
                    },
                    "switchport mode trunk": {
                        "line": "switchport mode trunk",
                        "tags": ["interface", "Ethernet1"],
                        "children": {},
                    },
                    "qos trust dscp": {
                        "line": "qos trust dscp",
                        "tags": ["interface", "qos", "Ethernet1"],
                        "children": {},
                    },
                    "tx-queue 0": {
                        "line": "tx-queue 0",
                        "tags": ["interface", "qos", "Ethernet1"],
                        "children": {
                            "no priority": {
                                "line": "no priority",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                            "bandwidth percent 10": {
                                "line": "bandwidth percent 10",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                        },
                    },
                    "tx-queue 1": {
                        "line": "tx-queue 1",
                        "tags": ["interface", "qos", "Ethernet1"],
                        "children": {
                            "no priority": {
                                "line": "no priority",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                            "bandwidth percent 20": {
                                "line": "bandwidth percent 20",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                        },
                    },
                    "tx-queue 2": {
                        "line": "tx-queue 2",
                        "tags": ["interface", "qos", "Ethernet1"],
                        "children": {
                            "no priority": {
                                "line": "no priority",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                            "bandwidth percent 30": {
                                "line": "bandwidth percent 30",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                        },
                    },
                    "tx-queue 3": {
                        "line": "tx-queue 3",
                        "tags": ["interface", "qos", "Ethernet1"],
                        "children": {
                            "no priority": {
                                "line": "no priority",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                            "bandwidth percent 40": {
                                "line": "bandwidth percent 40",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                        },
                    },
                    "tx-queue 4": {
                        "line": "tx-queue 4",
                        "tags": ["interface", "qos", "Ethernet1"],
                        "children": {
                            "no priority": {
                                "line": "no priority",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                            "bandwidth percent 50": {
                                "line": "bandwidth percent 50",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            },
                        },
                    },
                    "tx-queue 5": {
                        "line": "tx-queue 5",
                        "tags": ["interface", "qos", "Ethernet1"],
                        "children": {
                            "shape rate 60 percent": {
                                "line": "shape rate 60 percent",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            }
                        },
                    },
                    "tx-queue 6": {
                        "line": "tx-queue 6",
                        "tags": ["interface", "qos", "Ethernet1"],
                        "children": {
                            "shape rate 70 percent": {
                                "line": "shape rate 70 percent",
                                "tags": ["interface", "qos", "Ethernet1"],
                                "children": {},
                            }
                        },
                    },
                    "sflow enable": {"line": "sflow enable", "tags": ["interface", "Ethernet1"], "children": {}},
                    "storm-control broadcast level 0.1": {
                        "line": "storm-control broadcast level 0.1",
                        "tags": ["interface", "Ethernet1"],
                        "children": {},
                    },
                    "storm-control multicast level 0.1": {
                        "line": "storm-control multicast level 0.1",
                        "tags": ["interface", "Ethernet1"],
                        "children": {},
                    },
                    "spanning-tree portfast": {
                        "line": "spanning-tree portfast",
                        "tags": ["interface", "Ethernet1"],
                        "children": {},
                    },
                    "spanning-tree bpduguard enable": {
                        "line": "spanning-tree bpduguard enable",
                        "tags": ["interface", "Ethernet1"],
                        "children": {},
                    },
                },
            },
            "route-map RM_LOOPBACKS permit 10": {
                "line": "route-map RM_LOOPBACKS permit 10",
                "tags": [],
                "children": {
                    "match ip address prefix-list PL_LOOPBACKS": {
                        "line": "match ip address prefix-list PL_LOOPBACKS",
                        "tags": [],
                        "children": {},
                    }
                },
            },
            "route-map RM_DENY deny 10": {"line": "route-map RM_DENY deny 10", "tags": [], "children": {}},
            "ntp authentication-key 1 md5 7 ntp-secret-key": {
                "line": "ntp authentication-key 1 md5 7 ntp-secret-key",
                "tags": ["mgmt", "ntp"],
                "children": {},
            },
            "tacacs-server 1.2.3.4 vrf MGMT key 7 tacacs-secret-key": {
                "line": "tacacs-server 1.2.3.4 vrf MGMT key 7 tacacs-secret-key",
                "tags": [],
                "children": {},
            },
            "enable password sha512 enable-secret-key": {
                "line": "enable password sha512 enable-secret-key",
                "tags": ["mgmt"],
                "children": {},
            },
            "username admin privilege 15 role network-admin secret sha512 admin-secret-key": {
                "line": "username admin privilege 15 role network-admin secret sha512 admin-secret-key",
                "tags": ["mgmt", "user", "admin"],
                "children": {},
            },
            "qos map traffic-class 0 to cos 0": {
                "line": "qos map traffic-class 0 to cos 0",
                "tags": ["qos"],
                "children": {},
            },
            "qos map traffic-class 1 to cos 1": {
                "line": "qos map traffic-class 1 to cos 1",
                "tags": ["qos"],
                "children": {},
            },
            "management ssh": {
                "line": "management ssh",
                "tags": ["mgmt"],
                "children": {
                    "idle-timeout 30": {"line": "idle-timeout 30", "tags": ["mgmt"], "children": {}},
                    "shutdown": {"line": "shutdown", "tags": ["mgmt"], "children": {}},
                    "vrf MGMT": {
                        "line": "vrf MGMT",
                        "tags": ["mgmt"],
                        "children": {"no shutdown": {"line": "no shutdown", "tags": ["mgmt"], "children": {}}},
                    },
                },
            },
        },
    }
    deserialized = CTreeSerializer.from_dict(Vendor.ARISTA, src)
    assert root == deserialized

    src["children"]["logging buffered 16000"]["tags"].append("changed")  # type: ignore[index]
    deserialized = CTreeSerializer.from_dict(Vendor.ARISTA, src)
    assert root != deserialized


def test_masked_config(root: AristaCT) -> None:
    masked_config = dedent(
        f"""
        logging buffered 16000
        !
        logging vrf MGMT host 4.3.2.1 514
        !
        logging format hostname fqdn
        !
        hostname arista-switch
        !
        interface Ethernet1
           switchport trunk native vlan 123
           switchport mode trunk
           qos trust dscp
           tx-queue 0
              no priority
              bandwidth percent 10
           tx-queue 1
              no priority
              bandwidth percent 20
           tx-queue 2
              no priority
              bandwidth percent 30
           tx-queue 3
              no priority
              bandwidth percent 40
           tx-queue 4
              no priority
              bandwidth percent 50
           tx-queue 5
              shape rate 60 percent
           tx-queue 6
              shape rate 70 percent
           sflow enable
           storm-control broadcast level 0.1
           storm-control multicast level 0.1
           spanning-tree portfast
           spanning-tree bpduguard enable
        !
        route-map RM_LOOPBACKS permit 10
           match ip address prefix-list PL_LOOPBACKS
        !
        route-map RM_DENY deny 10
        !
        ntp authentication-key 1 md5 7 {AristaCT.masking_string}
        !
        tacacs-server 1.2.3.4 vrf MGMT key 7 {AristaCT.masking_string}
        !
        enable password sha512 {AristaCT.masking_string}
        !
        username admin privilege 15 role network-admin secret sha512 {AristaCT.masking_string}
        !
        qos map traffic-class 0 to cos 0
        !
        qos map traffic-class 1 to cos 1
        !
        management ssh
           idle-timeout 30
           shutdown
           vrf MGMT
              no shutdown
        !
        """
    ).strip()
    assert root.masked_config == masked_config


def test_masked_patch(root: AristaCT) -> None:
    masked_patch = dedent(
        f"""
        logging buffered 16000
        logging vrf MGMT host 4.3.2.1 514
        logging format hostname fqdn
        hostname arista-switch
        interface Ethernet1
        switchport trunk native vlan 123
        switchport mode trunk
        qos trust dscp
        tx-queue 0
        no priority
        bandwidth percent 10
        exit
        tx-queue 1
        no priority
        bandwidth percent 20
        exit
        tx-queue 2
        no priority
        bandwidth percent 30
        exit
        tx-queue 3
        no priority
        bandwidth percent 40
        exit
        tx-queue 4
        no priority
        bandwidth percent 50
        exit
        tx-queue 5
        shape rate 60 percent
        exit
        tx-queue 6
        shape rate 70 percent
        exit
        sflow enable
        storm-control broadcast level 0.1
        storm-control multicast level 0.1
        spanning-tree portfast
        spanning-tree bpduguard enable
        exit
        route-map RM_LOOPBACKS permit 10
        match ip address prefix-list PL_LOOPBACKS
        exit
        route-map RM_DENY deny 10
        exit
        ntp authentication-key 1 md5 7 {AristaCT.masking_string}
        tacacs-server 1.2.3.4 vrf MGMT key 7 {AristaCT.masking_string}
        enable password sha512 {AristaCT.masking_string}
        username admin privilege 15 role network-admin secret sha512 {AristaCT.masking_string}
        qos map traffic-class 0 to cos 0
        qos map traffic-class 1 to cos 1
        management ssh
        idle-timeout 30
        shutdown
        vrf MGMT
        no shutdown
        exit
        exit
        """
    ).strip()
    assert root.masked_patch == masked_patch


def test_searcher(root: AristaCT) -> None:
    qos_config = dedent(
        """
        interface Ethernet1
           qos trust dscp
           tx-queue 0
              no priority
              bandwidth percent 10
           tx-queue 1
              no priority
              bandwidth percent 20
           tx-queue 2
              no priority
              bandwidth percent 30
           tx-queue 3
              no priority
              bandwidth percent 40
           tx-queue 4
              no priority
              bandwidth percent 50
           tx-queue 5
              shape rate 60 percent
           tx-queue 6
              shape rate 70 percent
        !
        qos map traffic-class 0 to cos 0
        !
        qos map traffic-class 1 to cos 1
        !
        """
    ).strip()
    interface_or_qos_config = dedent(
        """
        interface Ethernet1
           switchport trunk native vlan 123
           switchport mode trunk
           qos trust dscp
           tx-queue 0
              no priority
              bandwidth percent 10
           tx-queue 1
              no priority
              bandwidth percent 20
           tx-queue 2
              no priority
              bandwidth percent 30
           tx-queue 3
              no priority
              bandwidth percent 40
           tx-queue 4
              no priority
              bandwidth percent 50
           tx-queue 5
              shape rate 60 percent
           tx-queue 6
              shape rate 70 percent
           sflow enable
           storm-control broadcast level 0.1
           storm-control multicast level 0.1
           spanning-tree portfast
           spanning-tree bpduguard enable
        !
        qos map traffic-class 0 to cos 0
        !
        qos map traffic-class 1 to cos 1
        !
        """
    ).strip()
    interface_and_qos_config = dedent(
        """
        interface Ethernet1
           qos trust dscp
           tx-queue 0
              no priority
              bandwidth percent 10
           tx-queue 1
              no priority
              bandwidth percent 20
           tx-queue 2
              no priority
              bandwidth percent 30
           tx-queue 3
              no priority
              bandwidth percent 40
           tx-queue 4
              no priority
              bandwidth percent 50
           tx-queue 5
              shape rate 60 percent
           tx-queue 6
              shape rate 70 percent
        !
        """
    ).strip()

    qos = CTreeSearcher.search(root, include_tags=["qos"])
    interface_or_qos = CTreeSearcher.search(root, include_tags=["qos", "interface"])
    interface_and_qos = CTreeSearcher.search(root, include_tags=["qos", "interface"], include_mode="and")
    assert qos.config == qos_config
    assert interface_or_qos.config == interface_or_qos_config
    assert interface_and_qos.config == interface_and_qos_config
