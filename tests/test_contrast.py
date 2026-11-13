"""Test contrast."""
import unittest
from coloraide import Color
from coloraide.everything import ColorAll
from . import util


class TestLuminance(util.ColorAsserts, unittest.TestCase):
    """Test luminance cases."""

    def test_luminance(self):
        """Test luminance."""

        c1 = Color('orange')
        c2 = c1.convert('xyz-d65')
        self.assertEqual(c1.luminance(), c2.get('y'))

    def test_luminance_auto(self):
        """Test luminance auto white point."""

        c1 = Color('orange').convert('prophoto-rgb')
        self.assertCompare(c1.luminance(), c1.convert('xyz-d65').get('y'))
        self.assertCompare(c1.luminance(white=None), c1.convert('xyz-d50').get('y'))


class TestContrast(util.ColorAsserts, unittest.TestCase):
    """Test miscellaneous API features."""

    def test_bad_indirect_input(self):
        """Test bad input when it is done indirectly through a method."""

        with self.assertRaises(TypeError):
            Color("red").contrast(3)

    def test_contrast_dict(self):
        """Test contrast with a dictionary mapping."""

        self.assertEqual(
            Color('white').contrast('blue'),
            Color('white').contrast({"space": "srgb", "coords": [0, 0, 1]})
        )

    def test_bad_method(self):
        """Test bad contrast method."""

        with self.assertRaises(ValueError):
            Color('white').contrast('blue', method='bad')


class TestContrastWCAG21(util.ColorAsserts, unittest.TestCase):
    """Test WCAG 2.1 contrast ration specifics."""

    def test_contrast_one_wcag21(self):
        """Test contrast of one."""

        self.assertEqual(Color('blue').contrast('blue', method='wcag21'), 1)

    def test_contrast_bigger_wcag21(self):
        """Test greater contrast."""

        self.assertCompare(Color('white').contrast('blue', method='wcag21'), 8.59301)

    def test_symmetry(self):
        """Test symmetry."""

        self.assertEqual(
            Color('white').contrast('blue', method='wcag21'),
            Color('blue').contrast('white', method='wcag21'),
        )


class TestContrastLstar(util.ColorAsserts, unittest.TestCase):
    """Test L* contrast difference."""

    def test_contrast_same(self):
        """Test contrast of to same colors."""

        self.assertEqual(ColorAll('blue').contrast('blue', method='lstar'), 0)

    def test_contrast_bigger(self):
        """Test greater contrast."""

        self.assertCompare(ColorAll('orange').contrast('blue', method='lstar'), 42.63303)

    def test_symmetry(self):
        """Test symmetry."""

        self.assertEqual(
            ColorAll('orange').contrast('blue', method='lstar'),
            ColorAll('blue').contrast('orange', method='lstar')
        )


class TestContrastAPCA(util.ColorAsserts, unittest.TestCase):
    """Test APCA-W3 0.1.9 contrast specifics."""

    def test_black_on_white(self):
        """Test dark text on a light background."""

        self.assertCompare(Color('black').contrast('white', method='apca'), 106.04067)

    def test_white_on_black(self):
        """Test light text on a dark background is negative."""

        self.assertCompare(Color('white').contrast('black', method='apca'), -107.88473)

    def test_polarity(self):
        """Test that the polarity is preserved and the values are not symmetrical."""

        bow = Color('#888888').contrast('#ffffff', method='apca')
        wob = Color('#ffffff').contrast('#888888', method='apca')
        self.assertCompare(bow, 63.05647)
        self.assertCompare(wob, -68.54146)
        self.assertNotEqual(bow, abs(wob))

    def test_reference_values(self):
        """Test the fixed expected values from the APCA-W3 0.1.9 reference test suite."""

        pairs = [
            ('#888888', '#ffffff', 63.056469930209424),
            ('#ffffff', '#888888', -68.54146436644962),
            ('#000000', '#aaaaaa', 58.146262578561334),
            ('#aaaaaa', '#000000', -56.24113336839742),
            ('#112233', '#ddeeff', 91.66830811481631),
            ('#ddeeff', '#112233', -93.06770049484275),
            ('#112233', '#444444', 8.32326136957393),
            ('#444444', '#112233', -7.526878460278154)
        ]
        for text, background, expected in pairs:
            self.assertEqual(Color(text).contrast(background, method='apca'), expected)

    def test_same_color_zero(self):
        """Test that identical colors return zero."""

        self.assertEqual(Color('red').contrast('red', method='apca'), 0.0)
        self.assertEqual(Color('#123456').contrast('#123456', method='apca'), 0.0)

    def test_low_contrast_zero(self):
        """Test that very low contrast rolls out to zero."""

        # The Lc value falls within the low clip threshold.
        self.assertEqual(Color('#000000').contrast('#010101', method='apca'), 0.0)


class TestContrastPreparation(util.ColorAsserts, unittest.TestCase):
    """Test that all methods use the displayed sRGB color: gamut clipping and CSS alpha compositing."""

    def test_alpha_compositing_wcag21(self):
        """Test that translucent text is composited over the background before calculating WCAG 2.1."""

        self.assertCompare(
            Color('srgb', [0, 0, 0], 0.4).contrast('white', method='wcag21'),
            2.84903
        )

    def test_alpha_compositing_apca(self):
        """Test that translucent text is composited over the background before calculating APCA."""

        self.assertCompare(
            Color('srgb', [0, 0, 0], 0.4).contrast('white', method='apca'),
            54.62184
        )

    def test_alpha_compositing_lstar(self):
        """Test that translucent text is composited over the background before calculating L*."""

        self.assertCompare(
            ColorAll('srgb', [0, 0, 0], 0.4).contrast('white', method='lstar'),
            36.77741
        )

    def test_alpha_ignored_before(self):
        """Test that the old behavior of treating translucent text as opaque is gone."""

        self.assertNotEqual(
            Color('srgb', [0, 0, 0], 0.4).contrast('white', method='wcag21'),
            Color('black').contrast('white', method='wcag21')
        )

    def test_gamut_clipping_wcag21(self):
        """Test that an out of gamut color is clipped to sRGB for WCAG 2.1."""

        p3_red = Color('display-p3', [1, 0, 0], 1)
        self.assertCompare(p3_red.contrast('white', method='wcag21'), 3.99788)
        # The clipped display-p3 red is equivalent to sRGB pure red.
        self.assertEqual(
            p3_red.contrast('white', method='wcag21'),
            Color('red').contrast('white', method='wcag21')
        )

    def test_gamut_clipping_apca(self):
        """Test that an out of gamut color is clipped to sRGB for APCA."""

        p3_red = Color('display-p3', [1, 0, 0], 1)
        self.assertCompare(p3_red.contrast('white', method='apca'), 64.12622)
        self.assertEqual(
            p3_red.contrast('white', method='apca'),
            Color('red').contrast('white', method='apca')
        )

    def test_gamut_clipping_lstar(self):
        """Test that an out of gamut color is clipped to sRGB for L*."""

        p3_red = ColorAll('display-p3', [1, 0, 0], 1)
        self.assertEqual(
            p3_red.contrast('white', method='lstar'),
            ColorAll('red').contrast('white', method='lstar')
        )

    def test_inputs_not_mutated(self):
        """Test that contrast calculation never alters the provided colors."""

        text = Color('srgb', [0, 0, 0], 0.4)
        background = Color('display-p3', [1, 0, 0], 1)
        text_str = text.to_string()
        bg_str = background.to_string()
        bg_space = background.space()
        for method in ('wcag21', 'apca'):
            text.contrast(background, method=method)
            self.assertEqual(text.to_string(), text_str)
            self.assertEqual(background.to_string(), bg_str)
            self.assertEqual(background.space(), bg_space)

    def test_opaque_in_gamut_unchanged_wcag21(self):
        """Test that opaque, in gamut colors produce the same result as the direct luminance calculation."""

        text = Color('blue')
        background = Color('white')
        lum1 = max(0, text.luminance())
        lum2 = max(0, background.luminance())
        expected = (max(lum1, lum2) + 0.05) / (min(lum1, lum2) + 0.05)
        self.assertEqual(text.contrast(background, method='wcag21'), expected)
