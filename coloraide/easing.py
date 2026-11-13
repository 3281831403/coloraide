"""
Easing functions.

https://drafts.csswg.org/css-easing/#easing-functions
https://probablymarcus.com/blocks/2015/02/26/using-bezier-curves-as-easing-functions.html
https://en.wikipedia.org/wiki/Horner%27s_method
https://en.wikipedia.org/wiki/Newton%27s_method

Since we know that control points P0 and P3 are always (0, 0) and (1, 1) respectively,
we can simplify the Bezier algorithm to:

```
x(t) = x0(1 - t)3 + 3x1(1 - t)2t + 3x2(1 - t)t2 + x3t3
x'(t) = 3(1 - t)2(x1 - x0) + 6(1 - t)t(x2 - x1) + 3t2(x3 - x2)
```

Further, they can be simplified to (Horner's method).

```
x(t) = (((1 - 3x2 + 3x1)t + 3x2 - 6x1)t + 3x1)t
x'(t) = 3(1 - 3x2 + 3x1)t2 + 2(3x2 - 6x1)t + 3x1
```

This allows us to calculate coefficients:

```
cx = 3.0 * p1x;
bx = 3.0 * (p2x - p1x) - cx;
ax = 1.0 - cx - bx;
```

And end up with:

```
x(t) = axt3 + bxt2 + cxt
x'(t) = 3axt2 + 2bxt + cx
```

This greatly simplifies things and makes it faster.
"""
from __future__ import annotations
import functools
from . import algebra as alg
from collections.abc import Callable, Sequence
from typing import Any


def _bezier(a: float, b: float, c: float, y: float = 0.0) -> Callable[[float], float]:
    """
    Calculate the Bezier point.

    We know that P0 and P3 are always (0, 0) and (1, 1) respectively.
    Knowing this we can simplify the equation by precalculating them in.
    """

    return lambda x: a * x ** 3 + b * x ** 2 + c * x - y


def _solve_bezier(
    target: float,
    a: float,
    b: float,
    c: float
) -> float:
    """
    Solve curve to find a `t` that satisfies our desired `x` (target).

    The `target` is expected to be within the range of 0 - 1, this will yield a `t` within that same range.
    """

    # These Bezier curves are designed such that beyond the range 0 - 1 the response is linear,
    # so it is assumed that any values at or exceeding this range `x == t`
    if target <= 0.0 or target >= 1.0:
        return target

    roots = alg.solve_poly([a, b, c, -target])
    # Find value within range
    for r in roots:
        # Solution is well within range
        if 0 <= r <= 1:
            return r

    # We should never hit this in normal situations
    raise ValueError(f'Could not find a solution for {a}t ** 3 + {b}t ** 2 + {c} = {target}')


def _extrapolate(t: float, p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """
    Extrapolate.

    Try to use the closest tangent to the endpoint, but if we can't,
    we'll just end up returning the same `t`.
    """

    # See if we can use the tangent of a point closest to P3
    if t > 1:
        slope = 1.0

        # Use a straight line through P2 and P3
        if p2[0] < 1:
            slope = (p2[1] - 1.0) / (p2[0] - 1.0)

        # Use a straight line through P1 and P3
        elif p1[0] < 1:
            slope = (p1[1] - 1.0) / (p1[0] - 1.0)

        intercept = 1.0 - slope

    # See if we can use the tangent of a point closest to P0
    else:
        slope = 1.0

        # Use a straight line through P1 and P0
        if p1[0] > 0.0:
            slope = p1[1] / p1[0]

        # Use a straight line through P2 and P0
        elif p2[0] > 0:
            slope = p2[1] / p2[0]

        intercept = 0.0

    return slope * t + intercept


def _calc_bezier(
    target: float,
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float]
) -> float:
    """
    Calculate the y value of the bezier curve with the given `x`.

    The value given is actually the target `x`. We need to find a
    `t` that satisfies the `x` so that we can find the `y`.
    """

    # Solve for `t` in relation to `x`
    t = _solve_bezier(target, a[0], b[0], c[0])

    # Extrapolate for `y` per the spec
    if t > 1 or t < 0:
        return _extrapolate(t, p1, p2)

    # Use the found `t` to locate the `y`
    y = _bezier(a[1], b[1], c[1])(t)
    return y


def cubic_bezier(x1: float, y1: float, x2: float, y2: float) -> Callable[..., float]:
    """Return a cubic bezier easing function."""

    if x1 < 0 or x1 > 1 or x2 < 0 or x2 > 1:
        raise ValueError("Cubic Bezier requires 'x' values to be between 0 - 1")

    # Precalculate the coefficients for Horner's method
    cx = 3.0 * x1
    bx = 3.0 * (x2 - x1) - cx
    ax = 1.0 - cx - bx

    cy = 3.0 * y1
    by = 3.0 * (y2 - y1) - cy
    ay = 1.0 - cy - by

    return functools.partial(_calc_bezier, a=(ax, ay), b=(bx, by), c=(cx, cy), p1=(x1, y1), p2=(x2, y2))


def linear(t: float) -> float:
    """Linear."""

    return t


def _steps(t: float, count: int, position: str) -> float:
    """
    Step easing.

    https://drafts.csswg.org/css-easing/#step-easing-functions

    The domain `[-inf, inf]` is divided into segments: `[-inf, 0)` has the value 0
    and `[1, inf]` has the value 1. `[0, 1)` is divided into `count` half-open
    intervals whose values are assigned per the step position. At the boundary
    between intervals, the associated value is the higher value.
    """

    if t < 0.0:
        return 0.0

    if t >= 1.0:
        return 1.0

    # Locate the half-open interval within `[0, 1)` (`t` is non-negative, so `int` floors)
    i = int(t * count)

    if position == 'jump-start':
        return (i + 1) / count

    if position == 'jump-none':
        return i / (count - 1)

    if position == 'jump-both':
        return (i + 1) / (count + 1)

    # jump-end
    return i / count


def steps(count: int, position: str = 'jump-end') -> Callable[..., float]:
    """
    CSS `steps()` easing function.

    https://drafts.csswg.org/css-easing/#step-easing-functions

    `start` and `end` are aliases of `jump-start` and `jump-end` respectively.
    `jump-none` requires at least 2 steps as it renders both `0` and `1`.
    """

    if isinstance(count, bool) or int(count) != count:
        raise ValueError(f"Step count must be an integer, not '{count}'")

    count = int(count)
    position = position.replace('_', '-')
    if position == 'start':
        position = 'jump-start'
    elif position == 'end':
        position = 'jump-end'

    if position not in ('jump-start', 'jump-end', 'jump-none', 'jump-both'):
        raise ValueError(f"Unknown step position '{position}'")

    if count < 1 or (position == 'jump-none' and count < 2):
        raise ValueError(f"Step position '{position}' requires at least {2 if position == 'jump-none' else 1} step(s)")

    return functools.partial(_steps, count=count, position=position)


def _css_linear(t: float, points: list[tuple[float, float]]) -> float:
    """
    CSS `linear()` easing function.

    https://drafts.csswg.org/css-easing/#linear-easing-functions

    Control points are `(input, output)` pairs with monotonically non-decreasing
    inputs. Progress between points is linearly interpolated; outside the range
    of defined inputs, the trajectory of the nearest two points is extrapolated.
    """

    if len(points) == 1:
        return points[0][1]

    # If the input matches at least one control point, use the last such point
    result = None
    for p_in, p_out in points:
        if p_in == t:
            result = p_out
    if result is not None:
        return result

    if t < points[0][0]:
        # Extrapolate using the first two points
        a, b = points[0], points[1]
        if a[0] == b[0]:
            return a[1]
    elif t > points[-1][0]:
        # Extrapolate using the last two points
        a, b = points[-2], points[-1]
        if a[0] == b[0]:
            return b[1]
    else:
        # `a` is the last point with an input below `t`, `b` the first with an input above `t`
        a = points[0]
        b = points[-1]
        for i in range(len(points) - 1):
            if points[i][0] < t < points[i + 1][0]:
                a, b = points[i], points[i + 1]
                break

    return a[1] + (b[1] - a[1]) * ((t - a[0]) / (b[0] - a[0]))


def css_linear(*args: float | Sequence[float]) -> Callable[..., float]:
    """
    CSS `linear()` easing function.

    https://drafts.csswg.org/css-easing/#linear-easing-functions

    Each argument is either an output value whose input position is resolved
    automatically, or a sequence of `(value, *percentages)` where one or two
    percentage positions (0 - 100) create one or two control points at the
    given input position(s), e.g. `linear(0, 0.25 75%, 1)` translates to
    `css_linear(0, (0.25, 75), 1)`.
    """

    if not args:
        raise ValueError("'linear()' requires at least one control point")

    points: list[list[Any]] = []
    for arg in args:
        if isinstance(arg, Sequence) and not isinstance(arg, (str, bytes)):
            if not 2 <= len(arg) <= 3:
                raise ValueError("Control points require a value with 1 - 2 percentage positions")
            value, pcts = arg[0], arg[1:]
            points.extend([pct / 100, value] for pct in pcts)
        else:
            points.append([None, arg])

    # If the first and/or last control point lacks an input, default them to 0 and 1
    if points[0][0] is None:
        points[0][0] = 0.0
    if points[-1][0] is None:
        points[-1][0] = 1.0

    # Inputs must be monotonically non-decreasing, clamp inputs that go backwards
    largest = points[0][0]
    for p in points:
        if p[0] is not None:
            if p[0] < largest:
                p[0] = largest
            else:
                largest = p[0]

    # Evenly space runs of points with unspecified inputs between their neighbors
    index = 0
    total = len(points)
    while index < total:
        if points[index][0] is None:
            end = index
            while points[end][0] is None:
                end += 1
            start_in = points[index - 1][0]
            size = end - index + 1
            for k in range(index, end):
                points[k][0] = start_in + (points[end][0] - start_in) * (k - index + 1) / size
            index = end
        else:
            index += 1

    return functools.partial(_css_linear, points=[(p[0], p[1]) for p in points])


# CSS Easings Level 2
ease = cubic_bezier(0.25, 0.1, 0.25, 1.0)
ease_in = cubic_bezier(0.42, 0.0, 1.0, 1.0)
ease_out = cubic_bezier(0.0, 0.0, 0.58, 1.0)
ease_in_out = cubic_bezier(0.42, 0.0, 0.58, 1.0)
