"""Test CSS Color 5 `color-mix()` parsing and evaluation."""
import math
import unittest
from coloraide import Color
from coloraide.everything import ColorAll
from . import util


class TestColorMix(util.ColorAsserts, unittest.TestCase):
    """Test color-mix cases."""

    def test_basic_two_colors(self):
        """Test a basic two color mix."""

        self.assertColorEqual(
            Color('color-mix(in srgb, red, blue)'),
            Color('srgb', [0.5, 0.0, 0.5])
        )

    def test_fixed_expectations(self):
        """Test fixed expected serialization values."""

        cases = [
            ('color-mix(in srgb, red, blue)', 'color(srgb 0.5 0 0.5)'),
            ('color-mix(in srgb, red 25%, blue 75%)', 'color(srgb 0.25 0 0.75)'),
            ('color-mix(in srgb, red 20%, blue)', 'color(srgb 0.2 0 0.8)'),
            ('color-mix(in srgb, red 200%, blue 100%)', 'color(srgb 0.66667 0 0.33333)'),
            ('color-mix(in srgb, red, green, blue)', 'color(srgb 0.33333 0.16732 0.33333)'),
            ('color-mix(in srgb, red 20%, green 30%, blue 50%)', 'color(srgb 0.2 0.15059 0.5)'),
            ('color-mix(in oklab, red, blue)', 'color(--oklab 0.53998 0.0962 -0.09284)'),
            ('color-mix(in oklch longer hue, red, blue)', 'color(--oklch 0.53998 0.28545 146.64)'),
            ('color-mix(in lch, white, black)', 'color(--lch 50 0 0)'),
            (
                'color-mix(in srgb, rgb(255 0 0 / .5), rgb(0 0 255 / .25))',
                'color(srgb 0.66667 0 0.33333 / 0.375)'
            ),
            (
                'color-mix(in srgb, color-mix(in srgb, red, yellow), blue)',
                'color(srgb 0.5 0.25 0.5)'
            ),
            (
                'color-mix(in display-p3, color(display-p3 1 0 0), rebeccapurple)',
                'color(display-p3 0.68683 0.10517 0.28956)'
            ),
            (
                'color-mix(in hsl shorter hue, hsl(0 100% 50%), hsl(180 100% 50%))',
                'color(--hsl 90 1 0.5)'
            ),
        ]
        for css, expected in cases:
            self.assertEqual(Color(css).to_string(color=True), expected, css)

    def test_result_stays_in_named_space(self):
        """Test the result remains in the space named after `in`."""

        self.assertEqual(Color('color-mix(in oklab, red, blue)').space(), 'oklab')
        self.assertEqual(Color('color-mix(in lch, red, blue)').space(), 'lch')
        self.assertEqual(
            Color('color-mix(in display-p3, red, blue)').space(),
            'display-p3'
        )

    def test_serialization(self):
        """Test that results serialize through the normal CSS machinery."""

        c = Color('color-mix(in oklch longer hue, red, blue)')
        self.assertEqual(c.serialize(), 'oklch(0.53998 0.28545 146.64)')
        self.assertEqual(c.to_string(color=True), 'color(--oklch 0.53998 0.28545 146.64)')

    def test_color_syntax_variants(self):
        """Test that any color syntax is accepted as a color entry."""

        cases = [
            'color-mix(in srgb, #ff0000, #0000ff)',
            'color-mix(in srgb, red, rgb(0 0 255))',
            'color-mix(in srgb, hsl(0 100% 50%), hwb(240 0% 0%))',
            'color-mix(in srgb, color(srgb 1 0 0), color(srgb 0 0 1))',
            'color-mix(in srgb, oklab(0.63 0.23 -0.16), lab(50% 50 -50))',
        ]
        for css in cases:
            self.assertIsNotNone(Color.match(css, fullmatch=True), css)

    def test_case_insensitive(self):
        """Test function and keyword casing."""

        self.assertColorEqual(
            Color('COLOR-MIX(IN SRGB, RED, BLUE)'),
            Color('color-mix(in srgb, red, blue)')
        )
        self.assertColorEqual(
            Color('Color-Mix(in Oklch Longer Hue, red, blue)'),
            Color('color-mix(in oklch longer hue, red, blue)')
        )

    def test_hue_adjusters(self):
        """Test all CSS hue interpolation methods."""

        results = {}
        for hue in ('shorter', 'longer', 'increasing', 'decreasing'):
            results[hue] = Color(f'color-mix(in oklch {hue} hue, red, blue)')

        self.assertColorEqual(results['shorter'], results['decreasing'])
        self.assertColorEqual(results['longer'], results['increasing'])
        self.assertNotEqual(results['shorter'], results['longer'])

    def test_hue_only_valid_in_polar_space(self):
        """Test hue interpolation methods are rejected for non-polar spaces."""

        for css in (
            'color-mix(in srgb shorter hue, red, blue)',
            'color-mix(in oklab increasing hue, red, blue)',
            'color-mix(in xyz-d65 longer hue, red, blue)',
        ):
            self.assertIsNone(Color.match(css, fullmatch=True), css)
            with self.assertRaises(ValueError):
                Color(css)

    def test_weight_normalization(self):
        """Test CSS weight normalization rules."""

        # No percentages -> equal weights
        self.assertColorEqual(
            Color('color-mix(in srgb, red, blue)'),
            Color('color-mix(in srgb, red 50%, blue 50%)')
        )
        # Missing percentage is filled to total 100
        self.assertColorEqual(
            Color('color-mix(in srgb, red 20%, blue)'),
            Color('color-mix(in srgb, red 20%, blue 80%)')
        )
        # Under 100 is scaled up
        self.assertColorEqual(
            Color('color-mix(in srgb, red 20%, blue 30%)'),
            Color('color-mix(in srgb, red 40%, blue 60%)')
        )
        # Over 100 is scaled down
        self.assertColorEqual(
            Color('color-mix(in srgb, red 200%, blue 100%)'),
            Color('color-mix(in srgb, red 66.6667%, blue 33.3333%)')
        )
        # A zero weight with a missing fill gives the fill color fully
        self.assertColorEqual(
            Color('color-mix(in srgb, red 0%, blue)'),
            Color('blue')
        )

    def test_invalid_weights_rejected(self):
        """Test invalid weight configurations are rejected."""

        for css in (
            'color-mix(in srgb, red 0%, blue 0%)',
            'color-mix(in srgb, red -10%, blue)',
            'color-mix(in srgb, red 120%, blue)',
            'color-mix(in srgb, red 50, blue)',
        ):
            self.assertIsNone(Color.match(css, fullmatch=True), css)

    def test_alpha_handling(self):
        """Test alpha is interpolated with premultiplied color weights."""

        c = Color('color-mix(in srgb, rgb(255 0 0 / .5), rgb(0 0 255 / .25))')
        self.assertAlmostEqual(c.alpha(), 0.375)
        # Fully transparent input still contributes via the weight on alpha
        c2 = Color('color-mix(in srgb, rgb(255 0 0 / 0), blue)')
        self.assertAlmostEqual(c2.alpha(), 0.5)

    def test_nested_calls(self):
        """Test nested color-mix calls."""

        nested = Color('color-mix(in srgb, color-mix(in srgb, red, yellow), blue)')
        self.assertColorEqual(nested, Color('srgb', [0.5, 0.25, 0.5]))

        deep = Color(
            'color-mix(in oklab, color-mix(in lch, white 30%, black) 60%, rgb(0 0 1 / .5))'
        )
        self.assertEqual(deep.space(), 'oklab')

    def test_multi_color_list(self):
        """Test mixes with more than two colors."""

        c = Color('color-mix(in srgb, red, green, blue)')
        self.assertEqual(c.space(), 'srgb')
        expected = Color.weighted_mix(
            ['red', 'green', 'blue'], [1 / 3, 1 / 3, 1 / 3], space='srgb'
        )
        self.assertColorEqual(c, expected)

        weighted = Color('color-mix(in srgb, red 20%, green 30%, blue 50%)')
        expected_w = Color.weighted_mix(
            ['red', 'green', 'blue'], [0.2, 0.3, 0.5], space='srgb'
        )
        self.assertColorEqual(weighted, expected_w)

    def test_match_offsets(self):
        """Test match start and end offsets in longer text."""

        text = 'prefix color-mix(in srgb, red 50%, blue) suffix'
        m = Color.match(text, start=7)
        self.assertIsNotNone(m)
        self.assertEqual(m.start, 7)
        self.assertEqual(text[m.start:m.end], 'color-mix(in srgb, red 50%, blue)')

    def test_match_nested_end_offset(self):
        """Test nested calls report the outer function's full span."""

        text = 'color-mix(in srgb, color-mix(in srgb, red, white), blue)TAIL'
        m = Color.match(text)
        self.assertIsNotNone(m)
        self.assertEqual(text[m.end:], 'TAIL')

    def test_fullmatch(self):
        """Test fullmatch only accepts strings consumed entirely."""

        self.assertIsNotNone(Color.match('color-mix(in srgb, red, blue)', fullmatch=True))
        self.assertIsNone(Color.match('color-mix(in srgb, red, blue) junk', fullmatch=True))
        # Without fullmatch the match ends at the closing paren
        m = Color.match('color-mix(in srgb, red, blue) junk')
        self.assertEqual(m.end, 29)

    def test_invalid_syntax(self):
        """Test malformed color-mix strings are rejected without raising."""

        invalid = [
            'color-mix()',
            'color-mix(in srgb)',
            'color-mix(in srgb, red)',
            'color-mix(in bogus, red, blue)',
            'color-mix(srgb, red, blue)',
            'color-mix(in srgb, red 50%, )',
            'color-mix(in srgb, red 50%, blue 50%',
            'color-mix(in srgb, bogusname, blue)',
            'color-mix(in srgb, red,, blue)',
            'color-mixer(in srgb, red, blue)',
            # A missing weight cannot be filled when the given weights exceed 100%
            'color-mix(in srgb, red 150%, blue)',
            # The interpolation space identifier is missing or not an identifier
            'color-mix(in, red, blue)',
            'color-mix(in 123, red, blue)',
            'color-mix(in ( red, blue)',
            # The function body opening paren is missing
            'color-mix in srgb, red, blue)',
            # The `in` keyword is missing
            'color-mix(srgb, red, blue)',
        ]
        for css in invalid:
            self.assertIsNone(Color.match(css, fullmatch=True), css)
            with self.assertRaises(ValueError):
                Color(css)

    def test_registered_space_identifier(self):
        """Test internal `--` prefixed space identifiers resolve correctly."""

        class C(Color):
            pass

        from coloraide.spaces.xyb import XYB
        C.register(XYB())
        m = C.match('color-mix(in --xyb, red, blue)', fullmatch=True)
        self.assertIsNotNone(m)
        self.assertEqual(m.color.space(), 'xyb')

    def test_coordinates_match_mix_within_tolerance(self):
        """Test color-mix coordinates match the existing mix() method within 1e-9."""

        cases = [
            ('srgb', 'red', 'blue', None),
            ('oklab', 'hsl(120 70% 50%)', '#aabbcc', None),
            ('lch', 'red', 'teal', None),
            ('oklch', 'red', 'blue', 'shorter'),
            ('oklch', 'red', 'blue', 'longer'),
            ('oklch', 'red', 'blue', 'increasing'),
            ('oklch', 'red', 'blue', 'decreasing'),
            ('hsl', 'red', 'blue', 'shorter'),
        ]
        for space, first, second, hue in cases:
            if hue is not None:
                css = f'color-mix(in {space} {hue} hue, {first}, {second})'
                reference = Color(first).mix(second, space=space, hue=hue)
            else:
                css = f'color-mix(in {space}, {first}, {second})'
                reference = Color(first).mix(second, space=space)

            result = Color(css)
            self.assertEqual(result.space(), reference.space())
            for a, b in zip(result[:], reference[:]):
                if math.isnan(a) and math.isnan(b):
                    continue
                self.assertLessEqual(abs(a - b), 1e-9, css)

    def test_percentaged_coordinates_match_mix_within_tolerance(self):
        """Test weighted color-mix matches mix() interpolation within 1e-9."""

        for percent in (0, 10, 25, 50, 75, 100):
            css = f'color-mix(in srgb, red {percent}%, blue {100 - percent}%)'
            # CSS weight of the first color maps to the complementary mix position
            reference = Color('red').mix('blue', (100 - percent) / 100, space='srgb')
            result = Color(css)
            for a, b in zip(result[:], reference[:]):
                self.assertLessEqual(abs(a - b), 1e-9, css)

    def test_colorall_support(self):
        """Test color-mix works through the ColorAll aggregate class."""

        self.assertIsNotNone(
            ColorAll.match('color-mix(in hsluv, red, blue)', fullmatch=True)
        )

    def test_parse_helper_returns_none_for_non_mix(self):
        """Test the low level parser rejects text that does not start with color-mix."""

        from coloraide.css import colormix

        self.assertIsNone(colormix.parse_color_mix(Color, 'red', 0))
        self.assertIsNone(colormix.color_mix(Color, 'rgb(1 0 0)', 0))
        # Missing opening parenthesis
        self.assertIsNone(colormix.parse_color_mix(Color, 'color-mix in srgb, red, blue)', 0))
        # The `in` keyword must be separated from the space name by whitespace
        self.assertIsNone(colormix.parse_color_mix(Color, 'color-mix(insrgb, red, blue)', 0))

    def test_space_without_color_format_is_skipped(self):
        """Test spaces that opt out of CSS formatting cannot be used as a mix space."""

        from coloraide.spaces.xyb import XYB

        class HiddenXyb(XYB):
            COLOR_FORMAT = False

        class C(Color):
            pass

        C.register(HiddenXyb())
        from coloraide.css import colormix
        self.assertIsNone(colormix.parse_color_mix(C, 'color-mix(in xyb, red, blue)', 0))
