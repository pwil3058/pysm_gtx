#  Copyright 2016 Peter Williams <pwil3058@gmail.com>
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

"""<DOCSTRING GOES HERE>"""

__all__ = []
__author__ = "Peter Williams <pwil3058@gmail.com>"

import gi
gi.require_version("Gtk", "3.0")
try:
    gi.require_version("GtkSpell", "3.0")
    GTK_SPELL_AVAILABLE = True
except ValueError:
    GTK_SPELL_AVAILABLE = False
from gi.repository import Gtk

def yield_to_pending_events():
    while True:
        Gtk.main_iteration()
        if not Gtk.events_pending():
            break
