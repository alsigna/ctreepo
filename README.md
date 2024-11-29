# Библиотека Conf-Tree

- [Библиотека Conf-Tree](#библиотека-conf-tree)
  - [Краткое описание](#краткое-описание)
  - [Быстрый пример (00.quick-start.py)](#быстрый-пример-00quick-startpy)
  - [Преобразование в дерево (01.parsing.py)](#преобразование-в-дерево-01parsingpy)
  - [Поиск/фильтрация (02.searching.py)](#поискфильтрация-02searchingpy)
  - [Сериализация/десериализация (03.serialization.py)](#сериализациядесериализация-03serializationpy)
  - [Изменение порядка](#изменение-порядка)

## Краткое описание

Библиотека для работы с конфигурацией сетевых устройств:

- преобразование конфигурации в дерево
- поиск/фильтрация конфигурации
- вычисление разницы (diff) между двумя конфигурациями

## Быстрый пример ([00.quick-start.py](./examples/00.quick-start.py))

- Читаем текущий и целевой конфигурации из файлов
- Преобразуем конфигурации в деревья, попутно размечая тегами секции bgp и static routes
- Получаем разницу конфигураций
- Фильтруем разницу (а можно сначала фильтровать текущее/целевое деревья, а потом вычислять разницу между ними)

<details>
    <summary>Листинг (click me)</summary>

```python
In [2]: from conf_tree import ConfTreeEnv, Vendor

In [3]: def get_configs() -> tuple[str, str]:
   ...:     with open(file="./examples/configs/cisco-router-1.txt", mode="r") as f:
   ...:         current_config = f.read()
   ...:     with open(file="./examples/configs/cisco-router-2.txt", mode="r") as f:
   ...:         target_config = f.read()
   ...:     return current_config, target_config
   ...: 

In [4]: def get_ct_environment() -> ConfTreeEnv:
   ...:     tagging_rules: list[dict[str, str | list[str]]] = [
   ...:         {"regex": r"^router bgp \d+$", "tags": ["bgp"]},
   ...:         {"regex": r"^ip route \S+", "tags": ["static"]},
   ...:     ]
   ...:     return ConfTreeEnv(
   ...:         vendor=Vendor.CISCO,
   ...:         tagging_rules=tagging_rules,
   ...:     )
   ...: 

In [5]: current_config, target_config = get_configs()

In [6]: env = get_ct_environment()

In [7]: current = env.parse(current_config)

In [8]: target = env.parse(target_config)

In [9]: diff = env.diff(current, target)

In [10]: print("\n!-- разница конфигураций --")
    ...: print(diff.config)
    ...: 

!-- разница конфигураций --
interface Tunnel2
 no ip ospf priority 0
 ip ospf priority 1
!
router bgp 64512
 no neighbor RR peer-group
 address-family ipv4
  network 10.255.255.1 mask 255.255.255.255
!
line vty 0 4
 no exec-timeout 15 0
 exec-timeout 10 0
!
line vty 5 15
 no exec-timeout 15 0
 exec-timeout 10 0
!
ip name-server 192.168.0.9
!
no ip name-server 192.168.0.3
!
no ip route 192.168.255.1 255.255.255.255 Tunnel2
!
no ip route vrf FVRF 192.66.55.44 255.255.255.255 143.31.31.2
!

In [11]: print("\n!-- разница без секций с тегами bgp и static --")
    ...: diff_no_routing = env.search(diff, exclude_tags=["bgp", "static"])
    ...: print(diff_no_routing.config)
    ...: 

!-- разница без секций с тегами bgp и static --
interface Tunnel2
 no ip ospf priority 0
 ip ospf priority 1
!
line vty 0 4
 no exec-timeout 15 0
 exec-timeout 10 0
!
line vty 5 15
 no exec-timeout 15 0
 exec-timeout 10 0
!
ip name-server 192.168.0.9
!
no ip name-server 192.168.0.3
!

In [12]: print("\n!-- разница в секции с тегом bgp --")
    ...: diff_bgp = env.search(diff, include_tags=["bgp"])
    ...: print(diff_bgp.config)
    ...: 

!-- разница в секции с тегом bgp --
router bgp 64512
 no neighbor RR peer-group
 address-family ipv4
  network 10.255.255.1 mask 255.255.255.255
!
```

</details>
<br>

## Преобразование в дерево ([01.parsing.py](./examples/01.parsing.py))

- Преобразование текстовой конфигурации в дерево на основе отступов в тексте
- Возможность размечать секции/строки тегами для последующей фильтрации
- pre-run и post-run обработка конфига и получившегося дерева, например нормализация входного конфига, обработка баннеров (cisco) и пр.

<details>
    <summary>Листинг (click me)</summary>

```python
In [1]: from conf_tree import ConfTreeEnv, Vendor

In [2]: def get_configs() -> str:
   ...:     with open(file="./examples/configs/cisco-example-1.txt", mode="r") as f:
   ...:         config = f.read()
   ...:     return config
   ...: 

In [3]: def get_ct_environment() -> ConfTreeEnv:
   ...:     return ConfTreeEnv(vendor=Vendor.CISCO)
   ...: 

In [4]: config_config = get_configs()

In [5]: env = get_ct_environment()

In [6]: current = env.parse(config_config)

In [7]: print("\n---дерево в виде привычной конфигурации---")
   ...: print(current.config)

---дерево в виде привычной конфигурации---
service tcp-keepalives-in
!
service timestamps debug datetime msec localtime show-timezone
!
enable secret 5 2Fe034RYzgb7xbt2pYxcpA==
!
aaa group server tacacs+ TacacsGroup
 server 192.168.0.100
 server 192.168.0.101
!
interface Tunnel1
 ip address 10.0.0.2 255.255.255.0
 no ip redirects
!
interface Tunnel2
 ip address 10.1.0.2 255.255.255.0
 no ip redirects
!
interface FastEthernet0
 switchport access vlan 100
 no ip address
!
router bgp 64512
 neighbor 192.168.255.1 remote-as 64512
 neighbor 192.168.255.1 update-source Loopback0
 address-family ipv4
  network 192.168.100.1 mask 255.255.255.0
  neighbor 192.168.255.1 activate
!

In [8]: print("\n---конфигурация с маскированными секретами---")
   ...: print(current.masked_config)

---конфигурация с маскированными секретами---
service tcp-keepalives-in
!
service timestamps debug datetime msec localtime show-timezone
!
enable secret 5 ******
!
aaa group server tacacs+ TacacsGroup
 server 192.168.0.100
 server 192.168.0.101
!
interface Tunnel1
 ip address 10.0.0.2 255.255.255.0
 no ip redirects
!
interface Tunnel2
 ip address 10.1.0.2 255.255.255.0
 no ip redirects
!
interface FastEthernet0
 switchport access vlan 100
 no ip address
!
router bgp 64512
 neighbor 192.168.255.1 remote-as 64512
 neighbor 192.168.255.1 update-source Loopback0
 address-family ipv4
  network 192.168.100.1 mask 255.255.255.0
  neighbor 192.168.255.1 activate
!

In [9]: print("\n---дерево в виде патча для устройства---")
   ...: print(current.patch)

---дерево в виде патча для устройства---
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
enable secret 5 2Fe034RYzgb7xbt2pYxcpA==
aaa group server tacacs+ TacacsGroup
server 192.168.0.100
server 192.168.0.101
exit
interface Tunnel1
ip address 10.0.0.2 255.255.255.0
no ip redirects
exit
interface Tunnel2
ip address 10.1.0.2 255.255.255.0
no ip redirects
exit
interface FastEthernet0
switchport access vlan 100
no ip address
exit
router bgp 64512
neighbor 192.168.255.1 remote-as 64512
neighbor 192.168.255.1 update-source Loopback0
address-family ipv4
network 192.168.100.1 mask 255.255.255.0
neighbor 192.168.255.1 activate
exit
exit

In [10]: print("\n---патч с маскированными секретами---")
    ...: print(current.masked_patch)

---патч с маскированными секретами---
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
enable secret 5 ******
aaa group server tacacs+ TacacsGroup
server 192.168.0.100
server 192.168.0.101
exit
interface Tunnel1
ip address 10.0.0.2 255.255.255.0
no ip redirects
exit
interface Tunnel2
ip address 10.1.0.2 255.255.255.0
no ip redirects
exit
interface FastEthernet0
switchport access vlan 100
no ip address
exit
router bgp 64512
neighbor 192.168.255.1 remote-as 64512
neighbor 192.168.255.1 update-source Loopback0
address-family ipv4
network 192.168.100.1 mask 255.255.255.0
neighbor 192.168.255.1 activate
exit
exit

In [11]: print("\n---дерево в виде формальной конфигурации (аналогично formal в ios-xr)---")
    ...: print(current.formal_config)

---дерево в виде формальной конфигурации (аналогично formal в ios-xr)---
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
enable secret 5 2Fe034RYzgb7xbt2pYxcpA==
aaa group server tacacs+ TacacsGroup / server 192.168.0.100
aaa group server tacacs+ TacacsGroup / server 192.168.0.101
interface Tunnel1 / ip address 10.0.0.2 255.255.255.0
interface Tunnel1 / no ip redirects
interface Tunnel2 / ip address 10.1.0.2 255.255.255.0
interface Tunnel2 / no ip redirects
interface FastEthernet0 / switchport access vlan 100
interface FastEthernet0 / no ip address
router bgp 64512 / neighbor 192.168.255.1 remote-as 64512
router bgp 64512 / neighbor 192.168.255.1 update-source Loopback0
router bgp 64512 / address-family ipv4 / network 192.168.100.1 mask 255.255.255.0
router bgp 64512 / address-family ipv4 / neighbor 192.168.255.1 activate
```

</details>
<br>

## Поиск/фильтрация ([02.searching.py](./examples/02.searching.py))

- может быть на основе тегов, проставленных во время преобразования в дерево
- может быть по строке (regex)
- в результате получается копия дерева с которой можно работать так же, как и с оригиналом

<details>
    <summary>Листинг (click me)</summary>

```python
In [1]: from conf_tree import ConfTreeEnv, Vendor
   ...: 
   ...: 
   ...: def get_configs() -> str:
   ...:     with open(file="./examples/configs/cisco-example-1.txt", mode="r") as f:
   ...:         config = f.read()
   ...:     return config
   ...: 
   ...: 
   ...: def get_ct_environment() -> ConfTreeEnv:
   ...:     tagging_rules: list[dict[str, str | list[str]]] = [
   ...:         {"regex": r"^router bgp \d+$", "tags": ["bgp"]},
   ...:         {"regex": r"^interface (Tunnel1) / ip address .*", "tags": ["interface", "tunnel-1-ip"]},
   ...:         {"regex": r"^interface (Tunnel2) / ip address .*", "tags": ["interface", "tunnel-1-ip"]},
   ...:         {"regex": r"^interface (\S+)$", "tags": ["interface"]},
   ...:     ]
   ...:     return ConfTreeEnv(
   ...:         vendor=Vendor.CISCO,
   ...:         tagging_rules=tagging_rules,
   ...:     )
   ...: 

In [2]: config_config = get_configs()
   ...: env = get_ct_environment()
   ...: router = env.parse(config_config)

In [3]: print("\n---все вхождения 'address'---")
   ...: address = env.search(router, string="address")
   ...: print(address.config)
   ...: 

---все вхождения 'address'---
interface Tunnel1
 ip address 10.0.0.2 255.255.255.0
!
interface Tunnel2
 ip address 10.1.0.2 255.255.255.0
!
interface FastEthernet0
 no ip address
!
router bgp 64512
 address-family ipv4
!

In [4]: print("\n---все вхождения 'address' с возможными потомками---")
   ...: address_children = env.search(router, string="address", include_children=True)
   ...: print(address_children.config)
   ...: 

---все вхождения 'address' с возможными потомками---
interface Tunnel1
 ip address 10.0.0.2 255.255.255.0
!
interface Tunnel2
 ip address 10.1.0.2 255.255.255.0
!
interface FastEthernet0
 no ip address
!
router bgp 64512
 address-family ipv4
  network 192.168.100.1 mask 255.255.255.0
  neighbor 192.168.255.1 activate
!

In [5]: print("\n---все вхождения 'address \d{1,3}'---")
   ...: address_ip = env.search(router, string=r"address \d{1,3}")
   ...: print(address_ip.config)
   ...: 

---все вхождения 'address \d{1,3}'---
interface Tunnel1
 ip address 10.0.0.2 255.255.255.0
!
interface Tunnel2
 ip address 10.1.0.2 255.255.255.0
!

In [6]: print("\n---конфигурация по тегу 'bgp'---")
   ...: bgp = env.search(router, include_tags=["bgp"])
   ...: print(bgp.masked_config)
   ...: 

---конфигурация по тегу 'bgp'---
router bgp 64512
 neighbor 192.168.255.1 remote-as 64512
 neighbor 192.168.255.1 update-source Loopback0
 address-family ipv4
  network 192.168.100.1 mask 255.255.255.0
  neighbor 192.168.255.1 activate
!

In [7]: print("\n---все, кроме тега 'bgp'---")
   ...: no_bgp = env.search(router, exclude_tags=["bgp"])
   ...: print(no_bgp.masked_config)
   ...: 

---все, кроме тега 'bgp'---
service tcp-keepalives-in
!
service timestamps debug datetime msec localtime show-timezone
!
enable secret 5 ******
!
aaa group server tacacs+ TacacsGroup
 server 192.168.0.100
 server 192.168.0.101
!
interface Tunnel1
 ip address 10.0.0.2 255.255.255.0
 no ip redirects
!
interface Tunnel2
 ip address 10.1.0.2 255.255.255.0
 no ip redirects
!
interface FastEthernet0
 switchport access vlan 100
 no ip address
!
```

</details>
<br>

Регулярные выражения пишутся для formal вида, т.е. строки с учетом иерархии над ней. Это дает возможность расставлять теги с учетом того, в какой секции находится конфигурационная строка:

```text
interface Tunnel1 / ip address 10.0.0.2 255.255.255.0
interface Tunnel2 / ip address 10.1.0.2 255.255.255.0
```

На ip интерфейса Tunnel1 вешаем тег "tunnel-1-ip", на ip интерфейса Tunnel2 вешаем тег "tunnel-2-ip"

```python
{
    "regex": r"^interface (Tunnel1) / ip address \S+ \S+(?: )?(secondary)?$",
    "tags": ["interface", "tunnel-1-ip"],
},
{
    "regex": r"^interface (Tunnel2) / ip address \S+ \S+(?: )?(secondary)?$",
    "tags": ["interface", "tunnel-1-ip"],
},
```

Если в регулярном выражении есть неименованные группы, то их содержимое автоматически попадает в теги:

```python
{
    "regex": r"^interface (\S+)$",
    "tags": ["interface"],
},
```

Помимо тега "interface", на строку конфигурации будет так же назначен тег, равный имени самого.

Если строка конфигурации не попала не в одно из правил, тогда теги для нее берутся из вышестоящего уровня. Например если на "interface Loopback0" были назначены теги ["interface", "Loopback0"], то все строки под этой секцией так же будут иметь эти теги, если явно не перезапишутся более узкими правилами.

## Сериализация/десериализация ([03.serialization.py](./examples/03.serialization.py))

Позволяет сохранить дерево в словарь и восстановить дерево из словаря, дальше в json, например сложить и сохранить в базу/отдать через API.

<details>
    <summary>Листинг (click me)</summary>

```python
In [1]: from conf_tree import ConfTreeEnv, Vendor
   ...: 
   ...: 
   ...: def get_configs() -> str:
   ...:     with open(file="./examples/configs/cisco-example-2.txt", mode="r") as f:
   ...:         config = f.read()
   ...:     return config
   ...: 
   ...: 
   ...: def get_ct_environment() -> ConfTreeEnv:
   ...:     tagging_rules: list[dict[str, str | list[str]]] = [
   ...:         {"regex": r"^router bgp \d+$", "tags": ["bgp"]},
   ...:         {"regex": r"^interface (\S+)$", "tags": ["interface"]},
   ...:     ]
   ...:     return ConfTreeEnv(
   ...:         vendor=Vendor.CISCO,
   ...:         tagging_rules=tagging_rules,
   ...:     )
   ...: 

In [2]: config = get_configs()
   ...: env = get_ct_environment()
   ...: router_original = env.parse(config)
   ...: 

In [3]: config_dict = env.to_dict(router_original)
   ...: print("\n---сериализация---")
   ...: print(config_dict)
   ...: 

---сериализация---
{'line': '', 'tags': [], 'children': {'service tcp-keepalives-in': {'line': 'service tcp-keepalives-in', 'tags': [], 'children': {}}, 'service timestamps debug datetime msec localtime show-timezone': {'line': 'service timestamps debug datetime msec localtime show-timezone', 'tags': [], 'children': {}}, 'interface FastEthernet0': {'line': 'interface FastEthernet0', 'tags': ['interface', 'FastEthernet0'], 'children': {'switchport access vlan 100': {'line': 'switchport access vlan 100', 'tags': ['interface', 'FastEthernet0'], 'children': {}}, 'no ip address': {'line': 'no ip address', 'tags': ['interface', 'FastEthernet0'], 'children': {}}}}, 'router bgp 64512': {'line': 'router bgp 64512', 'tags': ['bgp'], 'children': {'neighbor 192.168.255.1 remote-as 64512': {'line': 'neighbor 192.168.255.1 remote-as 64512', 'tags': ['bgp'], 'children': {}}, 'neighbor 192.168.255.1 update-source Loopback0': {'line': 'neighbor 192.168.255.1 update-source Loopback0', 'tags': ['bgp'], 'children': {}}, 'address-family ipv4': {'line': 'address-family ipv4', 'tags': ['bgp'], 'children': {'network 192.168.100.1 mask 255.255.255.0': {'line': 'network 192.168.100.1 mask 255.255.255.0', 'tags': ['bgp'], 'children': {}}, 'neighbor 192.168.255.1 activate': {'line': 'neighbor 192.168.255.1 activate', 'tags': ['bgp'], 'children': {}}}}}}}}

In [4]: router_restored = env.from_dict(config_dict)
   ...: print("\n---десериализация---")
   ...: print(router_restored.patch)

---десериализация---
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
interface FastEthernet0
switchport access vlan 100
no ip address
exit
router bgp 64512
neighbor 192.168.255.1 remote-as 64512
neighbor 192.168.255.1 update-source Loopback0
address-family ipv4
network 192.168.100.1 mask 255.255.255.0
neighbor 192.168.255.1 activate
exit
exit

In [5]: print("\n---равенство двух объектов---")
   ...: print(router_original == router_restored)

---равенство двух объектов---
True
```

</details>
<br>

## Изменение порядка

У дерева есть метод `reorder()`, который позволяет отсортировать конфигурацию в определенном порядке. Например в случаях, когда сначала нужно соблюсти порядок настройки объектов конфигурации: сначала prefix-lists, затем route-maps (которые используют созданные prefix-lists), затем назначить созданные route-maps на bgp пиров.

<details>
    <summary>Листинг (click me)</summary>

```python
In [1]: from conf_tree import ConfTreeEnv, Vendor
   ...: 
   ...: 
   ...: def get_configs() -> str:
   ...:     with open(file="./examples/configs/cisco-example-4.txt", mode="r") as f:
   ...:         config = f.read()
   ...:     return config
   ...: 
   ...: 
   ...: def get_ct_environment() -> ConfTreeEnv:
   ...:     tagging_rules: list[dict[str, str | list[str]]] = [
   ...:         {"regex": r"^router bgp .* neighbor (\S+) route-map (\S+) (?:in|out)", "tags": ["rm-attach"]},
   ...:         {"regex": r"^router bgp \d+$", "tags": ["bgp"]},
   ...:         {"regex": r"^route-map (\S+) (?:permit|deny) \d+$", "tags": ["rm"]},
   ...:         {"regex": r"^ip community-list (?:standard|expanded) (\S+)", "tags": ["cl"]},
   ...:         {"regex": r"^ip prefix-list (\S+)", "tags": ["pl"]},
   ...:     ]
   ...:     return ConfTreeEnv(
   ...:         vendor=Vendor.CISCO,
   ...:         tagging_rules=tagging_rules,
   ...:     )
   ...: 

In [2]: config = get_configs()
   ...: env = get_ct_environment()
   ...: router = env.parse(config)
   ...: 

In [3]: print("\n--community-list -> prefix-list -> route-map -> bgp -> untagged--")
   ...: router.reorder(["cl", "pl", "rm", "bgp"])
   ...: print(router.config)

--community-list -> prefix-list -> route-map -> bgp -> untagged--
ip community-list standard cl_PE1 permit 64512:10001
!
ip community-list standard cl_PE2 permit 64512:10002
!
ip community-list expanded cl_VPNv4_1 permit 64512:2[0-9][0-9][0-9]1
!
ip community-list expanded cl_VPNv4_2 permit 64512:2[0-9][0-9][0-9]2
!
ip prefix-list pl_CSC seq 5 permit 10.0.0.0/24 ge 32
!
route-map rm_CSC_PE_in deny 10
 match community cl_PE1 cl_PE2
!
route-map rm_CSC_PE_in permit 20
 match ip address prefix-list pl_CSC
 set local-preference 200
!
route-map rm_RR_in permit 10
 match community cl_VPNv4_1
 set local-preference 200
!
route-map rm_RR_in permit 20
 match community cl_VPNv4_2
 set local-preference 190
!
router bgp 64512
 neighbor CSC peer-group
 neighbor CSC remote-as 12345
 neighbor RR peer-group
 neighbor RR remote-as 64512
 address-family ipv4
  neighbor CSC send-community both
  neighbor CSC route-map rm_CSC_PE_in in
  neighbor CSC send-label
 address-family vpnv4
  neighbor RR route-map rm_RR_in in
!
no platform punt-keepalive disable-kernel-core
!
no service dhcp
!
ip dhcp bootp ignore
!
no service pad
!

In [4]: print("\n--bgp -> community-list -> prefix-list -> route-map -> untagged -> rm-attach--")
   ...: wo_rm_attach = env.search(router, exclude_tags=["rm-attach"])
   ...: rm_attach = env.search(router, include_tags=["rm-attach"])
   ...: wo_rm_attach.reorder(["bgp", "cl", "pl", "rm"])
   ...: print(wo_rm_attach.config)
   ...: print(rm_attach.config)

--bgp -> community-list -> prefix-list -> route-map -> untagged -> rm-attach--
router bgp 64512
 neighbor CSC peer-group
 neighbor CSC remote-as 12345
 neighbor RR peer-group
 neighbor RR remote-as 64512
 address-family ipv4
  neighbor CSC send-community both
  neighbor CSC send-label
 address-family vpnv4
!
ip community-list standard cl_PE1 permit 64512:10001
!
ip community-list standard cl_PE2 permit 64512:10002
!
ip community-list expanded cl_VPNv4_1 permit 64512:2[0-9][0-9][0-9]1
!
ip community-list expanded cl_VPNv4_2 permit 64512:2[0-9][0-9][0-9]2
!
ip prefix-list pl_CSC seq 5 permit 10.0.0.0/24 ge 32
!
route-map rm_CSC_PE_in deny 10
 match community cl_PE1 cl_PE2
!
route-map rm_CSC_PE_in permit 20
 match ip address prefix-list pl_CSC
 set local-preference 200
!
route-map rm_RR_in permit 10
 match community cl_VPNv4_1
 set local-preference 200
!
route-map rm_RR_in permit 20
 match community cl_VPNv4_2
 set local-preference 190
!
no platform punt-keepalive disable-kernel-core
!
no service dhcp
!
ip dhcp bootp ignore
!
no service pad
!
router bgp 64512
 address-family ipv4
  neighbor CSC route-map rm_CSC_PE_in in
 address-family vpnv4
  neighbor RR route-map rm_RR_in in
!
```

</details>
<br>
