from textwrap import dedent

from conf_tree import ConfTreeDiffer, ConfTreeParser, Vendor


def test_huawei_interface_post_processing_1() -> None:
    config_interfaces_1 = dedent(
        """
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
        """
    ).strip()

    config_interfaces_2 = dedent(
        """
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
        """
    ).strip()

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
    parser = ConfTreeParser(Vendor.HUAWEI)

    root1 = parser.parse(config_interfaces_1)
    root2 = parser.parse(config_interfaces_2)

    diff = ConfTreeDiffer.diff(root1, root2)
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_huawei_interface_post_processing_2() -> None:
    current_config = dedent(
        """
        interface GigabitEthernet0/0/1
         auto speed 10 100
         port link-type hybrid
         voice-vlan 101 enable
         vcmp disable
         port hybrid pvid vlan 102
         port hybrid tagged vlan 103
         port hybrid untagged vlan 104
         stp edged-port enable
         authentication-profile my_profile
         unicast-suppression packets 10
         multicast-suppression packets 20
         broadcast-suppression packets 30
        #
        """
    ).strip()

    target_config = dedent(
        """
        #
        interface GigabitEthernet0/0/1
         auto speed 10 100
         port link-type trunk
         port trunk pvid vlan 102
         port trunk allow-pass vlan 102 105 107
         voice-vlan 102 enable
         vcmp disable
         stp edged-port enable
         authentication-profile my_profile
         unicast-suppression packets 10
         multicast-suppression packets 20
         broadcast-suppression packets 30
        #
        """
    ).strip()

    diff_config = dedent(
        """
        interface GigabitEthernet0/0/1
         undo port link-type
         undo voice-vlan 101 enable
         port link-type trunk
         port trunk pvid vlan 102
         port trunk allow-pass vlan 102 105 107
         voice-vlan 102 enable
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        interface GigabitEthernet0/0/1
        undo port link-type
        undo voice-vlan 101 enable
        port link-type trunk
        port trunk pvid vlan 102
        port trunk allow-pass vlan 102 105 107
        voice-vlan 102 enable
        quit
        """
    ).strip()
    parser = ConfTreeParser(Vendor.HUAWEI)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = ConfTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_huawei_route_policy_post_processing() -> None:
    current_config = dedent(
        """
        route-policy RP_NAME_1 permit node 10
         if-match ip-prefix PL_NAME_1
         if-match ip next-hop ip-prefix PL_NHOP_NAME_1
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 20
         if-match ip-prefix PL_NAME_2
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 30
         if-match ip-prefix PL_NAME_1
         if-match ip next-hop ip-prefix PL_NHOP_NAME_1_1
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 40
         if-match ip-prefix PL_NAME_1
         if-match ip next-hop ip-prefix PL_NHOP_NAME_1_2
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 50
         if-match ip-prefix PL_NAME_3
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 70
         if-match ip-prefix PL_NAME_4
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 80
         if-match ip-prefix PL_NAME_5
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 90
         if-match ip-prefix PL_NAME_6
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 100
         if-match ip-prefix PL_NAME_7
         if-match ip next-hop ip-prefix PL_NHOP_NAME_3
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_2 permit node 10
         if-match ip-prefix PL_NAME_8
        #
        route-policy RP_NAME_2 permit node 20
         if-match ip-prefix PL_NAME_9
        #
        route-policy RP_NAME_3 permit node 5
         apply community community-list CL_NAME_2 additive
        #
        """
    ).strip()
    target_config = dedent(
        """
        route-policy RP_NAME_1 permit node 10
         if-match ip-prefix PL_NAME_1
         if-match ip next-hop ip-prefix PL_NHOP_NAME_1
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 30
         if-match ip-prefix PL_NAME_1
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 40
         if-match ip-prefix PL_NAME_1
         if-match ip next-hop ip-prefix PL_NHOP_NAME_1_2
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 50
         if-match ip-prefix PL_NAME_3
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 70
         if-match ip-prefix PL_NAME_4
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 80
         if-match ip-prefix PL_NAME_5
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 90
         if-match ip-prefix PL_NAME_6
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_NAME_1 permit node 100
         if-match ip-prefix PL_NAME_7
         if-match ip next-hop ip-prefix PL_NHOP_NAME_3
         apply community community-list CL_NAME_1 additive
        #
        route-policy RP_BLOCK deny node 10
        #
        route-policy RP_NAME_3 permit node 5
         apply community community-list CL_NAME_2 additive
        #
        """
    ).strip()
    diff_config = dedent(
        """
        route-policy RP_NAME_1 permit node 30
         undo if-match ip next-hop ip-prefix PL_NHOP_NAME_1_1
        #
        route-policy RP_BLOCK deny node 10
        #
        undo route-policy RP_NAME_1 node 20
        #
        undo route-policy RP_NAME_2 node 10
        #
        undo route-policy RP_NAME_2 node 20
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        route-policy RP_NAME_1 permit node 30
        undo if-match ip next-hop ip-prefix PL_NHOP_NAME_1_1
        quit
        route-policy RP_BLOCK deny node 10
        quit
        undo route-policy RP_NAME_1 node 20
        undo route-policy RP_NAME_2 node 10
        undo route-policy RP_NAME_2 node 20
        """
    ).strip()
    parser = ConfTreeParser(vendor=Vendor.HUAWEI)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = ConfTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_huawei_prefix_list_post_processing() -> None:
    current_config = dedent(
        """
        ip ip-prefix TEST_PL_1 index 10 permit 10.1.50.0 23 greater-equal 32 less-equal 32
        ip ip-prefix TEST_PL_2 index 10 permit 10.2.50.0 23 greater-equal 32 less-equal 32
        ip ip-prefix TEST_PL_3 index 10 permit 10.3.50.0 24 greater-equal 32 less-equal 32
        """
    ).strip()
    target_config = dedent(
        """
        ip ip-prefix TEST_PL_1 index 10 permit 10.0.0.0 243 greater-equal 32 less-equal 32
        ip ip-prefix TEST_PL_3 index 10 permit 10.3.50.0 24 greater-equal 32 less-equal 32
        """
    ).strip()
    diff_config = dedent(
        """
        ip ip-prefix TEST_PL_1 index 10 permit 10.0.0.0 243 greater-equal 32 less-equal 32
        #
        undo ip ip-prefix TEST_PL_2 index 10
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        ip ip-prefix TEST_PL_1 index 10 permit 10.0.0.0 243 greater-equal 32 less-equal 32
        undo ip ip-prefix TEST_PL_2 index 10
        """
    ).strip()

    parser = ConfTreeParser(vendor=Vendor.HUAWEI)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = ConfTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_huawei_user_post_processing_1() -> None:
    # случай 1: не меняем пароль для пользователей user1/user2, состав пользователей совпадает
    target_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
        #
        """
    ).strip()
    current_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher some_password_hash_1
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher some_password_hash_2
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
        #
        """
    ).strip()
    diff_config_raw = dedent(
        """
        aaa
         undo local-user user1@default password irreversible-cipher some_password_hash_1
         undo local-user user2@default password irreversible-cipher some_password_hash_2
         local-user user1@default password irreversible-cipher
         local-user user2@default password irreversible-cipher
        #
        """
    ).strip()
    diff_config_processed = ""
    parser = ConfTreeParser(Vendor.HUAWEI)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = ConfTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw

    diff_processed = ConfTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed


def test_huawei_user_post_processing_2() -> None:
    # случай 2: меняем пароль для user1, не меняем для user2, состав пользователей совпадает
    target_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
        #
        """
    ).strip()
    current_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher some_password_hash_1
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher some_password_hash_2
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
        #
        """
    ).strip()
    diff_config_raw = dedent(
        """
        aaa
         undo local-user user1@default password irreversible-cipher some_password_hash_1
         undo local-user user2@default password irreversible-cipher some_password_hash_2
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user2@default password irreversible-cipher
        #
        """
    ).strip()
    diff_config_processed = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher P@ssw0rd
        #
        """
    ).strip()
    parser = ConfTreeParser(Vendor.HUAWEI)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = ConfTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw

    diff_processed = ConfTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed


def test_huawei_user_post_processing_3() -> None:
    # случай 3: меняем пароль для user1, не меняем для user2, на устройстве лишний пользователь
    target_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
        #
        """
    ).strip()
    current_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher some_password_hash_1
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher some_password_hash_2
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
         local-user user3@default password irreversible-cipher some_password_hash_3
         local-user user3@default service-type terminal ssh
         local-user user3@default level 3
        #
        """
    ).strip()
    diff_config_raw = dedent(
        """
        aaa
         undo local-user user1@default password irreversible-cipher some_password_hash_1
         undo local-user user2@default password irreversible-cipher some_password_hash_2
         undo local-user user3@default password irreversible-cipher some_password_hash_3
         undo local-user user3@default service-type terminal ssh
         undo local-user user3@default level 3
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user2@default password irreversible-cipher
        #
        """
    ).strip()
    diff_config_processed = dedent(
        """
        aaa
         undo local-user user3@default
         local-user user1@default password irreversible-cipher P@ssw0rd
        #
        """
    ).strip()

    parser = ConfTreeParser(Vendor.HUAWEI)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = ConfTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw

    diff_processed = ConfTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed


def test_huawei_user_post_processing_4() -> None:
    # случай 4: меняем пароль для user1, не меняем для user2, на устройстве не хватает пользователя и один лишний
    target_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
         local-user user4@default password irreversible-cipher P@ssw0rd
         local-user user4@default service-type terminal ssh
         local-user user4@default level 3
        #
        """
    ).strip()
    current_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher some_password_hash_1
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher some_password_hash_2
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
         local-user user3@default password irreversible-cipher some_password_hash_3
         local-user user3@default service-type terminal ssh
         local-user user3@default level 3
        #
        """
    ).strip()
    diff_config_raw = dedent(
        """
        aaa
         undo local-user user1@default password irreversible-cipher some_password_hash_1
         undo local-user user2@default password irreversible-cipher some_password_hash_2
         undo local-user user3@default password irreversible-cipher some_password_hash_3
         undo local-user user3@default service-type terminal ssh
         undo local-user user3@default level 3
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user2@default password irreversible-cipher
         local-user user4@default password irreversible-cipher P@ssw0rd
         local-user user4@default service-type terminal ssh
         local-user user4@default level 3
        #
        """
    ).strip()
    diff_config_processed = dedent(
        """
        aaa
         undo local-user user3@default
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user4@default password irreversible-cipher P@ssw0rd
         local-user user4@default service-type terminal ssh
         local-user user4@default level 3
        #
        """
    ).strip()

    parser = ConfTreeParser(Vendor.HUAWEI)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = ConfTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw

    diff_processed = ConfTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed


def test_huawei_user_post_processing_5() -> None:
    # случай 5: меняем пароль для user1, не меняем для user2, меняем level для user2
    target_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher
         local-user user2@default service-type terminal ssh
         local-user user2@default level 1
        #
        """
    ).strip()
    current_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher some_password_hash_1
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher some_password_hash_2
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
        #
        """
    ).strip()
    diff_config_raw = dedent(
        """
        aaa
         undo local-user user1@default password irreversible-cipher some_password_hash_1
         undo local-user user2@default password irreversible-cipher some_password_hash_2
         undo local-user user2@default level 3
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user2@default password irreversible-cipher
         local-user user2@default level 1
        #
        """
    ).strip()
    diff_config_processed = dedent(
        """
        aaa
         undo local-user user2@default level
         local-user user1@default password irreversible-cipher P@ssw0rd
         local-user user2@default level 1
        #
        """
    ).strip()

    parser = ConfTreeParser(Vendor.HUAWEI)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = ConfTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw

    diff_processed = ConfTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed


def test_huawei_user_post_processing_6() -> None:
    # случай 6:
    # - user1 нет в системе, а в целевом конфиге нет пароля
    # - user2 есть в системе и в целевом конфиге есть пароль
    # - user3 есть в системе, а в целевом конфиге нет пароля
    target_config = dedent(
        """
        aaa
         local-user user1@default password irreversible-cipher
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher P@ssw0rd
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
         local-user user3@default password irreversible-cipher
         local-user user3@default service-type terminal ssh
         local-user user3@default level 1
        #
        """
    ).strip()
    current_config = dedent(
        """
        aaa
         local-user user2@default password irreversible-cipher some_password_hash_2
         local-user user2@default service-type terminal ssh
         local-user user2@default level 3
         local-user user3@default password irreversible-cipher some_password_hash_3
         local-user user3@default service-type terminal ssh
         local-user user3@default level 3
        #
        """
    ).strip()
    diff_config_raw = dedent(
        """
        aaa
         undo local-user user2@default password irreversible-cipher some_password_hash_2
         undo local-user user3@default password irreversible-cipher some_password_hash_3
         undo local-user user3@default level 3
         local-user user1@default password irreversible-cipher
         local-user user1@default service-type terminal ssh
         local-user user1@default level 3
         local-user user2@default password irreversible-cipher P@ssw0rd
         local-user user3@default password irreversible-cipher
         local-user user3@default level 1
        #
        """
    ).strip()
    diff_config_processed = dedent(
        """
        aaa
         undo local-user user3@default level
         local-user user2@default password irreversible-cipher P@ssw0rd
         local-user user3@default level 1
        #
        """
    ).strip()

    parser = ConfTreeParser(Vendor.HUAWEI)
    target = parser.parse(target_config)
    current = parser.parse(current_config)
    diff_raw = ConfTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff_raw.config == diff_config_raw

    diff_processed = ConfTreeDiffer.diff(current, target)
    assert diff_processed.config == diff_config_processed


def test_huawei_postproc_bgp() -> None:
    current_config = ""
    target_config = dedent(
        """
        route-map RM_TEST permit 10
         match ip address prefix-list PL_TEST
        #
        bgp 12345
         router-id 1.2.3.4
         no bgp default ipv4-unicast
         maximum-paths 4 ecmp 64
         address-family ipv4
          neighbor PEER_GROUP_1 activate
          neighbor PEER_GROUP_2 activate
         vrf VRF_NAME_1
          router-id 1.2.3.4
          rd 1.2.3.4:123
          route-target import evpn 123:456
          route-target export evpn 123:456
          bgp listen range 1.2.3.0/24 peer-group PEER_GROUP_1 peer-filter AS12345
         address-family evpn
          neighbor PEER_GROUP_3 activate
         neighbor PEER_GROUP_1 peer group
         neighbor PEER_GROUP_1 bfd
         neighbor PEER_GROUP_2 peer group
         neighbor PEER_GROUP_3 peer group
         neighbor 192.168.0.1 peer group PEER_GROUP_1
         neighbor 192.168.0.1 remote-as 12345
         neighbor 192.168.0.2 peer group PEER_GROUP_2
         neighbor 192.168.0.2 remote-as 12345
         neighbor 192.168.0.3 peer group PEER_GROUP_3
         neighbor 192.168.0.3 remote-as 12345
        #
        """
    ).strip()
    diff_config = dedent(
        """
        route-map RM_TEST permit 10
         match ip address prefix-list PL_TEST
        #
        bgp 12345
         router-id 1.2.3.4
         no bgp default ipv4-unicast
         maximum-paths 4 ecmp 64
         neighbor PEER_GROUP_1 peer group
         neighbor PEER_GROUP_1 bfd
         neighbor PEER_GROUP_2 peer group
         neighbor PEER_GROUP_3 peer group
         neighbor 192.168.0.1 peer group PEER_GROUP_1
         neighbor 192.168.0.1 remote-as 12345
         neighbor 192.168.0.2 peer group PEER_GROUP_2
         neighbor 192.168.0.2 remote-as 12345
         neighbor 192.168.0.3 peer group PEER_GROUP_3
         neighbor 192.168.0.3 remote-as 12345
         address-family ipv4
          neighbor PEER_GROUP_1 activate
          neighbor PEER_GROUP_2 activate
         vrf VRF_NAME_1
          router-id 1.2.3.4
          rd 1.2.3.4:123
          route-target import evpn 123:456
          route-target export evpn 123:456
          bgp listen range 1.2.3.0/24 peer-group PEER_GROUP_1 peer-filter AS12345
         address-family evpn
          neighbor PEER_GROUP_3 activate
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        route-map RM_TEST permit 10
        match ip address prefix-list PL_TEST
        quit
        bgp 12345
        router-id 1.2.3.4
        no bgp default ipv4-unicast
        maximum-paths 4 ecmp 64
        neighbor PEER_GROUP_1 peer group
        neighbor PEER_GROUP_1 bfd
        neighbor PEER_GROUP_2 peer group
        neighbor PEER_GROUP_3 peer group
        neighbor 192.168.0.1 peer group PEER_GROUP_1
        neighbor 192.168.0.1 remote-as 12345
        neighbor 192.168.0.2 peer group PEER_GROUP_2
        neighbor 192.168.0.2 remote-as 12345
        neighbor 192.168.0.3 peer group PEER_GROUP_3
        neighbor 192.168.0.3 remote-as 12345
        address-family ipv4
        neighbor PEER_GROUP_1 activate
        neighbor PEER_GROUP_2 activate
        quit
        vrf VRF_NAME_1
        router-id 1.2.3.4
        rd 1.2.3.4:123
        route-target import evpn 123:456
        route-target export evpn 123:456
        bgp listen range 1.2.3.0/24 peer-group PEER_GROUP_1 peer-filter AS12345
        quit
        address-family evpn
        neighbor PEER_GROUP_3 activate
        quit
        quit
        """
    ).strip()

    parser = ConfTreeParser(Vendor.HUAWEI)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = ConfTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_huawei_postproc_aaa() -> None:
    current_config = dedent(
        """
        aaa
         authorization-scheme scheme-name
          authorization-mode local if-authenticated
        """
    )
    target_config = dedent(
        """
        aaa
         undo local-user policy security-enhance
         default-domain admin domain-name
         authentication-scheme default
         authentication-scheme scheme-name
          authentication-mode hwtacacs local
         authentication-scheme local
         authorization-scheme default
         authorization-scheme scheme-name
          authorization-mode local if-authenticated
         accounting-scheme default
         domain default
         domain default_admin
         domain domain-name
          authentication-scheme group-name
          authorization-scheme group-name
          hwtacacs server group-name
         domain local
          authentication-scheme local
        """
    ).strip()
    diff_config = dedent(
        """
        aaa
         undo local-user policy security-enhance
         default-domain admin domain-name
         authentication-scheme default
         authentication-scheme scheme-name
          authentication-mode hwtacacs local
         authentication-scheme local
         authorization-scheme default
         accounting-scheme default
         domain default
         domain default_admin
         domain domain-name
          authentication-scheme group-name
          authorization-scheme group-name
          hwtacacs server group-name
         domain local
          authentication-scheme local
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        aaa
        undo local-user policy security-enhance
        default-domain admin domain-name
        authentication-scheme default
        quit
        authentication-scheme scheme-name
        authentication-mode hwtacacs local
        quit
        authentication-scheme local
        quit
        authorization-scheme default
        quit
        accounting-scheme default
        quit
        domain default
        quit
        domain default_admin
        quit
        domain domain-name
        authentication-scheme group-name
        authorization-scheme group-name
        hwtacacs server group-name
        quit
        domain local
        authentication-scheme local
        quit
        quit
        """
    ).strip()

    parser = ConfTreeParser(Vendor.HUAWEI)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = ConfTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    assert diff.patch == diff_patch


def test_huawei_postproc_tacacs_1() -> None:
    current_config = dedent(
        """
        hwtacacs-server template group-name
         hwtacacs-server authentication 10.0.0.1 vpn-instance MGMT
         hwtacacs-server authentication 10.0.0.2 vpn-instance MGMT secondary
         hwtacacs-server authentication 10.0.0.3 vpn-instance MGMT third
         undo hwtacacs-server user-name domain-included
         hwtacacs-server shared-key cipher old_secret_hash
        #
        """
    )
    target_config = dedent(
        """
        hwtacacs-server template group-name
         hwtacacs-server authentication 10.0.0.1 vpn-instance MGMT
         hwtacacs-server authentication 10.0.0.2 vpn-instance MGMT secondary
         hwtacacs-server authentication 10.0.0.3 vpn-instance MGMT third
         undo hwtacacs-server user-name domain-included
         hwtacacs-server shared-key cipher
        #
        """
    )
    diff_raw = dedent(
        """
        hwtacacs-server template group-name
         undo hwtacacs-server shared-key cipher old_secret_hash
         hwtacacs-server shared-key cipher
        #
        """
    ).strip()
    diff_processed = ""

    parser = ConfTreeParser(Vendor.HUAWEI)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = ConfTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff.config == diff_raw

    diff = ConfTreeDiffer.diff(current, target)
    assert diff.config == diff_processed


def test_huawei_postproc_tacacs_2() -> None:
    current_config = dedent(
        """
        hwtacacs-server template group-name
         hwtacacs-server authentication 10.0.0.1 vpn-instance MGMT
         hwtacacs-server authentication 10.0.0.2 vpn-instance MGMT secondary
         hwtacacs-server authentication 10.0.0.3 vpn-instance MGMT third
         undo hwtacacs-server user-name domain-included
         hwtacacs-server shared-key cipher old_secret_hash
        #
        """
    )
    target_config = dedent(
        """
        hwtacacs-server template group-name
         hwtacacs-server authentication 10.0.0.1 vpn-instance MGMT
         hwtacacs-server authentication 10.0.0.2 vpn-instance MGMT secondary
         hwtacacs-server authentication 10.0.0.3 vpn-instance MGMT third
         undo hwtacacs-server user-name domain-included
         hwtacacs-server shared-key cipher new_secret_hash
        #
        """
    )
    diff_raw = dedent(
        """
        hwtacacs-server template group-name
         undo hwtacacs-server shared-key cipher old_secret_hash
         hwtacacs-server shared-key cipher new_secret_hash
        #
        """
    ).strip()
    diff_processed = dedent(
        """
        hwtacacs-server template group-name
         hwtacacs-server shared-key cipher new_secret_hash
        #
        """
    ).strip()

    parser = ConfTreeParser(Vendor.HUAWEI)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = ConfTreeDiffer.diff(current, target, post_proc_rules=[])
    assert diff.config == diff_raw

    diff = ConfTreeDiffer.diff(current, target)
    assert diff.config == diff_processed
