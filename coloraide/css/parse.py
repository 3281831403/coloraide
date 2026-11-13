"""Parse utilities."""
from __future__ import annotations
import re
import math
from .. import algebra as alg
from ..types import Vector
from . import color_names
from ..channels import Channel, FLG_ANGLE, ANGLE_DEG
from typing import TYPE_CHECKING, Any
import functools

if TYPE_CHECKING:  # pragma: no cover
    from ..spaces import Space

RGB_CHANNEL_SCALE = 1.0 / 255.0
SCALE_PERCENT = 1 / 100.0
MAX_CHANNELS = 16

CONVERT_TURN = 360
CONVERT_GRAD = 90 / 100
CONVERT_RAD = 180 / math.pi

RE_HEX = re.compile(r'(?i)(\#)((?:[a-f0-9]{6}(?:[a-f0-9]{2})?|[a-f0-9]{3}(?:[a-f0-9])?))\b')
RE_NAME = re.compile(r'(?i)\b([a-z]{3,})\b')
RE_IDENT = re.compile(r'(?i)(-{0,2}[a-z][-a-z0-9_]*)')
RE_SPACE = re.compile(r'(\s+)')
RE_LOOSE_SPACE = re.compile(r'(\s*)')
RE_FROM = re.compile(r'(?i)(from)(?=\s+)')
RE_CHANNEL = re.compile(
    r'(?i)((?:[+\-]?(?:[0-9]*\.)?[0-9]+(?:e[-+]?[0-9]+)?))(?:(%)|(deg|rad|turn|grad))?|(none)|(alpha(?![-a-z0-9_]))|([a-z][-a-z0-9_]*)'
)
RE_FUNC_START = re.compile(r'(\()\s*')
RE_FUNC_END = re.compile(r'\s*(\))')
RE_COMMA = re.compile(r'\s*(,)\s*')
RE_SLASH = re.compile(r'\s*(/)\s*')
RE_CSS_FUNC = re.compile(r'\b(color|rgba?|hsla?|hwb|(?:ok)?lab|(?:ok)?lch|jzazbz|jzczhz|ictcp)\b')

# CSS Color 5 relative color syntax is only defined for modern (non-legacy) functions.
RELATIVE_FUNCS = frozenset(('rgb', 'hsl', 'hwb', 'lab', 'lch', 'oklab', 'oklch'))

# Channel keywords that may be inherited from the origin color, keyed by function name.
# The standalone `alpha` keyword is tokenized separately and may appear in any position.
RE_CHANNEL_KEYWORDS = {
    'rgb': frozenset(('r', 'g', 'b')),
    'hsl': frozenset(('h', 's', 'l')),
    'hwb': frozenset(('h', 'w', 'b')),
    'lab': frozenset(('l', 'a', 'b')),
    'lch': frozenset(('l', 'c', 'h')),
    'oklab': frozenset(('l', 'a', 'b')),
    'oklch': frozenset(('l', 'c', 'h'))
}


def norm_float(string: str) -> float:
    """Normalize a float value."""

    if string == "none":
        return math.nan
    return float(string)


def norm_hex_channel(string: str) -> float:
    """Normalize the hex string to a form we can handle."""

    return int(string, 16) * RGB_CHANNEL_SCALE


def norm_percent_channel(string: str, scale: float = 100, offset: float = 0.0) -> float:
    """Normalize percent channel."""

    if string == 'none':  # pragma: no cover
        return norm_float(string)
    elif string.endswith('%'):
        value = norm_float(string[:-1])
        return (value * scale * 0.01) - offset if scale != 100 else value
    else:  # pragma: no cover
        # Should only occur internally if we are doing something wrong.
        raise ValueError(f"Unexpected value '{string}'")


def norm_color_channel(string: str, scale: float = 1, offset: float = 0.0) -> float:
    """Normalize percent/number channel."""

    if string.endswith('%'):
        return norm_percent_channel(string, scale, offset)
    else:
        return norm_float(string)


def norm_scaled_color_channel(string: str, scale: float = 1, offset: float = 0.0) -> float:
    """Normalize scaled percent/number channel."""

    if string.endswith('%'):
        return norm_percent_channel(string, scale, offset)
    else:
        value = norm_float(string)
        return (value * scale * 0.01) - offset if scale != 100 else value


def norm_rgb_channel(string: str, scale: float = 1) -> float:
    """Normalize RGB channel."""

    if string.endswith("%"):
        return norm_percent_channel(string, scale)
    else:
        return norm_float(string) * RGB_CHANNEL_SCALE


def norm_alpha_channel(string: str) -> float:
    """Normalize alpha channel."""

    if string.endswith("%"):
        value = norm_percent_channel(string, 1)
    else:
        value = norm_float(string)
    return alg.clamp(value, 0.0, 1.0)


def norm_angle_channel(angle: str) -> float:
    """Normalize angle units."""

    if angle.endswith('turn'):
        value = norm_float(angle[:-4]) * CONVERT_TURN
    elif angle.endswith('grad'):
        value = norm_float(angle[:-4]) * CONVERT_GRAD
    elif angle.endswith('rad'):
        value = norm_float(angle[:-3]) * CONVERT_RAD
    elif angle.endswith('deg'):
        value = norm_float(angle[:-3])
    else:
        value = norm_float(angle)
    return value


def parse_hex(color: str) -> tuple[Vector, float]:
    """Parse hexadecimal color."""

    length = len(color)
    if length in (7, 9):
        return (
            [
                norm_hex_channel(color[1:3]),
                norm_hex_channel(color[3:5]),
                norm_hex_channel(color[5:7])
            ],
            norm_hex_channel(color[7:9]) if length == 9 else 1.0
        )
    else:
        return (
            [
                norm_hex_channel(color[1] * 2),
                norm_hex_channel(color[2] * 2),
                norm_hex_channel(color[3] * 2)
            ],
            norm_hex_channel(color[4] * 2) if length == 5 else 1.0
        )


def parse_rgb_channels(color: list[str], boundry: tuple[Channel, ...]) -> tuple[Vector, float]:
    """Parse CSS RGB format."""

    channels = []
    alpha = 1.0
    for i, c in enumerate(color, 0):
        c = c.lower()
        if i <= 2:
            channels.append(norm_rgb_channel(c, boundry[i].high))
        elif i == 3:
            alpha = norm_alpha_channel(c)
    return channels, alpha


def parse_channels(color: list[str], boundry: tuple[Channel, ...], scaled: bool = False) -> tuple[Vector, float]:
    """Parse CSS channel format."""

    channels = []
    alpha = 1.0
    length = len(boundry)
    for i, c in enumerate(color, 0):
        c = c.lower()
        if i < length:
            bound = boundry[i]
            if bound.flags & FLG_ANGLE:
                v = norm_angle_channel(c)
                channels.append(v * (bound.high / 360) if bound.angle != ANGLE_DEG else v)
            elif scaled:
                channels.append(norm_scaled_color_channel(c, bound.high))
            else:
                channels.append(norm_color_channel(c, bound.high))
        elif i == length:
            alpha = norm_alpha_channel(c)
    return channels, alpha


def parse_color(tokens: dict[str, Any], space: Space) -> tuple[Vector, float] | None:
    """Parse the color function."""

    # Iterate the spaces and see if we find the color serialization identifier
    num_channels = len(space.CHANNELS)
    values = len(tokens['func']['values'])

    if tokens['func']['slash']:
        values -= 1

    if values != num_channels:
        return None

    alpha = norm_alpha_channel(tokens['func']['values'][-1]['value'].lower()) if tokens['func']['slash'] else 1.0

    channels = []
    properties = space.CHANNELS
    for i in range(num_channels):
        entry = tokens['func']['values'][i]
        c = entry['value'].lower()
        channel = properties[i]
        if entry['type'] == 'degree':
            if not (channel.flags & FLG_ANGLE):
                return None
            v = norm_angle_channel(c)
            channels.append(v * (channel.high / 360) if channel.angle != ANGLE_DEG else v)
        else:
            channels.append(norm_color_channel(c, channel.span, channel.offset))
    return (channels, alpha)


def validate_color(tokens: dict[str, Any]) -> bool:
    """Validate the color function syntax."""

    return True


def validate_srgb(tokens: dict[str, Any]) -> bool:
    """Validate the RGB color functions."""

    length = len(tokens['func']['values'])
    delimiter = tokens['func']['delimiter']
    relative = tokens['func']['relative']

    if length < 3 or length > 4:
        return False
    vtype = tokens['func']['values'][0]['type']
    if relative:
        # Relative colors only use the space separated syntax, keywords may be mixed freely.
        return bool(delimiter == 'space' and (length == 4) == tokens['func']['slash'])
    if delimiter == 'comma':
        if vtype in ('none', 'degree') or not all(v['type'] == vtype for v in tokens['func']['values'][:3]):
            return False
        if length == 4 and tokens['func']['values'][3]['type'] in ('none', 'degree'):
            return False
    else:
        if any(v['type'] == 'degree' for v in tokens['func']['values']):
            return False
        if (length == 4) != tokens['func']['slash']:
            return False
    return True


def validate_cylindrical_srgb(tokens: dict[str, Any]) -> bool:
    """Validate cylindrical sRGB."""

    length = len(tokens['func']['values'])
    delimiter = tokens['func']['delimiter']
    func_name = tokens['func']['name']
    relative = tokens['func']['relative']

    if length < 3 or length > 4:
        return False

    if func_name == 'hwb' and delimiter == 'comma':
        return False

    if relative:
        # Relative colors only use the space separated syntax, keywords may be mixed freely.
        return bool(delimiter == 'space' and (length == 4) == tokens['func']['slash'])

    if delimiter == 'comma':
        if tokens['func']['values'][0]['type'] not in ('degree', 'number'):
            return False
        if not all(v['type'] == 'percent' for v in tokens['func']['values'][1:3]):
            return False
        if length == 4 and tokens['func']['values'][3]['type'] in ('none', 'degree'):
            return False
    else:
        if tokens['func']['values'][0]['type'] == 'percent':
            return False
        if any(v['type'] == 'degree' for v in tokens['func']['values'][1:]):
            return False

        if (length == 4) != tokens['func']['slash']:
            return False
    return True


def validate_lab(tokens: dict[str, Any]) -> bool:
    """Validate CSS Lab variant color spaces."""

    length = len(tokens['func']['values'])
    delimiter = tokens['func']['delimiter']
    relative = tokens['func']['relative']

    if delimiter == 'comma':
        return False

    if length < 3 or length > 4:
        return False

    if not relative and any(v['type'] == 'degree' for v in tokens['func']['values'][:]):
        return False

    if (length == 4) != tokens['func']['slash']:
        return False

    return True


def validate_lch(tokens: dict[str, Any]) -> bool:
    """Validate CSS LCh variant color spaces."""

    length = len(tokens['func']['values'])
    delimiter = tokens['func']['delimiter']
    relative = tokens['func']['relative']

    if delimiter == 'comma':
        return False

    if length < 3 or length > 4:
        return False

    if not relative:
        if tokens['func']['values'][2]['type'] == 'percent':
            return False

        if any(v['type'] == 'degree' for v in tokens['func']['values'][0:2]):
            return False

        if (length == 4 and tokens['func']['values'][3]['type'] == 'degree'):
            return False

    if (length == 4) != tokens['func']['slash']:
        return False

    return True


def find_origin_end(css: str, start: int) -> int:
    """Find the end of a relative color's origin color, honoring nested functions and parentheses."""

    pos = start
    depth = 0
    length = len(css)
    while pos < length:
        char = css[pos]
        if char == '(':
            depth += 1
        elif char == ')':
            if depth == 0:
                break
            depth -= 1
        elif depth == 0 and char.isspace():
            break
        pos += 1
    return pos


def validate_relative_channels(tokens: dict[str, Any]) -> bool:
    """Validate that inherited channel keywords are valid for the relative color function."""

    func_name = tokens['func']['name']
    keywords = RE_CHANNEL_KEYWORDS.get(func_name)
    if keywords is None:
        return False

    values = tokens['func']['values']
    length = len(values)
    if length < 3 or length > 4:
        return False

    # The `alpha` keyword may appear in any position: it inherits the origin alpha (treated
    # as a channel value in channel positions). Channel keywords are valid in the slash
    # position and inherit that channel's value. All other keywords must be channel names.
    for value in values:
        if value['type'] == 'keyword' and value['value'].lower() not in keywords:
            return False

    # An explicit alpha is only valid after a slash.
    if length == 4 and not tokens['func']['slash']:
        return False

    return True


@functools.lru_cache(maxsize=1)
def tokenize_css(css: str, start: int = 0) -> dict[str, Any]:
    """Tokenize the CSS string."""

    tokens = {}  # type: dict[str, Any]
    # `mypy` will get confused, just set to Any
    m = RE_HEX.match(css, start)  # type: Any
    if m:
        tokens['hex'] = {
            'start': m.group(1),
            'value': m.group(0)
        }
        tokens['id'] = 'srgb'
        tokens['end'] = m.end()
        return tokens
    m = RE_NAME.match(css, start)
    if m:
        # Is hex?
        if color_names.has_name(m.group(1)):
            tokens['name'] = {'color': m.group(1)}
            tokens['id'] = 'srgb'
            tokens['end'] = m.end()
            return tokens

        # Is CSS function
        func_name = m.group(0).lower()
        m2 = RE_CSS_FUNC.match(func_name)
        if not m2:
            return {}

        # Has function body?
        tokens['func'] = {
            'name': func_name,
            'values': [],
            'delimiter': '',
            'relative': False,
            'origin': None
        }
        m = RE_FUNC_START.match(css, m.end())
        if not m:  # pragma: no cover
            return {}

        # If a color function, does it have an identifier?
        delimiter = None
        if func_name == 'color':
            m2 = RE_IDENT.match(css, m.end())
            if not m2:
                return {}
            delimiter = 'space'
            tokens['func']['delimiter'] = delimiter
            tokens['id'] = m2.group(1)
            m = RE_SPACE.match(css, m2.end())
            if not m:
                return {}

        # Relative color syntax (CSS Color 5): `func(from <origin> <channels>)`
        m2 = RE_FROM.match(css, m.end())
        if m2:
            if func_name not in RELATIVE_FUNCS:
                return {}
            m3 = RE_SPACE.match(css, m2.end())
            if not m3:
                return {}
            origin_start = m3.end()
            origin_end = find_origin_end(css, origin_start)
            if origin_end == origin_start:
                return {}
            tokens['func']['relative'] = True
            tokens['func']['origin'] = css[origin_start:origin_end]
            m3 = RE_SPACE.match(css, origin_end)
            if not m3:
                return {}
            delimiter = 'space'
            tokens['func']['delimiter'] = delimiter
            m = m3

        # Gather function channel values, up to 16.
        slash = False
        for _ in range(MAX_CHANNELS):
            # Get channel value
            m2 = RE_CHANNEL.match(css, m.end())
            if not m2:
                # A slash or comma must be followed by a channel
                if slash or delimiter == 'comma':
                    return {}
                break
            m = m2
            if m.group(2):
                tokens['func']['values'].append({'type': 'percent', 'value': m.group(0)})
            elif m.group(3):
                tokens['func']['values'].append({'type': 'degree', 'value': m.group(0)})
            elif m.group(4):
                tokens['func']['values'].append({'type': 'none', 'value': m.group(0)})
            elif m.group(5):
                tokens['func']['values'].append({'type': 'alpha-keyword', 'value': m.group(5)})
            elif m.group(6):
                tokens['func']['values'].append({'type': 'keyword', 'value': m.group(6)})
            else:
                tokens['func']['values'].append({'type': 'number', 'value': m.group(1)})

            if slash:
                break

            # Get delimiter type
            if delimiter is None:
                m2 = RE_COMMA.match(css, m.end(0))
                if not m2:
                    m2 = RE_LOOSE_SPACE.match(css, m.end(0))
                    if m2:
                        delimiter = 'space'
                        tokens['func']['delimiter'] = delimiter
                else:
                    delimiter = 'comma'
                    tokens['func']['delimiter'] = delimiter

            # Find comma
            elif delimiter == 'comma':
                m2 = RE_COMMA.match(css, m.end(0))
                if not m2:
                    break

            # Find space/slash
            else:
                m2 = RE_SLASH.match(css, m.end(0))
                if m2:
                    slash = True
                else:
                    m2 = RE_LOOSE_SPACE.match(css, m.end(0))

            m = m2

        tokens['func']['slash'] = slash

        # Relative colors cannot use the legacy comma syntax and must inherit valid keywords.
        if tokens['func']['relative'] and (
            tokens['func']['delimiter'] == 'comma' or
            not validate_relative_channels(tokens)
        ):
            return {}

        # Get function end
        m = RE_FUNC_END.match(css, m.end())
        if not m:
            return {}

        # Do basic validation on the supported color functions
        tokens['end'] = m.end()
        if func_name == 'color' and not validate_color(tokens):
            return {}  # pragma: no cover

        elif func_name.startswith('rgb'):
            tokens['id'] = 'srgb'
            if not validate_srgb(tokens):
                return {}

        elif func_name in ('hsl', 'hsla', 'hwb'):
            tokens['id'] = '--hwb' if func_name == 'hwb' else '--hsl'

            if not validate_cylindrical_srgb(tokens):
                return {}

        elif func_name in ('lab', 'oklab', 'jzazbz', 'ictcp'):
            tokens['id'] = '--' + func_name

            if not validate_lab(tokens):
                return {}

        elif func_name in ('oklch', 'lch', 'jzczhz'):
            tokens['id'] = '--' + func_name

            if not validate_lch(tokens):
                return {}

    return tokens


def parse_origin(color_class: Any, origin: str, target_space: Space) -> Any:
    """Parse a relative color's origin and convert it into the target color space."""

    match = color_class._match(origin, fullmatch=True)
    if match is None:
        return None
    origin_color = color_class(match[0].NAME, match[1], match[2])
    if origin_color.space() != target_space.NAME:
        origin_color = origin_color.convert(target_space.NAME)
    return origin_color


def resolve_relative_channels(
    tokens: dict[str, Any],
    origin_color: Any,
    boundary: tuple[Channel, ...],
    rgb: bool = False,
    scaled: bool = False
) -> tuple[Vector, float]:
    """Resolve relative color channels, substituting inherited channel keywords from the origin."""

    values = tokens['func']['values']
    coords = origin_color[:-1]
    origin_alpha = origin_color[-1]
    keyword_index = {str(channel): i for i, channel in enumerate(boundary)}

    channels = []
    alpha = 1.0
    for i, entry in enumerate(values):
        vtype = entry['type']
        value = entry['value'].lower()

        # Alpha channel (always the last entry when present). The `alpha` keyword inherits
        # the origin alpha; a channel keyword inherits that channel's coordinate value.
        if i == len(boundary):
            if vtype == 'alpha-keyword':
                alpha = origin_alpha
            elif vtype == 'keyword':
                alpha = coords[keyword_index[value]]
            else:
                alpha = norm_alpha_channel(value)
            break
        bound = boundary[i]
        if vtype == 'alpha-keyword':
            # The origin alpha is a 0-1 value interpreted like any other channel number:
            # RGB channels scale against the 0-255 range, scaled (0-100 native) channels map
            # the fraction onto the 0-100 scale, and other channels keep the fraction as-is.
            if rgb:
                channels.append(origin_alpha * bound.high * RGB_CHANNEL_SCALE)
            elif scaled:
                channels.append(norm_scaled_color_channel(str(origin_alpha), bound.high))
            else:
                channels.append(origin_alpha)
        elif vtype == 'keyword':
            # Inherit the origin channel value after conversion to the target space.
            channels.append(coords[keyword_index[value]])
        elif vtype == 'none':
            channels.append(norm_float(value))
        elif rgb:
            channels.append(norm_rgb_channel(value, bound.high))
        elif bound.flags & FLG_ANGLE:
            v = norm_angle_channel(value)
            channels.append(v * (bound.high / 360) if bound.angle != ANGLE_DEG else v)
        elif scaled:
            channels.append(norm_scaled_color_channel(value, bound.high))
        else:
            channels.append(norm_color_channel(value, bound.span, bound.offset))

    return channels, alpha


def parse_css(
    cspace: Space,
    string: str,
    start: int = 0,
    fullmatch: bool = True,
    color: bool = False,
    color_class: Any = None
) -> tuple[tuple[Vector, float], int] | None:
    """Match a CSS color string."""

    target = cspace.SERIALIZE
    if not target:
        target = (cspace.NAME,)

    tokens = tokenize_css(string, start=start)

    # Could we parse it?
    if not tokens:
        return None

    # Does the space match the target space? Space names are not case sensitive.
    if tokens['id'].lower() not in [t.lower() for t in target]:
        return None

    # Did we get a full match if requested?
    if fullmatch and tokens['end'] < len(string):
        return None

    # Scale and convert the channel data according to the CSS space rules
    end = tokens['end']
    relative = 'func' in tokens and tokens['func']['relative']
    if relative:
        if color_class is None:
            return None
        origin_color = parse_origin(color_class, tokens['func']['origin'], cspace)
        if origin_color is None:
            return None

    if 'func' in tokens and tokens['func']['name'] == 'color':
        if color is False:
            return None

        result = parse_color(tokens, cspace)
        if result is None:
            return result
        return result, end

    elif tokens['id'] == 'srgb':
        if 'hex' in tokens:
            return parse_hex(tokens['hex']['value']), end
        elif 'name' in tokens:
            values = color_names.from_name(tokens['name']['color'])
            return (values[:-1], values[-1]), end  # type: ignore[index]
        elif relative:
            return resolve_relative_channels(tokens, origin_color, cspace.CHANNELS, rgb=True), end
        else:
            return parse_rgb_channels([v['value'] for v in tokens['func']['values']], cspace.CHANNELS), end
    elif tokens['id'] in ('--hsl', '--hwb'):
        if relative:
            return resolve_relative_channels(tokens, origin_color, cspace.CHANNELS, scaled=True), end
        return parse_channels([v['value'] for v in tokens['func']['values']], cspace.CHANNELS, scaled=True), end
    else:
        if relative:
            return resolve_relative_channels(tokens, origin_color, cspace.CHANNELS, scaled=False), end
        return parse_channels([v['value'] for v in tokens['func']['values']], cspace.CHANNELS), end
