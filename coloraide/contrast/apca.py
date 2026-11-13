"""
APCA-W3 0.1.9 (SAPC-8, G-4g) perceptual contrast.

https://github.com/Myndex/apca-w3
"""
from __future__ import annotations
from . import ColorContrast, prepare_srgb
from ..types import AnyColor
import math
from typing import Any

# APCA 0.0.98G - 4g - W3 compatible constants
MAIN_TRC = 2.4
# sRGB coefficients
SR_CO = 0.2126729
SG_CO = 0.7151522
SB_CO = 0.0721750
# G-4g constants for use with the 2.4 exponent
NORM_BG = 0.56
NORM_TXT = 0.57
REV_TXT = 0.62
REV_BG = 0.65
# G-4g clamps and scalers
BLK_THRS = 0.022
BLK_CLMP = 1.414
SCALE_BOW = 1.14
SCALE_WOB = 1.14
LO_BOW_OFFSET = 0.027
LO_WOB_OFFSET = 0.027
DELTA_Y_MIN = 0.0005
LO_CLIP = 0.1


def srgb_to_y(color: AnyColor) -> float:
    """Convert an sRGB color to the linear Y (luminance) using the APCA simple 2.4 monitor exponent."""

    r, g, b = color.convert('srgb', norm=False).coords(nans=False)
    return (
        SR_CO * math.pow(r, MAIN_TRC) +
        SG_CO * math.pow(g, MAIN_TRC) +
        SB_CO * math.pow(b, MAIN_TRC)
    )


class APCAContrast(ColorContrast):
    """APCA-W3 0.1.9 contrast."""

    NAME = "apca"

    def contrast(self, color1: AnyColor, color2: AnyColor, **kwargs: Any) -> float:
        """Contrast."""

        # Calculate based on the colors as they are actually displayed on an sRGB screen.
        text, background = prepare_srgb(color1, color2)

        txt_y = srgb_to_y(text)
        bg_y = srgb_to_y(background)

        # Return zero on out of range input.
        if math.isnan(txt_y) or math.isnan(bg_y) or min(txt_y, bg_y) < 0.0 or max(txt_y, bg_y) > 1.1:
            return 0.0

        # Soft clamp Y for either color if it is near black.
        txt_y = txt_y if txt_y > BLK_THRS else txt_y + math.pow(BLK_THRS - txt_y, BLK_CLMP)
        bg_y = bg_y if bg_y > BLK_THRS else bg_y + math.pow(BLK_THRS - bg_y, BLK_CLMP)

        # Return zero early for an extremely low delta Y.
        if abs(bg_y - txt_y) < DELTA_Y_MIN:
            return 0.0

        if bg_y > txt_y:
            # Normal polarity: dark text on a light background (BoW), a positive value.
            sapc = (math.pow(bg_y, NORM_BG) - math.pow(txt_y, NORM_TXT)) * SCALE_BOW

            # Low contrast smooth rollout to prevent polarity reversal and a low clip for very low contrast.
            return 0.0 if sapc < LO_CLIP else (sapc - LO_BOW_OFFSET) * 100.0

        # Reverse polarity: light text on a dark background (WoB), always a negative value.
        sapc = (math.pow(bg_y, REV_BG) - math.pow(txt_y, REV_TXT)) * SCALE_WOB
        return 0.0 if sapc > -LO_CLIP else (sapc + LO_WOB_OFFSET) * 100.0
