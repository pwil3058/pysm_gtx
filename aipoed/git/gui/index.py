### Copyright (C) 2005-2015 Peter Williams <pwil3058@gmail.com>
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

import collections
import os
import shutil

from gi.repository import Gtk
from gi.repository import GObject

from aipoed import scm
from aipoed import utils

from aipoed.gui import actions
from aipoed.gui import dialogue
from aipoed.gui import file_tree
from aipoed.gui import icons

from aipoed import enotify

from aipoed.git.gui import ifce

class IndexFileTreeModel(file_tree.FileTreeModel):
    REPOPULATE_EVENTS = scm.E_CHECKOUT|enotify.E_CHANGE_WD
    UPDATE_EVENTS = scm.E_FILE_CHANGES|scm.E_INDEX_MOD
    AU_FILE_CHANGE_EVENT = scm.E_INDEX_MOD # event returned by auto_update() if changes found
    @staticmethod
    def _get_file_db():
        return ifce.SCM.get_index_file_db()

class IndexFileTreeView(file_tree.FileTreeView, enotify.Listener, scm.gui.actions.WDListenerMixin, dialogue.ClientMixin):
    MODEL = IndexFileTreeModel
    UI_DESCR = '''
    <ui>
      <menubar name="index_files_menubar">
        <menu name="index_files_menu" action="index_files_menu_files">
          <menuitem action="refresh_files"/>
        </menu>
      </menubar>
      <popup name="files_popup">
        <placeholder name="selection_indifferent"/>
        <separator/>
        <placeholder name="selection">
          <menuitem action="index_unstage_selected_files"/>
        </placeholder>
        <separator/>
        <placeholder name="unique_selection"/>
        <separator/>
        <placeholder name="no_selection"/>
        <separator/>
        <separator/>
        <placeholder name="make_selections"/>
        <separator/>
      </popup>
    </ui>
    '''
    _FILE_ICON = {True : Gtk.STOCK_DIRECTORY, False : Gtk.STOCK_FILE}
    AUTO_EXPAND = True
    def __init__(self, hide_clean=False, **kwargs):
        file_tree.FileTreeView.__init__(self, hide_clean=hide_clean)
        enotify.Listener.__init__(self)
        scm.gui.actions.WDListenerMixin.__init__(self)
    def populate_action_groups(self):
        self.action_groups[actions.AC_DONT_CARE].add_actions(
            [
                ('index_files_menu_files', None, _('Staged _Files')),
            ])
        self.action_groups[scm.gui.actions.AC_IN_SCM_PGND|actions.AC_SELN_MADE].add_actions(
            [
                ('index_unstage_selected_files', Gtk.STOCK_REMOVE, _('_Unstage'), None,
                 _('Remove/unstage the selected files/directories from the index'), self.unstage_selected_files_acb),
            ])
    def unstage_selected_files_acb(self, _action=None):
        file_list = self.get_selected_fsi_paths()
        if len(file_list) == 0:
            return
        with self.showing_busy():
            result = ifce.SCM.do_remove_files_from_index(file_list)
        self.report_any_problems(result)

class IndexFileTreeWidget(file_tree.FileTreeWidget):
    MENUBAR = "/index_files_menubar"
    BUTTON_BAR_ACTIONS = ["hide_clean_files"]
    TREE_VIEW = IndexFileTreeView
    #SIZE = (240, 320)
