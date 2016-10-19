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

import os
import urllib.parse

from gi.repository import Gtk

from aipoed import utils

from aipoed.gui import apath
from aipoed.gui import gutils

_APP_NAME = None

def initialize(app_name, config_dir_name):
    global _APP_NAME
    global RepoPathView
    _APP_NAME = app_name
    RepoPathView.SAVED_FILE_NAME = os.path.join(config_dir_name, "repositories")

class RepoPathView(apath.AliasPathView):
    SAVED_FILE_NAME = None
    def __init__(self):
        apath.AliasPathView.__init__(self)
    @staticmethod
    def _extant_path(path):
        if urllib.parse.urlparse(path).scheme:
            # for the time being treat all paths expressed as URLs as extant
            return True
        return apath.AliasPathView._extant_path(path)
    @staticmethod
    def _same_paths(path1, path2):
        up1 = urllib.parse.urlparse(path1)
        if up1.scheme:
            up2 = urllib.parse.urlparse(path2)
            if up2.scheme:
                # compare normalized URLs for better confidence in result
                return up1.geturl() == up2.geturl()
            else:
                return False
        elif urllib.parse.urlparse(path2).scheme:
            return False
        else:
            return apath.AliasPathView._same_paths(path1, path2)
    @staticmethod
    def _default_alias(path):
        urlp = urllib.parse.urlparse(path)
        if not urlp.scheme:
            return apath.AliasPathView._default_alias(path)
        else:
            return os.path.basename(urlp.path)

class RepoPathTable(apath.AliasPathTable):
    VIEW = RepoPathView

class RepoSelectDialog(apath.PathSelectDialog):
    PATH_TABLE = RepoPathTable
    def __init__(self, parent=None):
        apath.PathSelectDialog.__init__(self, label=_("Repository"), parent=parent)
        hbox = Gtk.HBox()
        hbox.pack_start(Gtk.Label(_("As:")), expand=True, fill=True, padding=0)
        self._target = gutils.new_mutable_combox_text_with_entry()
        self._target.get_child().set_width_chars(32)
        self._target.get_child().connect("activate", self._target_cb)
        hbox.pack_start(self._target, expand=True, fill=True, padding=0)
        self._default_button = Gtk.Button(label=_("_Default"))
        self._default_button.connect("clicked", self._default_cb)
        hbox.pack_start(self._default_button, expand=False, fill=False, padding=0)
        self.vbox.pack_start(hbox, expand=False, fill=False, padding=0)
        self.show_all()
    def _target_cb(self, entry=None):
        self.response(Gtk.ResponseType.OK)
    def _get_default_target(self):
        rawpath = self.get_path()
        urp = urllib.parse.urlparse(rawpath)
        if urp.scheme:
            path = urp.path
        else:
            path = rawpath
        return os.path.basename(path)
    def _default_cb(self, button=None):
        dflt = self._get_default_target()
        self._target.set_text(dflt)
    def get_target(self):
        target = self._target.get_text()
        if not target:
            target = self._get_default_target()
        return target
    def _browse_cb(self, button=None):
        repo_uri = self.select_uri(_("Browse for Repository"))
        if repo_uri:
            parsed = urllib.parse.urlparse(repo_uri)
            if parsed.scheme and parsed.scheme != "file":
                self._path.set_text(repo_uri)
            else:
                self._path.set_text(utils.path_rel_home(parsed.path))

def add_repo_path(path):
    return RepoPathView.append_saved_path(path)
