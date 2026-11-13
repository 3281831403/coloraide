"""Contrast."""
from __future__ import annotations
from abc import ABCMeta, abstractmethod
from ..types import Plugin, AnyColor
from typing import Any


class ColorContrast(Plugin, metaclass=ABCMeta):
    """Color contrast plugin class."""

    NAME = ''

    @abstractmethod
    def contrast(self, color1: AnyColor, color2: AnyColor, **kwargs: Any) -> float:
        """Get the contrast of the two provided colors."""


def prepare_srgb(text: AnyColor, background: AnyColor) -> tuple[AnyColor, AnyColor]:
    """
    Prepare colors for contrast calculation.

    Contrast is calculated based on what is actually displayed on screen. Therefore, both colors are first fitted to
    the sRGB gamut by clipping, as out of gamut colors cannot be displayed on an sRGB screen. Then, any transparency in
    the text (foreground) color is alpha composited over the opaque background per the CSS compositing rules.

    Opaque colors that are already in the sRGB gamut are returned untouched so that existing, in-gamut results are
    numerically identical.
    """

    # Fast path: nothing is out of gamut or transparent, so no adjustments are needed.
    if (
        text.alpha(nans=False) == 1.0 and
        background.alpha(nans=False) == 1.0 and
        text.in_gamut('srgb', tolerance=0) and
        background.in_gamut('srgb', tolerance=0)
    ):
        return text, background

    # Fit both colors to the sRGB gamut by clipping to what a screen can actually display.
    text = text.clone().convert('srgb', norm=False).clip()
    background = background.clone().convert('srgb', norm=False).clip()

    # Composite the text over the background per CSS alpha compositing rules when the text has transparency.
    if text.alpha(nans=False) != 1.0:
        text = text.layer([text, background])

    return text, background


def contrast(name: str | None, color1: AnyColor, color2: AnyColor, **kwargs: Any) -> float:
    """Get the appropriate contrast plugin."""

    if name is None:
        name = color1.CONTRAST

    method = color1.CONTRAST_MAP.get(name)
    if not method:
        raise ValueError(f"'{name}' contrast method is not supported")

    return method.contrast(color1, color2, **kwargs)
