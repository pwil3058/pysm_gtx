### Copyright (C) 2016 Peter Williams <pwil3058@gmail.com>
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

import os
import sys
import collections

from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GdkPixbuf

PACKAGE_NAME = "aipoed"

def find_icon_directory(app_or_pkg_name):
    # find the icons directory
    # first look in the source directory (so that we can run uninstalled)
    icon_dir_path = os.path.join(sys.path[0], "pixmaps")
    if not os.path.exists(icon_dir_path) or not os.path.isdir(icon_dir_path):
        _TAILEND = os.path.join("share", "pixmaps", app_or_pkg_name)
        _prefix = sys.path[0]
        while _prefix:
            icon_dir_path = os.path.join(_prefix, _TAILEND)
            if os.path.exists(icon_dir_path) and os.path.isdir(icon_dir_path):
                break
            _prefix = os.path.dirname(_prefix)

StockAlias = collections.namedtuple("StockAlias", ["name", "alias", "text"])

def add_stock_aliases(stock_alias_list):
    factory = Gtk.IconFactory()
    factory.add_default()
    style = Gtk.Frame().get_style()
    for item in stock_alias_list:
        factory.add(item.name, style.lookup_icon_set(item.alias))


_PREFIX = PACKAGE_NAME + "_"

# Icons that are aliased to Gtk or other stock items
STOCK_RENAME = _PREFIX + "stock_rename"
STOCK_INSERT = _PREFIX + "_stock_insert"

# Icons that have to be designed eventually (using GtK stock in the meantime)
_STOCK_ALIAS_LIST = [
    StockAlias(name=STOCK_RENAME, alias=Gtk.STOCK_PASTE, text=""),
    StockAlias(name=STOCK_INSERT, alias=Gtk.STOCK_ADD, text=_("Insert")),
]

add_stock_aliases(_STOCK_ALIAS_LIST)
