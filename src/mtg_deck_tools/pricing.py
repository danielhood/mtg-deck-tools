"""Fixed pricing rules for deck building and budget estimates."""

from __future__ import annotations

BASIC_LAND_PRICE_USD = 0.05


def is_basic_land_card(*, is_basic_land: bool = False, type_line: str = "") -> bool:
    return is_basic_land or type_line.startswith("Basic Land")


def basic_land_price() -> tuple[float, bool]:
    """USD price and price_known flag used for all basic lands."""
    return BASIC_LAND_PRICE_USD, True


def resolve_card_price(
    *,
    price_usd: float | None,
    price_known: bool,
    is_basic_land: bool = False,
    type_line: str = "",
) -> tuple[float | None, bool]:
    """Return effective price; basic lands always use BASIC_LAND_PRICE_USD."""
    if is_basic_land_card(is_basic_land=is_basic_land, type_line=type_line):
        return basic_land_price()
    return price_usd, price_known
