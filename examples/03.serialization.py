from conf_tree import ConfTreeEnv, Vendor


def get_configs() -> str:
    with open(file="./examples/configs/cisco-example-2.txt", mode="r") as f:
        config = f.read()
    return config


def get_ct_environment() -> ConfTreeEnv:
    tagging_rules: list[dict[str, str | list[str]]] = [
        {"regex": r"^router bgp \d+$", "tags": ["bgp"]},
        {"regex": r"^interface (\S+)$", "tags": ["interface"]},
    ]
    return ConfTreeEnv(
        vendor=Vendor.CISCO,
        tagging_rules=tagging_rules,
    )


if __name__ == "__main__":
    config = get_configs()
    env = get_ct_environment()
    router_original = env.parse(config)

    config_dict = env.to_dict(router_original)
    print("\n---сериализация---")
    print(config_dict)

    router_restored = env.from_dict(config_dict)
    print("\n---десериализация---")
    print(router_restored.patch)

    print("\n---равенство двух объектов---")
    print(router_original == router_restored)
