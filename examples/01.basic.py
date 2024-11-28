from conf_tree import ConfTreeEnv  # общий класс, собирающий весь функционал в единую точку входа
from conf_tree import Vendor  # список доступных производителей

with open("./examples/configs/cisco-router.txt", "r") as f:
    config_str = f.read()

ct_env = ConfTreeEnv(
    vendor=Vendor.CISCO,  # обязательный аргумент
)

# преобразование текстовой конфигурации в дерево
router = ct_env.parse(config=config_str)

# .config - дерево в удобном (привычном) для инженера виде
# print(router.config)

# .patch - патч для устройства, та же информация, что и в config, но без отступов и с выходами из секций
# print(router.patch)

# поиск конфигурации в дереве
af_ipv4 = ct_env.search(
    ct=router,  # где ищем
    string="address-family ipv4",  # что ищем
    include_children=True,  # если у найденной секции есть потомки, включать их в результат или нет
)
# результатом поиска является такой же объект, как и исходное дерево, у него доступны те же атрибуты
# print(af_ipv4.config)

# поиск может быть по регулярному выражению, например все упоминания "network 192.168.x.x"
ip = ct_env.search(
    ct=router,
    string=r"network 192\.168\.\d{1,3}\.\d{1,3}",
    include_children=True,
)
# результат - отфильтрованное дерево
# print(ip.config)
