def is_base_excluded(
    base_name: str,
    base_distro: str,
    base_exclude: set[str],
    base_distro_exclude: set[str],
) -> bool:
    base_name_lc = base_name.lower()
    if base_name_lc in base_exclude:
        return True
    if base_distro.lower() in base_distro_exclude:
        return True
    return False


def normalize_exclude(values: list[str]) -> set[str]:
    if not values:
        return set()
    return {value.lower() for value in values}
