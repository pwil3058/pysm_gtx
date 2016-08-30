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

class QuestionDialog(Dialog):
    def __init__(self, question="", explanation="", **kwargs):
        Dialog.__init__(self, **kwargs)
        self.set_skip_taskbar_hint(True)
        self.set_destroy_with_parent(True)
        grid = Gtk.Grid()
        self.vbox.add(grid)
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_DIALOG_QUESTION, Gtk.IconSize.DIALOG)
        grid.add(image)
        q_label = Gtk.Label()
        q_label.set_markup("<big><b>" + question + "</b></big>")
        q_label.set_justify(Gtk.Justification.LEFT)
        q_label.set_line_wrap(True)
        grid.attach_next_to(q_label, image, Gtk.PositionType.RIGHT, 1, 1)
        if explanation:
            e_label = Gtk.Label(explanation)
            e_label.set_justify(Gtk.Justification.FILL)
            e_label.set_line_wrap(True)
            grid.attach_next_to(e_label, q_label, Gtk.PositionType.BOTTOM, 1, 1)
        self.show_all()

CANCEL_OK_BUTTONS = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
NO_YES_BUTTONS = (Gtk.STOCK_NO, Gtk.ResponseType.NO, Gtk.STOCK_YES, Gtk.ResponseType.YES)

class AskerMixin:
    def ask_question(self, question, explanation="", buttons=CANCEL_OK_BUTTONS):
        dialog = QuestionDialog(parent=self.get_toplevel(), buttons=buttons, question=question, explanation=explanation)
        response = dialog.run()
        dialog.destroy()
        return response
