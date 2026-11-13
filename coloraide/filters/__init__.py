"""Provides a plugin system for filtering colors."""
from __future__ import annotations
import math
import re
from abc import ABCMeta, abstractmethod
from ..types import Plugin, AnyColor
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:  #pragma: no cover
    from ..color import Color

RE_FILTER_START = re.compile(r'\s*([A-Za-z][-A-Za-z0-9]*)\(')

# Angle units and their conversion factor to degrees.
ANGLES = {
    'grad': 360.0 / 400.0,
    'turn': 360.0,
    'deg': 1.0,
    'rad': 180.0 / math.pi
}


class Filter(Plugin, metaclass=ABCMeta):
    """Filter a color."""

    NAME = ''
    DEFAULT_SPACE = 'srgb-linear'
    ALLOWED_SPACES = ('srgb-linear',)  # type: tuple[str, ...]

    @abstractmethod
    def filter(self, color: Color, amount: float | None, **kwargs: Any) -> None:  # noqa: A003
        """Filter the given color."""


def parse_amount(name: str, arg: str) -> float | None:
    """
    Parse a CSS filter function argument.

    Percentages are scaled to a 0 - 1 range and angles are converted to degrees.
    """

    if not arg:
        # No argument, use the filter's default
        return None

    parts = arg.split()
    if len(parts) > 1:
        raise ValueError(f"'{name}' accepts at most one argument, got '{arg}'")

    token = parts[0].lower()

    if token.endswith('%'):
        if name == 'hue-rotate':
            raise ValueError(f"'{name}' does not accept a percentage value: '{arg}'")
        number = token[:-1]
        scale = 0.01
    else:
        scale = 1.0
        number = token
        for unit, factor in ANGLES.items():
            if token.endswith(unit):
                if name != 'hue-rotate':
                    raise ValueError(f"'{name}' does not accept an angle value: '{arg}'")
                number = token[:-len(unit)]
                scale = factor
                break

    try:
        return float(number) * scale
    except ValueError:
        raise ValueError(f"Could not parse the '{name}' filter argument '{arg}'") from None


def parse_filter_list(string: str) -> list[tuple[str, float | None]]:
    """
    Parse a CSS filter function list such as `sepia(60%) hue-rotate(90deg)`.

    Functions are returned in the order they are specified so they can be
    applied sequentially, just as a browser would apply them.
    """

    if not string.strip():
        raise ValueError('Filter list is empty, no filter functions were specified')

    chain = []
    pos = 0
    end = len(string)
    while pos < end:
        if string[pos].isspace():
            pos += 1
            continue

        if string[pos] == ',':
            raise ValueError(
                'Filter functions must be separated by whitespace, not commas: '
                f"'{string}'"
            )

        m = RE_FILTER_START.match(string, pos)
        if m is None:
            raise ValueError(f"Could not parse the filter function list at '{string[pos:]}'")

        name = m.group(1).lower()

        # Find the closing parenthesis; filter arguments cannot nest parentheses.
        close = string.find(')', m.end())
        if close == -1:
            raise ValueError(f"Unclosed parenthesis in the filter function '{name}('")
        if '(' in string[m.end():close]:
            raise ValueError(f"Could not parse the arguments of the filter function '{name}'")

        chain.append((name, parse_amount(name, string[m.end():close].strip())))
        pos = close + 1

    return chain


def filters(
    color: AnyColor,
    name: str,
    amount: float | None = None,
    space: str | None = None,
    out_space: str | None = None,
    in_place: bool = False,
    **kwargs: Any
) -> AnyColor:
    """Filter."""

    if '(' in name or ',' in name or not name.strip():
        if amount is not None:
            raise ValueError("Cannot specify an 'amount' with a CSS filter function list")
        chain = parse_filter_list(name)
    else:
        chain = [(name, amount)]

    ftypes = []
    for fname, _ in chain:
        f = color.FILTER_MAP.get(fname)
        if not f:
            raise ValueError(f"'{fname}' filter is not supported")
        ftypes.append(f)

    if space is None:
        space = ftypes[0].DEFAULT_SPACE

    for (fname, _), f in zip(chain, ftypes):
        if space not in f.ALLOWED_SPACES:
            raise ValueError(
                f"The '{fname}' only supports filtering in the {f.ALLOWED_SPACES!s} spaces, not '{space}'"
            )

    if out_space is None:
        out_space = space

    c = color.convert(space, in_place=in_place, norm=False).normalize()
    for (_, amt), f in zip(chain, ftypes):
        f.filter(c, amt, **kwargs)
    return c.convert(out_space, in_place=True)
