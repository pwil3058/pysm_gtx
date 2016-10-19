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

from aipoed import enotify
from aipoed import os_utils
from aipoed import scm
from aipoed import pm
from aipoed import utils

from aipoed.gui import actions
from aipoed.gui import dialogue
from aipoed.gui import file_tree
from aipoed.gui import xtnl_edit
from aipoed.gui import icons

from aipoed.git.gui import ifce
from aipoed.git.gui import do_opn

class WDTreeModel(file_tree.FileTreeModel):
    UPDATE_EVENTS = os_utils.E_FILE_CHANGES|scm.E_NEW_SCM|scm.E_FILE_CHANGES|pm.E_FILE_CHANGES|pm.E_PATCH_STACK_CHANGES|pm.E_PATCH_REFRESH|pm.E_POP|pm.E_PUSH|scm.E_WD_CHANGES
    AU_FILE_CHANGE_EVENT = scm.E_FILE_CHANGES|os_utils.E_FILE_CHANGES # event returned by auto_update() if changes found
    @staticmethod
    def _get_file_db():
        return scm.gui.ifce.SCM.get_wd_file_db()

class WDTreeView(file_tree.FileTreeView, enotify.Listener, scm.gui.actions.WDListenerMixin, pm.gui.actions.WDListenerMixin, do_opn.DoOpnMixin):
    MODEL = WDTreeModel
    UI_DESCR = \
    """
    <ui>
      <menubar name="wd_files_menubar">
        <menu name="wd_files_menu" action="wd_files_menu_files">
          <menuitem action="refresh_files"/>
        </menu>
      </menubar>
      <popup name="files_popup">
          <menuitem action="new_file"/>
        <separator/>
          <menuitem action="copy_fs_items"/>
          <menuitem action="move_fs_items"/>
          <menuitem action="rename_fs_item"/>
          <menuitem action="delete_fs_items"/>
      </popup>
      <popup name="scmic_files_popup">
        <placeholder name="selection_indifferent"/>
        <separator/>
        <placeholder name="selection">
          <separator/>
          <menuitem action="wd_edit_selected_files"/>
          <separator/>
          <menuitem action="wd_add_files_to_index"/>
          <menuitem action="wd_remove_files_in_index"/>
        </placeholder>
        <separator/>
        <placeholder name="unique_selection"/>
          <menuitem action="copy_file_to_index"/>
          <menuitem action="rename_file_in_index"/>
          <menuitem action="launch_diff_tool_re_head"/>
        <separator/>
          <menuitem action="copy_fs_items"/>
          <menuitem action="move_fs_items"/>
          <menuitem action="rename_fs_item"/>
          <menuitem action="delete_fs_items"/>
        <placeholder name="no_selection"/>
        <separator/>
        <separator/>
        <placeholder name="make_selections"/>
        <separator/>
      </popup>
      <popup name="pmic_files_popup"/>
    </ui>
    """
    def __init__(self, show_hidden=False, hide_clean=False):
        file_tree.FileTreeView.__init__(self, show_hidden=show_hidden, hide_clean=hide_clean)
        enotify.Listener.__init__(self)
        scm.gui.actions.WDListenerMixin.__init__(self)
        pm.gui.actions.WDListenerMixin.__init__(self)
        self._update_popup_cb()
        self.add_notification_cb(pm.E_PATCH_STACK_CHANGES|pm.E_NEW_PM|enotify.E_CHANGE_WD, self._update_popup_cb)
    def _update_popup_cb(self, **kwargs):
        if pm.gui.ifce.PM.is_poppable:
            self.set_popup("/pmic_files_popup")
        elif ifce.SCM.in_valid_pgnd:
            self.set_popup("/scmic_files_popup")
        else:
            self.set_popup(self.DEFAULT_POPUP)
    def populate_action_groups(self):
        self.action_groups[actions.AC_DONT_CARE].add_actions(
            [
                ('wd_files_menu_files', None, _('Working Directory')),
            ])
        self.action_groups[scm.gui.actions.AC_IN_SCM_PGND|pm.gui.actions.AC_NOT_PMIC|actions.AC_SELN_UNIQUE|file_tree.AC_ONLY_FILES_SELECTED].add_actions(
            [
                ("copy_file_to_index", Gtk.STOCK_COPY, _("Copy"), None,
                 _("Make a copy of the selected file in the index"),
                 lambda _action=None: self.git_do_copy_file_to_index(self.get_selected_fsi_path())
                ),
            ])
        self.action_groups[scm.gui.actions.AC_IN_SCM_PGND|pm.gui.actions.AC_NOT_PMIC|actions.AC_SELN_UNIQUE].add_actions(
            [
                ("rename_file_in_index", icons.STOCK_RENAME, _("Rename"), None,
                 _("Rename the selected file/directory in the index (i.e. git mv)"),
                 lambda _action=None: self.git_do_rename_fsi_in_index(self.get_selected_fsi_path())
                ),
            ])
        self.action_groups[scm.gui.actions.AC_IN_SCM_PGND|actions.AC_SELN_UNIQUE|file_tree.AC_ONLY_FILES_SELECTED].add_actions(
            [
                ("launch_diff_tool_re_head", icons.STOCK_DIFF, _("Difftool"), None,
                 _("Launch difftool for the selected file w.r.t. HEAD"),
                 lambda _action=None: ifce.SCM.launch_difftool("HEAD", "--", self.get_selected_fsi_path())
                ),
            ])
        self.action_groups[scm.gui.actions.AC_IN_SCM_PGND|pm.gui.actions.AC_NOT_PMIC|actions.AC_SELN_MADE].add_actions(
            [
                ("wd_add_files_to_index", Gtk.STOCK_ADD, _("Add"), None,
                 _("Run \"git add\" on the selected files/directories"),
                 lambda _action=None: self.git_do_add_fsis_to_index(self.get_selected_fsi_paths())
                ),
            ])
        self.action_groups[scm.gui.actions.AC_IN_SCM_PGND|pm.gui.actions.AC_NOT_PMIC|actions.AC_SELN_MADE|file_tree.AC_ONLY_FILES_SELECTED].add_actions(
            [
                ("wd_edit_selected_files", Gtk.STOCK_EDIT, _("Edit"), None,
                 _("Open the selected files for editing"),
                 lambda _action=None: xtnl_edit.edit_files_extern(self.get_selected_fsi_paths())
                ),
                # TODO: extend the "Remove" command to include directories
                ("wd_remove_files_in_index", Gtk.STOCK_REMOVE, _("Remove"), None,
                 _("Run \"git rm\" on the selected files"),
                 lambda _action=None: self.git_do_remove_files_in_index(self.get_selected_fsi_paths())
                ),
            ])

class WDFileTreeWidget(file_tree.FileTreeWidget):
    MENUBAR = "/wd_files_menubar"
    BUTTON_BAR_ACTIONS = ["show_hidden_files", "hide_clean_files"]
    TREE_VIEW = WDTreeView
    @staticmethod
    def get_menu_prefix():
        return ifce.SCM.name
