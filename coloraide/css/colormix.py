"""CSS Color 5 `color-mix()` parsing."""
from __future__ import annotations
from . import parse
from ..types import Vector
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from ..color import Color


def _parse_ident(text: str, index: int) -> tuple[str, int] | None:
    """Parse a CSS identifier (color space name) at the given index."""

    m = parse.RE_IDENT.match(text, index)
    if not m:
        return None
    return m.group(1), m.end()


def _parse_hue(text: str, index: int) -> tuple[str | None, int]:
    """Parse an optional `<hue-interpolation-method>` at the given index."""

    m = parse.RE_HUE.match(text, index)
    if not m:
        return None, index
    return m.group(1).lower(), m.end()

def _resolve_space(color_cls: type[Color], name: str) -> str | None:
    """Resolve a CSS color space identifier to a registered space name."""

    lower = name.lower()
    for space_class in color_cls.CS_MAP.values():
        if not space_class.COLOR_FORMAT:
            continue
        target = space_class.SERIALIZE if space_class.SERIALIZE else (space_class.NAME,)
        # Internal CSS identifiers may carry a `--` prefix (e.g. `--oklab` for `oklab()`);
        # match both the written CSS name and the internal identifier.
        ids = [t.lower() for t in target] + [t.lstrip('-').lower() for t in target]
        if lower in ids or lower == space_class.NAME.lower():
            return space_class.NAME
    return None


def _parse_percent(text: str, index: int) -> tuple[float, int] | None:
    """Parse a percentage at the given index."""

    m = parse.RE_PERCENT.match(text, index)
    if not m:
        return None
    return float(m.group(1)[:-1]), m.end()


def _parse_color_entry(
    color_cls: type[Color],
    text: str,
    index: int
) -> tuple[Color, float | None, int] | None:
    """Parse one `<color>` and its optional percentage from a color list."""

    # Nested colors (including nested `color-mix()`) are resolved via the normal matching logic
    m = color_cls._match(text, index, fullmatch=False)
    if m is None:
        return None
    color = color_cls(m[0].NAME, m[1], m[2])
    index = m[4]

    # Optional percentage weight, separated from the color by whitespace
    ws = parse.RE_SPACE.match(text, index)
    if ws:
        p = _parse_percent(text, ws.end())
        if p is not None:
            return color, p[0], p[1]
    return color, None, index


def _normalize_weights(percentages: list[float | None]) -> list[float] | None:
    """Normalize color-mix percentages per the CSS Color 5 rules."""

    given = [p is not None for p in percentages]

    if not any(given):
        # No percentages: every color gets equal weight
        weights = [1.0 / len(percentages)] * len(percentages)
        return weights

    if not all(given):
        # Fill missing percentages so the list totals 100%
        missing = sum(1 for g in given if not g)
        total = sum(p for p in percentages if p is not None)
        if total > 100.0 or missing == 0:
            return None
        fill = (100.0 - total) / missing
        values = [p if p is not None else fill for p in percentages]
    else:
        values = [float(p) for p in percentages]  # type: ignore[arg-type]

    # Negative percentages are invalid per the CSS grammar
    if any(v < 0.0 for v in values):
        return None

    total = sum(values)
    if total <= 0.0:
        return None

    # Scale when the weights do not total exactly 100% (under or over)
    scale = 100.0 / total
    return [v * scale / 100.0 for v in values]


def parse_color_mix(color_cls: type[Color], text: str, start: int = 0) -> dict[str, Any] | None:
    """
    Parse a CSS Color 5 `color-mix()` function.

    Returns a token dictionary with the resolved interpolation space, optional hue
    interpolation method, and the parsed color entries, or `None` if the text does
    not contain a valid `color-mix()` at the given position.
    """

    m = parse.RE_COLOR_MIX.match(text, start)
    if not m:
        return None

    index = m.end()
    m = parse.RE_FUNC_START.match(text, index)
    if not m:
        return None
    index = m.end()

    # Resolve the interpolation color space: optional whitespace, the `in` keyword, whitespace
    ws = parse.RE_LOOSE_SPACE.match(text, index)
    if ws is not None:
        index = ws.end()
    m = parse.RE_IN.match(text, index)
    if not m:
        return None
    index = m.end()
    # `RE_IN` only matches when whitespace follows, so this match always succeeds
    ws = parse.RE_SPACE.match(text, index)
    assert ws is not None
    index = ws.end()

    ident = _parse_ident(text, index)
    if ident is None:
        return None
    space_name, index = ident
    space = _resolve_space(color_cls, space_name)
    if space is None:
        return None

    # Optional hue interpolation method (only valid in polar/cylindrical spaces)
    hue, index = _parse_hue(text, index)
    if hue is not None and not color_cls.CS_MAP[space].is_polar():
        return None

    # The color list is comma separated; an optional comma may directly follow
    # the space/hue method per the CSS grammar
    m = parse.RE_COMMA.match(text, index)
    if m:
        index = m.end()

    colors = []  # type: list[Any]
    percentages = []  # type: list[float | None]

    while True:
        # Consume any whitespace before the color (required after the space/hue
        # method, optional following a comma which consumes its own whitespace)
        ws = parse.RE_LOOSE_SPACE.match(text, index)
        if ws is not None:
            index = ws.end()

        entry = _parse_color_entry(color_cls, text, index)
        if entry is None:
            return None
        color, percent, index = entry
        colors.append(color)
        percentages.append(percent)

        m = parse.RE_COMMA.match(text, index)
        if not m:
            break
        index = m.end()

    # At least two colors are required
    if len(colors) < 2:
        return None

    m = parse.RE_FUNC_END.match(text, index)
    if not m:
        return None
    index = m.end()

    weights = _normalize_weights(percentages)
    if weights is None:
        return None

    return {
        'space': space,
        'hue': hue if hue is not None else 'shorter',
        'colors': colors,
        'weights': weights,
        'end': index
    }


def color_mix(color_cls: type[Color], text: str, start: int = 0) -> tuple[tuple[str, Vector, float], int] | None:
    """Parse and evaluate a `color-mix()` function, returning space, coordinates, alpha, and end index."""

    tokens = parse_color_mix(color_cls, text, start)
    if tokens is None:
        return None

    result = color_cls.weighted_mix(
        tokens['colors'],
        tokens['weights'],
        space=tokens['space'],
        out_space=tokens['space'],
        hue=tokens['hue']
    )
    return (result.space(), result[:-1], result[-1]), tokens['end']
