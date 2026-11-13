"""
Test CSS Color 5 relative color syntax (`from`).

W3C WPT cross-check sources: color-computed-relative-color.html,
color-valid-relative-color.html, color-invalid-relative-color.html and
relative-color-out-of-gamut.html under css/css-color/parsing/.
Each valid entry is `(relative string, target space, expected coords, expected alpha)`;
coords use the native scale and `NaN` marks a missing channel.
"""
import math
import unittest
from . import util
from coloraide import Color, NaN
import pytest


# Native-space expected values cross-checked against WPT computed values.
RELATIVE_COLORS = [
    # ---------------------------------------------------------------- rgb
    # Identity inheritance from a named color.
    ('rgb(from rebeccapurple r g b)', 'srgb', [0.4, 0.2, 0.6], 1.0),
    # Inheritance of the origin alpha through the `alpha` keyword.
    ('rgb(from rgb(20%, 40%, 60%, 80%) r g b / alpha)', 'srgb', [0.2, 0.4, 0.6], 0.8),
    ('rgb(from hsl(120deg 20% 50% / .5) r g b / alpha)', 'srgb', [0.4, 0.6, 0.4], 0.5),
    # Channel reordering.
    ('rgb(from rebeccapurple g b r)', 'srgb', [0.2, 0.6, 0.4], 1.0),
    ('rgb(from red b g r)', 'srgb', [0.0, 0.0, 1.0], 1.0),
    # Numeric replacement (0-255 scale).
    ('rgb(from rebeccapurple 0 0 0)', 'srgb', [0.0, 0.0, 0.0], 1.0),
    ('rgb(from rebeccapurple 25 g b / alpha)', 'srgb', [25 / 255, 0.2, 0.6], 1.0),
    # Percent replacement.
    ('rgb(from rebeccapurple 20% g b / alpha)', 'srgb', [0.2, 0.2, 0.6], 1.0),
    ('rgb(from rebeccapurple r g b / 20%)', 'srgb', [0.4, 0.2, 0.6], 0.2),
    # A channel keyword reused for every channel and as alpha.
    ('rgb(from rebeccapurple r r r / r)', 'srgb', [0.4, 0.4, 0.4], 0.4),
    # The `alpha` keyword in a channel position resolves to origin alpha on the 0-255 scale.
    ('rgb(from rebeccapurple alpha alpha alpha / alpha)', 'srgb',
     [1 / 255, 1 / 255, 1 / 255], 1.0),
    ('rgb(from rebeccapurple b alpha r / g)', 'srgb', [0.6, 1 / 255, 0.4], 0.2),
    ('rgb(from rgb(20%, 40%, 60%, 80%) b alpha r / g)', 'srgb',
     [0.6, 0.8 / 255, 0.2], 0.4),
    # Mixed keyword, percent and number.
    ('rgb(from rebeccapurple r 20% 10)', 'srgb', [0.4, 0.2, 10 / 255], 1.0),
    # `none` channels and alpha.
    ('rgb(from rebeccapurple none none none)', 'srgb', [NaN, NaN, NaN], 1.0),
    ('rgb(from rebeccapurple r g none)', 'srgb', [0.4, 0.2, NaN], 1.0),
    ('rgb(from rebeccapurple r g b / none)', 'srgb', [0.4, 0.2, 0.6], NaN),
    ('rgb(from rgb(none none none / none) r g b / alpha)', 'srgb',
     [NaN, NaN, NaN], NaN),
    # Out-of-gamut values are not clamped (relative colors preserve the computed value).
    ('rgb(from lab(100 104.3 -50.9) r g b)', 'srgb', [1.5935, 0.58776, 1.40555], 1.0),
    ('rgb(from lab(0 104.3 -50.9) r g b)', 'srgb', [0.35137, -0.21392, 0.29945], 1.0),
    ('rgb(from lch(100 116 334) r g b)', 'srgb', [1.59336, 0.58802, 1.40517], 1.0),
    ('rgb(from oklab(1 0.365 -0.16) r g b)', 'srgb', [1.59297, 0.3602, 1.38555], 1.0),
    ('rgb(from oklab(0 0.365 -0.16) r g b)', 'srgb', [0.07636, -0.04559, 0.09322], 1.0),
    ('rgb(from oklch(1 0.399 336.3) r g b)', 'srgb', [1.59331, 0.35856, 1.38647], 1.0),
    ('rgb(from oklch(0 0.399 336.3) r g b)', 'srgb', [0.07651, -0.04579, 0.0937], 1.0),
    ('rgb(from color(display-p3 0 1 0) r g b / alpha)', 'srgb',
     [-0.5116, 1.01827, -0.31067], 1.0),

    # ---------------------------------------------------------------- hsl
    ('hsl(from rebeccapurple h s l)', 'hsl',
     Color('rebeccapurple').convert('hsl').coords(), 1.0),
    ('hsl(from rebeccapurple 0 s l / alpha)', 'hsl', [0.0, 0.5, 0.4], 1.0),
    ('hsl(from rebeccapurple h 0% l / alpha)', 'hsl', [270.0, 0.0, 0.4], 1.0),
    ('hsl(from rebeccapurple h s 0% / alpha)', 'hsl', [270.0, 0.5, 0.0], 1.0),
    # Origin alpha used as a (scaled 0-100) channel and a channel keyword used as alpha.
    ('hsl(from rebeccapurple h alpha l / s)', 'hsl', [270.0, 0.01, 0.4], 0.5),
    ('hsl(from rebeccapurple none none none)', 'hsl', [NaN, NaN, NaN], 1.0),
    ('hsl(from rebeccapurple 0.5turn s l)', 'hsl', [180.0, 0.5, 0.4], 1.0),

    # ---------------------------------------------------------------- hwb
    ('hwb(from rebeccapurple h w b)', 'hwb', [270.0, 0.2, 0.4], 1.0),
    ('hwb(from rebeccapurple h b w)', 'hwb', [270.0, 0.4, 0.2], 1.0),
    ('hwb(from rebeccapurple h alpha w / b)', 'hwb', [270.0, 0.01, 0.2], 0.4),
    ('hwb(from rebeccapurple h w w / w)', 'hwb', [270.0, 0.2, 0.2], 0.2),
    ('hwb(from rebeccapurple none w b / alpha)', 'hwb', [NaN, 0.2, 0.4], 1.0),

    # ---------------------------------------------------------------- lab
    ('lab(from lab(25 20 50) l a b)', 'lab', [25.0, 20.0, 50.0], 1.0),
    ('lab(from lab(25 20 50 / 40%) l a b / alpha)', 'lab', [25.0, 20.0, 50.0], 0.4),
    ('lab(from lab(25 20 50) 0 a b / alpha)', 'lab', [0.0, 20.0, 50.0], 1.0),
    ('lab(from lab(25 20 50) l 0 b / alpha)', 'lab', [25.0, 0.0, 50.0], 1.0),
    ('lab(from lab(25 20 50) l a 0 / alpha)', 'lab', [25.0, 20.0, 0.0], 1.0),
    ('lab(from color(display-p3 0 0 0) l a b / alpha)', 'lab', [0.0, 0.0, 0.0], 1.0),
    # Origin conversion from a different space.
    ('lab(from red l a b)', 'lab', Color('red').convert('lab').coords(), 1.0),

    # ---------------------------------------------------------------- lch
    ('lch(from lch(0.7 45 30) l c h)', 'lch', [0.7, 45.0, 30.0], 1.0),
    ('lch(from lch(0.7 45 30 / 40%) l c h / alpha)', 'lch', [0.7, 45.0, 30.0], 0.4),
    ('lch(from blue l c h)', 'lch', Color('blue').convert('lch').coords(), 1.0),

    # ---------------------------------------------------------------- oklab
    ('oklab(from oklab(0.25 0.2 0.5) l a b)', 'oklab', [0.25, 0.2, 0.5], 1.0),
    ('oklab(from oklab(0.25 0.2 0.5 / 40%) l a b / alpha)', 'oklab',
     [0.25, 0.2, 0.5], 0.4),
    ('oklab(from oklab(0.25 0.2 0.5) l b a)', 'oklab', [0.25, 0.5, 0.2], 1.0),
    ('oklab(from oklab(0.25 0.2 0.5) l a none)', 'oklab', [0.25, 0.2, NaN], 1.0),
    # Origin alpha used as a (non-scaled) lab/oklab channel keeps the 0-1 fraction.
    ('lab(from lab(25 20 50 / 40%) alpha a b)', 'lab', [0.4, 20.0, 50.0], 1.0),
    ('oklab(from oklab(0.25 0.2 0.5 / 40%) l alpha b)', 'oklab', [0.25, 0.4, 0.5], 1.0),
    # A channel keyword in the slash position inherits that channel's value as alpha.
    ('oklab(from oklab(0.25 0.2 0.5) l a b / l)', 'oklab', [0.25, 0.2, 0.5], 0.25),

    # ---------------------------------------------------------------- oklch
    ('oklch(from blue l c h)', 'oklch', Color('blue').convert('oklch').coords(), 1.0),
    ('oklch(from blue l 0.1 h)', 'oklch',
     [Color('blue').convert('oklch')['l'], 0.1, Color('blue').convert('oklch')['h']], 1.0),

    # ---------------------------------------------------------------- nesting
    ('rgb(from rgb(from rebeccapurple r g b) r g b)', 'srgb', [0.4, 0.2, 0.6], 1.0),
    ('lab(from rgb(from red r g b) l a b)', 'lab',
     Color('red').convert('lab').coords(), 1.0),
    ('hwb(from hwb(from rebeccapurple h w b) h w b)', 'hwb', [270.0, 0.2, 0.4], 1.0),

    # ---------------------------------------------------------------- origin forms
    ('rgb(from #663399 r g b)', 'srgb', [0.4, 0.2, 0.6], 1.0),
    ('rgb(from color(srgb 0.4 0.2 0.6) r g b)', 'srgb', [0.4, 0.2, 0.6], 1.0),
]

# Relative color strings that must be rejected (cross-checked with WPT invalid cases).
INVALID_RELATIVE_COLORS = [
    # Legacy comma syntax cannot use `from`.
    'rgb(from rebeccapurple, r, g, b)',
    'hsl(from rebeccapurple, h, s, l)',
    # Legacy function names (rgba/hsla) do not support relative syntax.
    'rgba(from rgb(10%, 20%, 30%, 40%), r, g, b, alpha)',
    'hsla(from rgb(10%, 20%, 30%, 40%), h, s, l, alpha)',
    # Angles are not valid for non-hue channels.
    'rgb(from rebeccapurple r 10deg 10)',
    'rgb(from rebeccapurple r 10 10deg)',
    'rgb(from rebeccapurple 10deg g b)',
    # Unknown / out-of-space keywords.
    'rgb(from rebeccapurple red g b)',
    'rgb(from rebeccapurple l g b)',
    'rgb(from rebeccapurple h g b)',
    'rgb(from rebeccapurple x g b)',
    'hsl(from rebeccapurple hue s l)',
    'hsl(from rebeccapurple x s l)',
    'hsl(from rebeccapurple h g b)',
    'hwb(from rebeccapurple hue w b)',
    'hwb(from rebeccapurple h g b)',
    # Percent is not valid on the hue channel of cylindrical spaces.
    'hsl(from rebeccapurple 10% s l)',
    'hwb(from rebeccapurple 10% w b)',
    # `alpha` outside a relative color is meaningless.
    'rgb(0 0 0 / alpha)',
    # Wrong channel count.
    'rgb(from red r g)',
    'rgb(from red r g b b)',
    'oklch(from blue l c)',
    'hwb(from red h w)',
    # Dangling slash.
    'oklch(from blue l c h /)',
    # Missing `from` / origin / channels.
    'rgb(red r g b)',
    'rgb(from)',
    'rgb(from red)',
    # The generic `color()` function does not define relative syntax.
    'color(from srgb r g b)',
    # Spaces outside the CSS Color 5 set do not support relative syntax.
    'jzazbz(from red z iz az)',
    # Bad origin color.
    'rgb(from nosuchcolor r g b)',
    # A 4th channel without a slash.
    'rgb(from red r g b r)',
    # Malformed `from` clause: missing origin or missing whitespace.
    'rgb(from)',
    'rgb(fromred r g b)',
    'rgb(from  r g b)',
    # Unrecognized keyword in a lab family function.
    'lab(from lab(25 20 50) x a b)',
    'oklch(from blue l c 50%)',
    # A degree value is not valid on a non-hue channel.
    'lab(from lab(25 20 50) 10deg a b)',
    'lch(from lch(50 40 90) l 10deg h)',
]


class TestRelativeColors(util.ColorAssertsPyTest):
    """Test relative color parsing against CSS Color 5 expectations."""

    @pytest.mark.parametrize('string,space,coords,alpha', RELATIVE_COLORS)
    def test_relative_colors(self, string, space, coords, alpha):
        """Test valid relative colors resolve to the expected native coordinates."""

        color = Color(string)
        self.assertEqual(color.space(), space)

        for index, expected in enumerate(coords):
            actual = color[index]
            if math.isnan(expected):
                assert math.isnan(actual), f"channel {index} expected NaN, got {actual}"
            else:
                self.assertCompare(actual, expected, 5)

        if math.isnan(alpha):
            assert math.isnan(color[-1]), f"alpha expected NaN, got {color[-1]}"
        else:
            self.assertCompare(color[-1], alpha, 5)

    @pytest.mark.parametrize('string', INVALID_RELATIVE_COLORS)
    def test_invalid_relative_colors(self, string):
        """Test invalid relative colors raise a value error."""

        with pytest.raises(ValueError):
            Color(string)

    def test_relative_equals_manual_conversion(self):
        """Inheriting every channel is equivalent to converting the origin to the space."""

        for func, space in [
            ('rgb', 'srgb'),
            ('hsl', 'hsl'),
            ('hwb', 'hwb'),
            ('lab', 'lab'),
            ('lch', 'lch'),
            ('oklab', 'oklab'),
            ('oklch', 'oklch')
        ]:
            channels = ' '.join(str(c) for c in Color.CS_MAP[space].CHANNELS)
            relative = Color(f'{func}(from blue {channels})')
            converted = Color('blue').convert(space)
            self.assertEqual(relative, converted)

    def test_relative_default_alpha_is_one(self):
        """Without a slash the resulting alpha defaults to one, even if the origin has alpha."""

        self.assertEqual(Color('rgb(from rgb(1 2 3 / 0.4) r g b)')[-1], 1.0)

    def test_relative_none_in_origin_propagates(self):
        """A `none` (NaN) origin channel is inherited as NaN."""

        color = Color('rgb(from rgb(none none none) r g b)')
        assert all(math.isnan(value) for value in color.coords())

    def test_relative_keyword_case_insensitive(self):
        """Function, `from` and channel keywords are case insensitive."""

        assert Color('RGB(FROM red R G B)') == Color('rgb(from red r g b)')


class TestRelativeColorMatch(unittest.TestCase):
    """Test `Color.match` offset handling for relative colors."""

    def test_match_offset(self):
        """Test match offsets for a relative color embedded in a buffer."""

        text = 'yellow green oklch(from blue l c h) rgb(1 0 0)'
        fragment = 'oklch(from blue l c h)'
        match = Color.match(text, start=13)
        self.assertIsNotNone(match)
        self.assertEqual(match.start, 13)
        self.assertEqual(match.end, 13 + len(fragment))
        self.assertEqual(match.color, Color('blue').convert('oklch'))

    def test_match_nested_offset(self):
        """Test offsets for nested relative colors."""

        fragment = 'lab(from rgb(from red r g b) l a b)'
        text = f'xx {fragment} tail'
        match = Color.match(text, start=3)
        self.assertIsNotNone(match)
        self.assertEqual(match.start, 3)
        self.assertEqual(match.end, 3 + len(fragment))

    def test_fullmatch(self):
        """Test full match requirement."""

        self.assertIsNotNone(Color.match('rgb(from red r g b)', fullmatch=True))
        self.assertIsNone(Color.match('rgb(from red r g b) junk', fullmatch=True))
        self.assertIsNotNone(Color.match('rgb(from red r g b) junk'))


class TestRelativeColorSubclass(unittest.TestCase):
    """Relative colors resolve through the Color subclass doing the parsing."""

    def test_subclass_relative(self):
        """Test relative colors work for Color subclasses."""

        class Custom(Color):
            pass

        color = Custom('oklch(from blue l c h)')
        self.assertIs(type(color), Custom)
        self.assertEqual(color, Custom('blue').convert('oklch'))

        nested = Custom('rgb(from oklch(from blue l c h) r g b)')
        self.assertIs(type(nested), Custom)
