### -*- coding: utf-8 -*-
###
###  Copyright (C) 2016 Peter Williams <pwil3058@gmail.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; version 2 of the License only.
###
### This program is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.
###
### You should have received a copy of the GNU General Public License
### along with this program; if not, write to the Free Software
### Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

from contextlib import contextmanager

from gi.repository import Gtk
from gi.repository import Gdk

from . import yield_to_pending_events

class BusyIndicator:
    def __init__(self, parent=None):
        self._bi_parent = parent
        self._bi_depth = 0
        self.connect("destroy", lambda _widget: self._turn_off_busy())
    def _turn_off_busy(self):
        while self.is_busy:
            self.unshow_busy()
    def show_busy(self):
        if self._bi_parent and self.get_modal():
            self._bi_parent.show_busy()
        self._bi_depth += 1
        if self._bi_depth == 1:
            window = self.get_window()
            if window is not None:
                window.set_cursor(Gdk.Cursor.new(Gdk.CursorType.WATCH))
                yield_to_pending_events()
    def unshow_busy(self):
        if self._bi_parent and self.get_modal():
            self._bi_parent.unshow_busy()
        self._bi_depth -= 1
        assert self._bi_depth >= 0
        if self._bi_depth == 0:
            window = self.get_window()
            if window is not None:
                window.set_cursor(None)
                yield_to_pending_events()
    @contextmanager
    def showing_busy(self):
        self.show_busy()
        try:
            yield
        finally:
            self.unshow_busy()
    @property
    def is_busy(self):
        return self._bi_depth > 0

class BusyIndicatorUser:
    @contextmanager
    def showing_busy(self):
        self.get_toplevel().show_busy()
        try:
            yield
        finally:
            self.get_toplevel().unshow_busy()

class Window(Gtk.Window, BusyIndicator):
    def __init__(self, **kwargs):
        Gtk.Window.__init__(self, **kwargs)
        BusyIndicator.__init__(self)

class Dialog(Gtk.Dialog, BusyIndicator):
    def __init__(self, **kwargs):
        Gtk.Dialog.__init__(self, **kwargs)
        BusyIndicator.__init__(self, kwargs.get("parent", None))
