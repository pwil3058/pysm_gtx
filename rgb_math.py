#  Copyright 2017 Peter Williams <pwil3058@gmail.com>
#
# This software is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License only.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; if not, write to:
#  The Free Software Foundation, Inc., 51 Franklin Street,
#  Fifth Floor, Boston, MA 02110-1301 USA

"""Basic mathematic routines for RGB, Hue and Value transformations
"""

import array
import collections
import math

from ..bab import mathx

__all__ = []
__author__ = "Peter Williams <pwil3058@gmail.com>"

RGB = collections.namedtuple("RGB", ["red", "green", "blue"])
XY = collections.namedtuple("XY", ["x", "y"])

ARRAY_ONE = {
    "f" : 1.0,
    "d" : 1.0,
    "B" : (1 << 8) - 1,
    "H" : (1 << 16) - 1,
    "L" : (1 << 32) - 1,
}


def proportions_to_array(prpns, array_type_code):
    """Return an array of the requested type with values equivalent to
    the proportions in prpns.
    """
    if array_type_code in ["f", "d"]:
        return array.array(array_type_code, prpns)
    ONE = ARRAY_ONE[array_type_code]
    return array.array(array_type_code, [int(p * ONE + 0.5) for p in prpns])

def rgb_indices_value_order(rgb):
    """Return the indices of rgb in descending order by value
    """
    if rgb[0] > rgb[1]:
        if rgb[0] > rgb[2]:
            if rgb[1] > rgb[2]:
                return (0, 1, 2)
            else:
                return (0, 2, 1)
        else:
            return (2, 0, 1)
    elif rgb[1] > rgb[2]:
        if rgb[0] > rgb[2]:
            return (1, 0, 2)
        else:
            return (1, 2, 0)
    else:
        return (2, 1, 0)

def non_zero_components(rgb):
    """Return the number of non zero components in the container
    """
    return len(rgb) - rgb.count(0)

def rgb_hue_angle(rgb):
    """Return the hue angle for the given rgb.
    Angle returned is the angle between pure red (0 radians) and the hue
    for the given rgb taken anticlockwise through green.
    """
    return HueAngle.from_rgb(rgb)

def rgb_value_numerator(rgb):
    """Return the enumerator of the given rgb's value (as a float).
    The implicit denominator is the value that represents the maximum
    intensity value for the rgb's component values.
    """
    return sum(rgb) / 3

def rgb_chroma_numerator(rgb):
    """Return the enumerator of the given rgb's chroma (as a float).
    The implicit denominator is the value that represents the maximum
    intensity value for the rgb's component values.
    """
    x, y = rgb_to_xy(rgb)
    return math.hypot(x, y) * HueAngle.from_xy(x, y).chroma_correction

def rgb_warmth_numerator(rgb):
    """Return the enumerator of the given rgb's warmth (as a float).
    The implicit denominator is the value that represents the maximum
    intensity value for the rgb's component values.
    """
    return rgb_x_coord(rgb)

def rgb_array_value(rgb_array):
    return rgb_value_numerator(rgb_array) / ARRAY_ONE[rgb_array.typecode]

def rgb_array_chroma(rgb_array):
    return rgb_chroma_numerator(rgb_array) / ARRAY_ONE[rgb_array.typecode]

def rgb_array_warmth(rgb_array):
    return rgb_warmth_numerator(rgb_array) / ARRAY_ONE[rgb_array.typecode]

class PRGB(RGB):
    """An RGB tupple whose components are represented by floats with
    values in the range 0.0 to 1.0.
    """
    ONE = 1.0

SIN_60 = math.sin(mathx.PI_60)
SIN_120 = math.sin(mathx.PI_120)
COS_120 = -0.5 # math.cos(mathx.PI_120) is slightly out

RGB_TO_X_VECTOR = (1.0, COS_120, COS_120)
RGB_TO_Y_VECTOR = (0.0, SIN_120, -SIN_120)

def rgb_x_coord(rgb):
    """Return the X cartesian coordinate for rgb
    """
    return sum(RGB_TO_X_VECTOR[i] * rgb[i] for i in range(3))

def rgb_y_coord(rgb):
    """Return the X cartesian coordinate for rgb
    """
    return sum(RGB_TO_Y_VECTOR[i] * rgb[i] for i in range(1, 3))

def rgb_to_xy(rgb):
    """Return the cartesian coordinates for rgb
    """
    return XY(rgb_x_coord(rgb), rgb_y_coord(rgb))

def xy_to_rgb(x, y):
    """Return the RGB with at most 2 non-zero components that matches our x and y.
    NB this cannot be used to reverse rgb_to_xy() as information is lost
    during that transformation.
    The components in the result will be floats and their dimensions
    will be consistent with the dimensions of x and y.
    """
    a = x / COS_120
    b = y / SIN_120
    if y > 0.0:
        if a > b:
            return RGB(0.0, ((a + b) / 2), ((a - b) / 2))
        else:
            return RGB((x - b * COS_120), b, 0.0)
    elif y < 0.0:
        if a > -b:
            return RGB(0.0, ((a + b) / 2), ((a - b) / 2))
        else:
            return RGB((x + b * COS_120), 0.0, -b)
    elif x < 0.0:
        ha = a / 2
        return RGB(0.0, ha, ha)
    else:
        return RGB(x, 0.0, 0.0)


class HueAngle:
    __slots__ = ["__angle", "__max_chroma_rgb", "__chroma_correction"]
    def __init__(self, angle):
        if math.isnan(angle):
            self.__angle = float("nan")
            self.__max_chroma_rgb = PRGB(1.0, 1.0, 1.0)
            self.__chroma_correction = 1.0
        else:
            aha = abs(angle)
            self.__angle = mathx.Angle(angle)
            def calc_other(oa):
                if oa in [mathx.PI_60, mathx.PI_180]:
                    return 1.0
                return math.sin(oa) / math.sin(mathx.PI_120 - oa)
            if aha <= mathx.PI_60:
                other = calc_other(aha)
                self.__max_chroma_rgb = PRGB(1.0, other, 0.0) if angle >= 0 else PRGB(1.0, 0.0, other)
            elif aha <= mathx.PI_120:
                other = calc_other(mathx.PI_120 - aha)
                self.__max_chroma_rgb = PRGB(other, 1.0, 0.0) if angle >= 0 else PRGB(other, 0.0, 1.0)
            else:
                other = calc_other(aha - mathx.PI_120)
                self.__max_chroma_rgb = PRGB(0.0, 1.0, other) if angle >= 0 else PRGB(0.0, other, 1.0)
            self.__chroma_correction = 1.0 / math.sqrt(1.0 + other * other - other)
    def __float__(self):
        return self.__angle
    @classmethod
    def from_rgb(cls, rgb):
        x, y = rgb_to_xy(rgb)
        if x == 0.0 and y == 0.0:
            return cls(float("nan"))
        else:
            return cls(math.atan2(y, x))
    @classmethod
    def from_xy(cls, x, y):
        if x == 0.0 and y == 0.0:
            return cls(float("nan"))
        else:
            return cls(math.atan2(y, x))
    @property
    def angle(self):
        return self.__angle
    @property
    def max_chroma_prgb(self):
        return self.__max_chroma_rgb
    def max_chroma_rgb_array(self, typecode):
        return proportions_to_array(self.__max_chroma_rgb, typecode)
    @property
    def chroma_correction(self):
        return self.__chroma_correction
    def __eq__(self, other):
        if math.isnan(self.__angle):
            return math.isnan(other.__angle)
        return self.__angle.__eq__(other.__angle)
    def __ne__(self, other):
        return not self.__eq__(other.__angle)
    def __lt__(self, other):
        if math.isnan(self.__angle):
            return not math.isnan(other.__angle)
        return self.__angle.__lt__(other.__angle)
    def __le__(self, other):
        return self.__lt__(other.__angle) or self.__eq__(other.__angle)
    def __gt__(self, other):
        return not self.__le__(other.__angle)
    def __ge__(self, other):
        return not self.__lt__(other.__angle)
    def __sub__(self, other):
        diff = self.__angle - other.__angle
        if diff > math.pi:
            diff -= math.pi * 2
        elif diff < -math.pi:
            diff += math.pi * 2
        return diff
    def int_rgb(self, one):
        return RGB(*(int(a * one + 0.5) for a in self.__max_chroma_rgb))
    @property
    def max_chroma_value(self):
        """Return the value attribute for the maximum chroma RGB for
        this hue.
        """
        return sum(self.__max_chroma_rgb) / 3
    def max_chroma_for_value(self, value):
        """Return the maximum chroma value that can be achieved for an
        RGB with this hue and the given value
        """
        if math.isnan(self.__angle):
            return 0.0
        total = value * 3.0
        mct = sum(self.__max_chroma_rgb)
        if mct > total: # on the dark side (easy)
            return total / mct
        else:
            aha = abs(self.__angle)
            return ((3.0 - total) / (2.0 * math.cos(aha if aha < mathx.PI_60 else aha - mathx.PI_120))) * self.__chroma_correction
    def __make_up_shortfall(self, shortfall):
        """Return the PRGB for this hue with the specified component
        total.
        NB if shortfall is too big for the hue the returned rgb
        will deviate towards the weakest component on its way to white.
        """
        result = [1.0, 1.0, 1.0]
        io = rgb_indices_value_order(self.__max_chroma_rgb)
        # it's simpler two work out the weakest component first
        other = self.__max_chroma_rgb[io[1]]
        result[io[2]] = shortfall / (2.0 - other)
        result[io[1]] = other + shortfall - result[io[2]]
        return PRGB(*result)
    def max_chroma_prgb_with_value(self, req_value):
        """Return the PRGB for this hue with the specified value and the
        maximum chroma possible for that combination.
        NB if requested value is too big for the hue the returned value
        will deviate towards the weakest component on its way to white.
        """
        assert req_value >= 0.0 and req_value <= 1.0, "{}: requeste value must be betwwen 0.0 and 1.0".format(req_value)
        if math.isnan(self.__angle):
            return PRGB(req_value, req_value, req_value)
        req_total = req_value * 3
        cur_total = sum(self.__max_chroma_rgb)
        shortfall = req_total - cur_total
        if shortfall == 0.0:
            return self.__max_chroma_rgb
        elif shortfall < 0.0:
            # lose chroma towards the dark side
            return PRGB(*(a * req_total / cur_total for a in self.__max_chroma_rgb))
        else:
            # lose chroma towards the light side
            return self.__make_up_shortfall(shortfall)
    def max_chroma_rgb_array_with_value(self, req_value, array_type_code):
        """
        Return the RGB for this hue with the specified value and
        maximum chroma for the combination as an array of the specified
        type.
        NB if requested value is too big for the hue the returned value
        will deviate towards the weakest component on its way to white.
        """
        return proportions_to_array(self.max_chroma_prgb_with_value(req_value), array_type_code)
    @property
    def is_grey(self):
        return math.isnan(self.__angle)
    def rotated_by(self, delta_angle):
        return self.__class__(self.__angle + delta_angle)
    def prgb_with_chroma(self, req_chroma, dark_side=True):
        if req_chroma == 0:
            return PRGB(0.0, 0.0, 0.0) if dark_side else PRGB(1.0, 1.0, 1.0)
        assert req_chroma > 0 and req_chroma <= 1.0
        if dark_side:
            req_hypot = req_chroma  / self.__chroma_correction
            return xy_to_rgb(req_hypot * math.cos(self.__angle), req_hypot * math.sin(self.__angle))
        else:
            shortfall = (1.0 - req_chroma / self.__chroma_correction) * (3.0 - sum(self.__max_chroma_rgb))
            result = [1.0, 1.0, 1.0]
            io = rgb_indices_value_order(self.__max_chroma_rgb)
            # it's simpler two work out the weakest component first
            other = self.__max_chroma_rgb[io[1]]
            result[io[2]] = shortfall / (2.0 - other)
            result[io[1]] = other + shortfall - result[io[2]]
            return PRGB(*result)


class RGBManipulator:
    def __init__(self, rgb):
        self.set_rgb(rgb)
    def set_rgb(self, rgb):
        self.__rgb_cls = rgb.__class__
        if hasattr(rgb, "typecode"):
            self.__rgb_array_type_code = rgb.typecode
            self.__rgb_one = ARRAY_ONE[rgb.typecode]
        else:
            self.__rgb_one = rgb.ONE if hasattr(rgb, "ONE") else None
        if self.__rgb_one:
            rgb = (c / self.__rgb_one for c in rgb)
        self.__set_rgb(rgb)
        self.__last_hue = self.__hue
    def __set_rgb(self, rgb):
        self.__rgb = PRGB(*rgb)
        self.__value = rgb_value_numerator(self.__rgb)
        self.__xy = rgb_to_xy(self.__rgb)
        self.__base_rgb = xy_to_rgb(*self.__xy)
        self.__hue = HueAngle.from_xy(*self.__xy)
        self.__chroma = min(math.hypot(*self.__xy) * self.__hue.chroma_correction, 1.0)
    def _min_value_for_current_HC(self):
        return rgb_value_numerator(self.__base_rgb)
    def _max_value_for_current_HC(self):
        return rgb_value_numerator(self.__base_rgb) + 1.0 - max(self.__base_rgb)
    def get_rgb(self):
        if issubclass(self.__rgb_cls, array.array):
            if self.__rgb_array_type_code in ["f", "d"]:
                return self.__rgb_cls(self.__rgb_array_type_code, self.__rgb)
            else:
                return self.__rgb_cls(self.__rgb_array_type_code, (int(p * self.__rgb_one + 0.5) for p in self.__rgb))
        elif isinstance(self.__rgb_one, float):
            return self.__rgb_cls(*(p * self.__rgb_one for p in self.__rgb))
        elif self.__rgb_one:
            return self.__rgb_cls(*(int(p * self.__rgb_one + 0.5) for p in self.__rgb))
        else:
            return PRGB(*self.__rgb)
    def _set_from_value(self, new_value):
        new_chroma = self.__hue.max_chroma_for_value(new_value)
        new_base_rgb = self.__hue.prgb_with_chroma(new_chroma)
        delta = new_value - rgb_value_numerator(new_base_rgb)
        self.__set_rgb((c + delta for c in new_base_rgb))
    def _set_from_chroma(self, new_chroma):
        ratio = new_chroma / self.__chroma
        new_base_rgb = PRGB(*(c * ratio for c in self.__base_rgb))
        delta = min(1.0 - max(new_base_rgb), self.__value - rgb_value_numerator(new_base_rgb))
        if delta > 0.0:
            self.__set_rgb((c + delta for c in new_base_rgb))
        else:
            self.__set_rgb(new_base_rgb)
    def decr_value(self, deltav):
        if self.__value <= 0.0:
            return False
        new_value = max(0.0, self.__value - deltav)
        min_value = self._min_value_for_current_HC()
        if new_value == 0.0:
            self.__set_rgb((0.0, 0.0, 0.0))
        elif new_value < min_value:
            # We have to do this the hard way
            self._set_from_value(new_value)
        else:
            delta = new_value - min_value
            self.__set_rgb((c + delta for c in self.__base_rgb))
        return True
    def incr_value(self, deltav):
        if self.__value >= 1.0:
            return False
        new_value = min(1.0, self.__value + deltav)
        max_value = self._max_value_for_current_HC()
        if new_value >= 1.0:
            self.__set_rgb((1.0, 1.0, 1.0))
        elif new_value > max_value:
            # We have to do this the hard way
            self._set_from_value(new_value)
        else:
            delta = new_value - self._min_value_for_current_HC()
            self.__set_rgb((c + delta for c in self.__base_rgb))
        return True
    def decr_chroma(self, deltac):
        if self.__chroma <= 0.0:
            return False
        self._set_from_chroma(max(0.0, self.__chroma - deltac))
        return True
    def incr_chroma(self, deltac):
        if self.__chroma >= 1.0:
            return False
        if self.__hue.is_grey:
            if self.__value <= 0.0 or self.__value >= 1.0:
                if self.__last_hue.is_grey:
                    # any old hue will do
                    new_base_rgb = HueAngle(0.5).prgb_with_chroma(deltac)
                else:
                    new_base_rgb = self.__last_hue.prgb_with_chroma(deltac)
                if self.__value <= 0.0:
                    self.__set_rgb(new_base_rgb)
                else:
                    delta = 1.0 - max(new_base_rgb)
                    self.__set_rgb((c + delta for c in new_base_rgb))
            else:
                if self.__last_hue.is_grey:
                    # any old hue will do
                    new_base_rgb = HueAngle(0.5).prgb_with_chroma(min(deltac, self.__value))
                else:
                    max_chroma = self.__last_hue.max_chroma_for_value(self.__value)
                    new_base_rgb = self.__last_hue.prgb_with_chroma(min(deltac, max_chroma))
                # delta should be greater than or equal to zero
                delta = self.__value - rgb_value_numerator(new_base_rgb)
                self.__set_rgb((c + delta for c in new_base_rgb))
            self.__last_hue = self.__hue
        else:
            self._set_from_chroma(min(1.0, self.__chroma + deltac))
        return True
    def rotate_hue(self, deltah):
        if self.__hue.is_grey:
            return False # There is no hue to rotate
        # keep same chroma
        new_base_rgb = self.__hue.rotated_by(deltah).prgb_with_chroma(self.__chroma)
        # keep same value if possible (otherwise as close as possible)
        max_delta = 1.0 - max(new_base_rgb)
        delta = min(max_delta, self.__value - rgb_value_numerator(new_base_rgb))
        if delta > 0.0:
            self.__set_rgb((c + delta for c in new_base_rgb))
        else:
            self.__set_rgb(new_base_rgb)
        self.__last_hue = self.__hue
        return True
