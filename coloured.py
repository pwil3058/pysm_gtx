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

"""Coloured widgets"""

import fractions

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

__all__ = []
__author__ = "Peter Williams <pwil3058@gmail.com>"

GDK_BITS_PER_CHANNEL = 16
GDK_ONE = (1 << GDK_BITS_PER_CHANNEL) - 1

def best_foreground(rgb, threshold=0.5):
    wval = (rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114)
    if wval > GDK_ONE * threshold:
        return Gdk.Color(0, 0, 0)
    else:
        return Gdk.Color(GDK_ONE, GDK_ONE, GDK_ONE)

class ColourableLabel(Gtk.EventBox):
    def __init__(self, label=""):
        Gtk.EventBox.__init__(self)
        self.label = Gtk.Label(label=label)
        self.add(self.label)
        self.show_all()
    def modify_base(self, state, colour):
        Gtk.EventBox.modify_base(self, state, colour)
        self.label.modify_base(state, colour)
    def modify_text(self, state, colour):
        Gtk.EventBox.modify_text(self, state, colour)
        self.label.modify_text(state, colour)
    def modify_fg(self, state, colour):
        Gtk.EventBox.modify_fg(self, state, colour)
        self.label.modify_fg(state, colour)

class ColouredLabel(ColourableLabel):
    def __init__(self, label, colour=None):
        ColourableLabel.__init__(self, label=label)
        if colour is not None:
            self.set_colour(colour)
    def set_colour(self, colour):
        bg_colour = Gdk.Color(*colour)
        fg_colour = best_foreground(colour)
        for state in [Gtk.StateType.NORMAL, Gtk.StateType.PRELIGHT, Gtk.StateType.ACTIVE]:
            self.modify_base(state, bg_colour)
            self.modify_bg(state, bg_colour)
            self.modify_fg(state, fg_colour)
            self.modify_text(state, fg_colour)

class ColouredButton(Gtk.EventBox):
    prelit_width = 2
    unprelit_width = 0
    state_value_ratio = {
        Gtk.StateType.NORMAL: fractions.Fraction(1),
        Gtk.StateType.ACTIVE: fractions.Fraction(1, 2),
        Gtk.StateType.PRELIGHT: fractions.Fraction(1),
        Gtk.StateType.SELECTED: fractions.Fraction(1),
        Gtk.StateType.INSENSITIVE: fractions.Fraction(1, 4)
    }
    def __init__(self, colour=None, label=None):
        self.label = ColouredLabel(label, colour)
        Gtk.EventBox.__init__(self)
        self.set_size_request(25, 25)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK|Gdk.EventMask.BUTTON_RELEASE_MASK|Gdk.EventMask.LEAVE_NOTIFY_MASK|Gdk.EventMask.FOCUS_CHANGE_MASK)
        self.connect("button-press-event", self._button_press_cb)
        self.connect("button-release-event", self._button_release_cb)
        self.connect("enter-notify-event", self._enter_notify_cb)
        self.connect("leave-notify-event", self._leave_notify_cb)
        self.frame = Gtk.Frame()
        self.frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.frame.set_border_width(self.unprelit_width)
        self.frame.add(self.label)
        self.add(self.frame)
        if colour is not None:
            self.set_colour(colour)
        self.show_all()
    def _button_press_cb(self, widget, event):
        if event.button != 1:
            return False
        self.frame.set_shadow_type(Gtk.ShadowType.IN)
        self.set_state(Gtk.StateType.ACTIVE)
    def _button_release_cb(self, widget, event):
        if event.button != 1:
            return False
        self.frame.set_shadow_type(Gtk.ShadowType.OUT)
        self.set_state(Gtk.StateType.PRELIGHT)
        self.emit("clicked", int(event.get_state()))
    def _enter_notify_cb(self, widget, event):
        self.frame.set_shadow_type(Gtk.ShadowType.OUT)
        self.frame.set_border_width(self.prelit_width)
        self.set_state(Gtk.StateType.PRELIGHT)
    def _leave_notify_cb(self, widget, event):
        self.frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.frame.set_border_width(self.unprelit_width)
        self.set_state(Gtk.StateType.NORMAL)
    def set_colour(self, colour):
        self.colour = colour
        for state, value_ratio in self.state_value_ratio.items():
            rgb = [min(int(colour[i] * value_ratio), 65535) for i in range(3)]
            bg_gcolour = Gdk.Color(*rgb)
            fg_gcolour = best_foreground(rgb)
            self.modify_base(state, bg_gcolour)
            self.modify_bg(state, bg_gcolour)
            self.modify_fg(state, fg_gcolour)
            self.modify_text(state, fg_gcolour)
        self.label.set_colour(colour)
GObject.signal_new("clicked", ColouredButton, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_INT,))
