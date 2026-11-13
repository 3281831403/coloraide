"""Test easings."""
import math
import unittest
from coloraide import Color, ease, ease_in, ease_out, ease_in_out, linear, cubic_bezier, steps, css_linear


class TestCubicBezier(unittest.TestCase):
    """Test Cubic Bezier specific cases."""

    def test_x_range(self):
        """Test that X range is constrained to 0 - 1."""

        with self.assertRaises(ValueError):
            cubic_bezier(1.2, 0, 1, 1)

        with self.assertRaises(ValueError):
            cubic_bezier(-0.2, 0, 1, 1)

        with self.assertRaises(ValueError):
            cubic_bezier(0, 0, 1.2, 1)

        with self.assertRaises(ValueError):
            cubic_bezier(0, 0, -0.2, 1)

    def test_difficult_case(self):
        """
        Previously, difficult case.

        When we used Newton's method, this required a fallback to bisect.
        We no longer use Newton's method with a fallback to bisection, so
        this case is no more difficult than any other case as we now
        use Cardano's method.
        """

        ease_in_out_expo = cubic_bezier(1.000, 0.000, 0.000, 1.000)
        self.assertEqual(ease_in_out_expo(0.43), 0.14556294236116715)

    def test_fail(self):
        """Force a failure to calculate a Bezier."""

        ease_in_out_expo = cubic_bezier(1.000, 0.000, 0.000, 1.000)
        with self.assertRaises(ValueError):
            ease_in_out_expo(math.nan)


class TestEasingMethods(unittest.TestCase):
    """Test different easing methods."""

    def ease(self, method, expected):
        """Perform easing test."""

        i = -0.5
        results = []
        while i < 1.6:
            results.append(method(i))
            i += 0.1
        self.assertTrue(all(math.isclose(a, b, rel_tol=1e-14, abs_tol=1e-15) for a, b in zip(results, expected)))

    def test_linear(self):
        """Test linear."""

        self.ease(
            linear,
            [
                -0.5,
                -0.4,
                -0.30000000000000004,
                -0.20000000000000004,
                -0.10000000000000003,
                -2.7755575615628914e-17,
                0.09999999999999998,
                0.19999999999999998,
                0.3,
                0.4,
                0.5,
                0.6,
                0.7,
                0.7999999999999999,
                0.8999999999999999,
                0.9999999999999999,
                1.0999999999999999,
                1.2,
                1.3,
                1.4000000000000001,
                1.5000000000000002
            ]
        )

    def test_ease(self):
        """Test ease."""

        self.ease(
            ease,
            [
                -0.2,
                -0.16000000000000003,
                -0.12000000000000002,
                -0.08000000000000002,
                -0.040000000000000015,
                -1.1102230246251566e-17,
                0.09479630571604325,
                0.2952443342678225,
                0.5133151609733584,
                0.6825405059781395,
                0.802403387584857,
                0.8852293098761204,
                0.94076461429764,
                0.9756253556235666,
                0.9943164774845565,
                1.0000000000000002,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
            ]
        )

    def test_ease_in(self):
        """Test ease in."""

        self.ease(
            ease_in,
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.017026609651562864,
                0.06228200013673216,
                0.12957676084535247,
                0.2148609387528933,
                0.3153568125725391,
                0.4291197692963168,
                0.5548140325286626,
                0.6916339333193126,
                0.8394278457624664,
                0.9999999999999996,
                1.172413793103448,
                1.3448275862068964,
                1.5172413793103448,
                1.6896551724137931,
                1.8620689655172415
            ]
        )

    def test_ease_out(self):
        """Test ease out."""

        self.ease(
            ease_out,
            [
                -0.8620689655172414,
                -0.6896551724137931,
                -0.517241379310345,
                -0.34482758620689663,
                -0.17241379310344834,
                -4.785444071660158e-17,
                0.16057215423753335,
                0.3083660666806867,
                0.445185967471337,
                0.5708802307036829,
                0.6846431874274607,
                0.7851390612471065,
                0.8704232391546475,
                0.9377179998632676,
                0.9829733903484368,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
            ]
        )

    def test_ease_in_out(self):
        """Test ease in/out."""

        self.ease(
            ease_in_out,
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.019722453548311168,
                0.08165985626589742,
                0.1873959067053125,
                0.33188387009764614,
                0.5,
                0.668116129902354,
                0.8126040932946875,
                0.9183401437341026,
                0.9802775464516886,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
            ]
        )


class TestSteps(unittest.TestCase):
    """Test CSS `steps()` easing against fixed sample tables."""

    def ease(self, method, expected):
        """Perform easing test."""

        i = -0.5
        results = []
        while i < 1.6:
            results.append(method(i))
            i += 0.1
        self.assertTrue(all(math.isclose(a, b, rel_tol=1e-14, abs_tol=1e-15) for a, b in zip(results, expected)))

    def test_jump_end(self):
        """Test `jump-end` (the default)."""

        self.ease(
            steps(4),
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.25,
                0.25,
                0.5,
                0.5,
                0.5,
                0.75,
                0.75,
                0.75,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
            ]
        )

    def test_jump_start(self):
        """Test `jump-start`."""

        self.ease(
            steps(4, 'jump-start'),
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.25,
                0.25,
                0.5,
                0.5,
                0.75,
                0.75,
                0.75,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
            ]
        )

    def test_jump_none(self):
        """Test `jump-none`."""

        self.ease(
            steps(3, 'jump-none'),
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.5,
                0.5,
                0.5,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
            ]
        )

    def test_jump_both(self):
        """Test `jump-both`."""

        self.ease(
            steps(2, 'jump-both'),
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1 / 3,
                1 / 3,
                1 / 3,
                1 / 3,
                2 / 3,
                2 / 3,
                2 / 3,
                2 / 3,
                2 / 3,
                2 / 3,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
            ]
        )

    def test_start_end_aliases(self):
        """Test that `start` and `end` alias `jump-start` and `jump-end`."""

        self.assertEqual(steps(1, 'start')(0.5), steps(1, 'jump-start')(0.5))
        self.assertEqual(steps(1, 'end')(0.5), steps(1, 'jump-end')(0.5))
        self.assertEqual(steps(1, 'start')(0.5), 1.0)
        self.assertEqual(steps(1, 'end')(0.5), 0.0)

    def test_underscore_position(self):
        """Test that positions with underscores are accepted."""

        self.assertEqual(steps(4, 'jump_start')(0.1), 0.25)

    def test_single_step(self):
        """Test single step behavior."""

        self.ease(
            steps(1, 'jump-start'),
            [0.0] * 6 + [1.0] * 15
        )
        self.ease(
            steps(1, 'jump-both'),
            [0.0] * 6 + [0.5] * 10 + [1.0] * 5
        )

    def test_bad_count(self):
        """Test invalid step counts."""

        with self.assertRaises(ValueError):
            steps(0)

        with self.assertRaises(ValueError):
            steps(-2)

        with self.assertRaises(ValueError):
            steps(2.5)

        with self.assertRaises(ValueError):
            steps(True)

    def test_jump_none_requires_two_steps(self):
        """Test that `jump-none` with a single step is invalid."""

        with self.assertRaises(ValueError):
            steps(1, 'jump-none')

    def test_bad_position(self):
        """Test invalid step position."""

        with self.assertRaises(ValueError):
            steps(4, 'bogus')


class TestCSSLinear(unittest.TestCase):
    """Test CSS `linear()` easing against fixed sample tables."""

    def sample(self, method, points, expected):
        """Sample the easing at the given points and compare against the expected table."""

        results = [method(t) for t in points]
        self.assertTrue(all(math.isclose(a, b, rel_tol=1e-14, abs_tol=1e-15) for a, b in zip(results, expected)))

    def test_percentage_control_point(self):
        """Test `linear(0, 0.25 75%, 1)`."""

        self.sample(
            css_linear(0, (0.25, 75), 1),
            [-0.75, 0.0, 0.375, 0.75, 0.875, 1.0, 1.5],
            [-0.25, 0.0, 0.125, 0.25, 0.625, 1.0, 2.5]
        )

    def test_evenly_spaced_points(self):
        """Test that points without positions are evenly spaced."""

        self.sample(
            css_linear(0, 0.2, 0.4, 1),
            [0.0, 1 / 6, 1 / 3, 0.5, 2 / 3, 1.0],
            [0.0, 0.1, 0.2, 0.3, 0.4, 1.0]
        )

    def test_double_position(self):
        """Test a control point with two positions, `linear(0, 0.5 25% 75%, 1)`."""

        self.sample(
            css_linear(0, (0.5, 25, 75), 1),
            [0.0, 0.125, 0.25, 0.5, 0.75, 0.875, 1.0],
            [0.0, 0.25, 0.5, 0.5, 0.5, 0.75, 1.0]
        )

    def test_out_of_order_inputs_clamped(self):
        """Test that inputs that go backwards are clamped to the largest preceding input."""

        self.sample(
            css_linear((0, 50), (0.75, 25), 1),
            [0.0, 0.4, 0.5, 0.75, 1.0, 1.5],
            [0.0, 0.0, 0.75, 0.875, 1.0, 1.25]
        )

    def test_extrapolate_shared_inputs(self):
        """Test extrapolation when the boundary points share an input."""

        # First two points share an input
        self.sample(
            css_linear((0, 25), (1, 25), 0.5),
            [-0.5, 0.25, 1.0, 1.5],
            [0.0, 1.0, 0.5, 1 / 6]
        )

        # Last two points share an input
        self.sample(
            css_linear(0, (1, 75), (0.5, 75)),
            [-0.5, 0.375, 0.75, 1.0],
            [-2 / 3, 0.5, 0.5, 0.5]
        )

    def test_single_point(self):
        """Test that a single control point always yields its output."""

        self.sample(css_linear(0.5), [-1.0, 0.0, 0.3, 1.0, 2.0], [0.5] * 5)

    def test_bare_linear(self):
        """Test that `linear(0, 1)` is equivalent to the `linear` keyword."""

        self.sample(css_linear(0, 1), [-0.2, 0.0, 0.3, 1.0, 1.4], [-0.2, 0.0, 0.3, 1.0, 1.4])

    def test_no_points(self):
        """Test that at least one control point is required."""

        with self.assertRaises(ValueError):
            css_linear()

    def test_bad_control_point(self):
        """Test malformed control points."""

        with self.assertRaises(ValueError):
            css_linear((0.5,))

        with self.assertRaises(ValueError):
            css_linear((0.5, 25, 50, 75))

        with self.assertRaises(ValueError):
            css_linear(())


class TestCSSEasingInterpolation(unittest.TestCase):
    """Test CSS easings plugged into `mix`/`interpolate` as `progress` or per-channel easings."""

    def assertColorEqual(self, color1, color2):
        """Assert two colors have equal coordinates."""

        self.assertEqual(color1.space(), color2.space())
        self.assertTrue(
            all(math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12) for a, b in zip(color1[:], color2[:])),
            f'{color1[:]} != {color2[:]}'
        )

    def test_steps_progress(self):
        """Test `steps()` as the progress of a mix."""

        self.assertColorEqual(
            Color('red').mix('blue', 0.4, space='srgb', progress=steps(4)),
            Color('red').mix('blue', 0.25, space='srgb')
        )

    def test_steps_progress_midpoint(self):
        """Test that a step landing on the linear midpoint matches the default mix."""

        self.assertColorEqual(
            Color('red').mix('blue', 0.5, space='srgb', progress=steps(4)),
            Color('red').mix('blue', 0.5, space='srgb')
        )

    def test_css_linear_progress(self):
        """Test `css_linear()` as the progress of an interpolation."""

        self.assertColorEqual(
            Color.interpolate(['red', 'blue'], space='srgb', progress=css_linear(0, (0.25, 75), 1))(0.875),
            Color.interpolate(['red', 'blue'], space='srgb')(0.625)
        )

    def test_inline_easing(self):
        """Test CSS easings injected directly in the interpolation list."""

        self.assertColorEqual(
            Color.interpolate(['red', steps(4), 'blue'], space='srgb')(0.4),
            Color.interpolate(['red', 'blue'], space='srgb')(0.25)
        )

    def test_channel_mapping(self):
        """Test CSS easings mapped to specific channels."""

        self.assertColorEqual(
            Color.interpolate(['red', 'blue'], space='srgb', progress={'r': steps(2)})(0.4),
            Color('srgb', [1, 0, 0.4])
        )

    def test_color_steps_unchanged(self):
        """Test that `Color.steps` is unaffected by the `steps` easing."""

        colors = Color.steps(['red', 'blue'], steps=3, space='srgb')
        self.assertEqual(len(colors), 3)
        self.assertColorEqual(colors[0], Color('red'))
        self.assertColorEqual(colors[2], Color('blue'))
