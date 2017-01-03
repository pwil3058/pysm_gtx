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

"""Various button like widgets
"""

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

__all__ = []
__author__ = "Peter Williams <pwil3058@gmail.com>"

from . import dialogue

#TODO: move button widgets in gutils into buttons.py

class ArrowButton(Gtk.Button):
    def __init__(self, arrow_type, shadow_type, width=-1, height=-1):
        Gtk.Button.__init__(self)
        self.set_size_request(width, height)
        self.add(Gtk.Arrow(arrow_type, shadow_type))

class HexSpinButton(Gtk.HBox, dialogue.ReporterMixin):
    #TODO: find out why HexSpinnButtons are so tall
    OFF, INCR, DECR = range(3)
    PAUSE = 500
    INTERVAL = 5
    def __init__(self, max_value, label=None):
        Gtk.HBox.__init__(self)
        if label:
            self.pack_start(label, expand=True, fill=True, padding=0)
        self.__dirn = self.OFF
        self.__value = 0
        self.__max_value = max_value
        self.__current_step = 1
        self.__max_step = max(1, max_value // 32)
        width = 0
        while max_value:
            width += 1
            max_value //= 16
        self.format_str = "0x{0:0>" + str(width) + "X}"
        self.entry = Gtk.Entry(width_chars=width + 2)
        self.pack_start(self.entry, expand=False, fill=True, padding=0)
        self._update_text()
        self.entry.connect("key-press-event", self._key_press_cb)
        self.entry.connect("key-release-event", self._key_release_cb)
        eh = self.entry.size_request().height
        bw = eh * 2 / 3
        bh = eh / 2 -1
        vbox = Gtk.VBox()
        self.pack_start(vbox, expand=False, fill=True, padding=0)
        self.up_arrow = ArrowButton(Gtk.ArrowType.UP, Gtk.ShadowType.NONE, bw, bh)
        self.up_arrow.connect("button-press-event", self._arrow_pressed_cb, self.INCR)
        self.up_arrow.connect("button-release-event", self._arrow_released_cb)
        self.up_arrow.connect("leave-notify-event", self._arrow_released_cb)
        vbox.pack_start(self.up_arrow, expand=True, fill=True, padding=0)
        self.down_arrow = ArrowButton(Gtk.ArrowType.DOWN, Gtk.ShadowType.NONE, bw, bh)
        self.down_arrow.connect("button-press-event", self._arrow_pressed_cb, self.DECR)
        self.down_arrow.connect("button-release-event", self._arrow_released_cb)
        self.down_arrow.connect("leave-notify-event", self._arrow_released_cb)
        vbox.pack_start(self.down_arrow, expand=True, fill=True, padding=0)
    def get_value(self):
        return self.__value
    def set_value(self, value):
        if value < 0 or value > self.__max_value:
            raise ValueError("{0:#X}: NOT in range 0X0 to {1:#X}".format(value, self.__max_value))
        self.__value = value
        self._update_text()
    def _arrow_pressed_cb(self, arrow, event, dirn):
        self.__dirn = dirn
        if self.__dirn is self.INCR:
            if self._incr_value():
                GObject.timeout_add(self.PAUSE, self._iterate_steps)
        elif self.__dirn is self.DECR:
            if self._decr_value():
                GObject.timeout_add(self.PAUSE, self._iterate_steps)
    def _arrow_released_cb(self, arrow, event):
        self.__dirn = self.OFF
    def _incr_value(self, step=1):
        if self.__value >= self.__max_value:
            return False
        self.__value = min(self.__value + step, self.__max_value)
        self._update_text()
        self.emit("value-changed", False)
        return True
    def _decr_value(self, step=1):
        if self.__value <= 0:
            return False
        self.__value = max(self.__value - step, 0)
        self._update_text()
        self.emit("value-changed", False)
        return True
    def _update_text(self):
        self.entry.set_text(self.format_str.format(self.__value))
    def _bump_current_step(self, exponential=True):
        if exponential:
            self.__current_step = min(self.__current_step * 2, self.__max_step)
        else:
            self.__current_step = min(self.__current_step + 1, self.__max_step)
    def _reset_current_step(self):
        self.__current_step = 1
    def _iterate_steps(self):
        keep_going = False
        if self.__dirn is self.INCR:
            keep_going = self._incr_value(self.__current_step)
        elif self.__dirn is self.DECR:
            keep_going = self._decr_value(self.__current_step)
        if keep_going:
            self._bump_current_step()
        else:
            self._reset_current_step()
        return keep_going
    def _key_press_cb(self, entry, event):
        if event.keyval in [Gdk.KEY_Return, Gdk.KEY_Tab]:
            try:
                self.set_value(int(entry.get_text(), 16))
                self.emit("value-changed", event.keyval == Gdk.KEY_Tab)
            except ValueError as edata:
                self.report_exception_as_error(edata)
                self._update_text()
            return True # NOTE: this will nobble the "activate" signal
        elif event.keyval == Gdk.KEY_Up:
            if self._incr_value(self.__current_step):
                self._bump_current_step(False)
            return True
        elif event.keyval == Gdk.KEY_Down:
            if self._decr_value(self.__current_step):
                self._bump_current_step(False)
            return True
    def _key_release_cb(self, entry, event):
        if event.keyval in [Gdk.KEY_Up, Gdk.KEY_Down]:
            self._reset_current_step()
            return True
GObject.signal_new("value-changed", HexSpinButton, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_BOOLEAN,))
