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

"""Provide support for applications to add their own icons"""

import os
import sys

from gi.repository import Gtk
from gi.repository import GdkPixbuf

try:
    from .. import APP_NAME
except ImportError:
    from ... import APP_NAME

def find_app_icon_directory(app_name):
    """Find the directory containing "app_name"'s pixmaps."""
    # first look in the source directory (so that we can run uninstalled)
    icon_dir_path = os.path.join(sys.path[0], "pixmaps")
    if not os.path.exists(icon_dir_path) or not os.path.isdir(icon_dir_path):
        _TAILEND = os.path.join("share", "pixmaps", app_name)
        _prefix = sys.path[0]
        while _prefix:
            icon_dir_path = os.path.join(_prefix, _TAILEND)
            if os.path.exists(icon_dir_path) and os.path.isdir(icon_dir_path):
                break
            _prefix = os.path.dirname(_prefix)
    return icon_dir_path

APP_PIXMAPS_DIR_PATH = find_app_icon_directory(APP_NAME)
APP_ICON = APP_NAME
APP_ICON_FILE = os.path.join(os.path.dirname(APP_PIXMAPS_DIR_PATH), APP_ICON + os.extsep + "png")
APP_ICON_PIXBUF = GdkPixbuf.Pixbuf.new_from_file(APP_ICON_FILE)

def add_own_stock_icons(stock_item_list):
    # TODO: find out how to make STOCK items properly in GTK+-30
    OFFSET = len(APP_NAME) + 1
    png_file_name = lambda item_name: os.path.join(APP_PIXMAPS_DIR_PATH, item_name[OFFSET:] + os.extsep + "png")
    def make_pixbuf(name):
        return GdkPixbuf.Pixbuf.new_from_file(png_file_name(name))
    factory = Gtk.IconFactory()
    factory.add_default()
    for _item in stock_item_list:
        _name = _item[0]
        factory.add(_name, Gtk.IconSet(make_pixbuf(_name)))

