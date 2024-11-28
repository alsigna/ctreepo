# Библиотека Conf-Tree

- [Библиотека Conf-Tree](#библиотека-conf-tree)
  - [Краткое описание](#краткое-описание)
  - [Быстрый пример (00.quick-start.py)](#быстрый-пример-00quick-startpy)
  - [Простейший поиск](#простейший-поиск)

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

## Простейший поиск

```python
```
