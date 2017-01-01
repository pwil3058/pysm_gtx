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

"""Take screen samples
"""

__all__ = []
__author__ = "Peter Williams <pwil3058@gmail.com>"

import sys

import faulthandler
faulthandler.enable()
faulthandler.dump_traceback_later(1)

from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import Gtk

# Screen Sampling
# Based on escrotum code (<https://github.com/Roger/escrotum>)
# TODO: fix problem with screen sampler causing core dump on second invocation
# TODO: fix problem with screen sampler not working properly over windows
class ScreenSampler(Gtk.Window):
    def __init__(self, clipboard=Gdk.SELECTION_CLIPBOARD):
        Gtk.Window.__init__(self, Gtk.WindowType.POPUP)
        self.started = False
        self.x = self.y = 0
        self.start_x = self.start_y = 0
        self.height = self.width = 0
        self.clipboard = clipboard
        self.connect("draw", self.on_expose)
        self.grab_mouse()
    def set_rect_size(self, event):
        if event.x < self.start_x:
            x = int(event.x)
            width = self.start_x - x
        else:
            x = self.start_x
            width = int(event.x) - self.start_x
        self.x = x
        self.width = width
        if event.y < self.start_y:
            y = int(event.y)
            height = self.start_y - y
        else:
            height = int(event.y) - self.start_y
            y = self.start_y
        self.y = y
        self.height = height
    def take_sample(self):
        x, y = (self.x, self.y)
        width, height = self.width, self.height
        if self.height == 0 or self.width == 0:
            # treat a zero area selection as a user initiated cancellation
            self.finish()
            return
        win = Gdk.get_default_root_window()
        pb = Gdk.pixbuf_get_from_window(win, x, y, width, height)
        if pb:
            cbd = Gtk.Clipboard.get(self.clipboard)
            cbd.set_image(pb)
        self.finish()
        return False
    def mouse_event_handler(self, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button.button != 1:
                # treat button 2 or 3 press as a user initiated cancellation
                self.finish()
                return
            self.started = True
            self.start_x = int(event.button.x)
            self.start_y = int(event.button.y)
            self.move(self.x, self.y)
        elif event.type == Gdk.EventType.MOTION_NOTIFY:
            if not self.started:
                return
            self.set_rect_size(event.button)
            if self.width > 3 and self.height > 3:
                self.resize(self.width, self.height)
                self.move(self.x, self.y)
                self.show_all()
        elif event.type == Gdk.EventType.BUTTON_RELEASE:
            if not self.started:
                return
            self.set_rect_size(event.button)
            Gdk.pointer_ungrab(Gdk.CURRENT_TIME)
            self.hide()
            GObject.timeout_add(125, self.take_sample)
        else:
            return Gtk.main_do_event(event)
    def grab_mouse(self):
        win = Gdk.get_default_root_window()
        mask = Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK |  Gdk.EventMask.POINTER_MOTION_MASK  | Gdk.EventMask.POINTER_MOTION_HINT_MASK |  Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK
        Gdk.pointer_grab(win, True, mask, None, Gdk.Cursor(Gdk.CursorType.CROSSHAIR), Gdk.CURRENT_TIME)
        self.saved_event_mask = win.get_events()
        win.set_events(Gdk.EventMask.ALL_EVENTS_MASK)
        Gdk.event_handler_set(self.mouse_event_handler)
    def finish(self):
        if Gdk.pointer_is_grabbed():
            Gdk.pointer_ungrab(Gdk.CURRENT_TIME)
        Gdk.get_default_root_window().set_events(self.saved_event_mask)
        Gdk.event_handler_set(Gtk.main_do_event)
        self.destroy()
    def on_expose(self, widget, cairo_ctxt):
        width, height = self.get_size()
        width, height = widget.get_allocated_width(), widget.get_allocated_height()
        #print("SIZE:", width, height, widget.get_allocated_width(), widget.get_allocated_height())
        widget.set_opacity(0.15)
        widget.set_keep_above(True)
        widget.show_all()
        cairo_ctxt.set_source_rgb(0, 0, 0)
        cairo_ctxt.set_line_width(12)
        cairo_ctxt.move_to(0, 0)
        cairo_ctxt.line_to(width, 0)
        cairo_ctxt.line_to(width, height)
        cairo_ctxt.line_to(0, height)
        cairo_ctxt.close_path()
        #cairo_ctxt.rectangle(0, 0, width, height)
        cairo_ctxt.stroke()
        #print("EXPOSED")


def take_screen_sample():
    if sys.platform.startswith("win"):
        from . import dialogue
        dlg = dialogue.MessageDialog(text=_("Functionality NOT available on Windows. Use built in Clipping Tool."))
        Gdk.beep()
        dlg.run()
        dlg.destroy()
        return None
    else:
        return ScreenSampler()
