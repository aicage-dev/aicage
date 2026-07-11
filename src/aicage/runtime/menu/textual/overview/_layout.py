from rich.cells import cell_len

from .._models import BuiltInShareValue, CustomShareValue


def shell_width(
    built_in_shares: list[BuiltInShareValue],
    custom_shares: list[CustomShareValue],
    viewport_width: int,
) -> int:
    min_width = 92
    section_row_width = 90
    shell_overhead = 16
    longest_share_width = max((cell_len(text) for text in _share_row_texts(built_in_shares, custom_shares)), default=0)
    target_width = max(section_row_width, longest_share_width + shell_overhead, min_width)
    viewport_cap = max(viewport_width - 4, min_width)
    return min(target_width, viewport_cap)


def _share_row_texts(
    built_in_shares: list[BuiltInShareValue],
    custom_shares: list[CustomShareValue],
) -> list[str]:
    texts = [f"{item.label}: {item.path}" for item in built_in_shares]
    texts.extend(item.value for item in custom_shares)
    return texts
