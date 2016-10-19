### Copyright (C) 2013 Peter Williams <pwil3058@gmail.com>
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
import re

from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import GObject

from aipoed import enotify
from aipoed import CmdFailure
from aipoed import runext
from aipoed import scm
from aipoed import utils

from aipoed.gui import actions
from aipoed.gui import dialogue
from aipoed.gui import table
from aipoed.gui import text_edit
from aipoed.gui import icons

from aipoed.patch_diff.gui import diff

from aipoed import utils

from aipoed.git.gui import ifce

StashListRow = collections.namedtuple("StashListRow",    ["name", "branch", "commit"])

class StashTableData(table.TableData):
    RE = re.compile("^(stash@{\d+}):\s*([^:]+):(.*)")
    def _get_data_text(self, h):
        text = runext.run_get_cmd(["git", "stash", "list"], default="")
        h.update(text.encode())
        return text
    def _finalize(self, pdt):
        self._lines = pdt.splitlines()
    def iter_rows(self):
        for line in self._lines:
            m = self.RE.match(line)
            yield StashListRow(*m.groups())

class StashListView(table.MapManagedTableView, scm.gui.actions.WDListenerMixin):
    class MODEL(table.MapManagedTableView.MODEL):
        ROW = StashListRow
        TYPES = ROW(name=GObject.TYPE_STRING, branch=GObject.TYPE_STRING, commit=GObject.TYPE_STRING,)
        def get_stash_name(self, plist_iter):
            return self.get_value_named(plist_iter, "name")
        def get_branch(self, plist_iter):
            return self.get_value_named(plist_iter, "branch")
        def get_commit(self, plist_iter):
            return self.get_value_named(plist_iter, "commit")
    PopUp = "/stashes_popup"
    SET_EVENTS = enotify.E_CHANGE_WD|scm.E_NEW_SCM
    REFRESH_EVENTS = scm.E_STASH
    AU_REQ_EVENTS = scm.E_STASH
    UI_DESCR = """
    <ui>
      <popup name="stashes_popup">
        <menuitem action="show_selected_stash"/>
        <separator/>
        <menuitem action="pop_selected_stash"/>
        <menuitem action="apply_selected_stash"/>
        <menuitem action="branch_selected_stash"/>
        <separator/>
        <menuitem action="drop_selected_stash"/>
        <separator/>
        <menuitem action="table_refresh_contents"/>
      </popup>
    </ui>
    """
    SPECIFICATION = table.simple_text_specification(MODEL, (_("Name"), "name", 0.0), (_("Branch"), "branch", 0.0), (_("Commit"), "commit", 0.0),)
    def __init__(self, size_req=None):
        table.MapManagedTableView.__init__(self, size_req=size_req)
        scm.gui.actions.WDListenerMixin.__init__(self)
        self.set_contents()
    def populate_action_groups(self):
        self.action_groups[actions.AC_SELN_UNIQUE].add_actions(
            [
                ("show_selected_stash", icons.STOCK_STASH_SHOW, _("Show"), None,
                  _("Show the contents of the selected stash."),
                  lambda _action=None: StashDiffDialog(stash=self.get_selected_stash()).show()
                ),
                ("pop_selected_stash", icons.STOCK_STASH_POP, _("Pop"), None,
                  _("Pop the selected stash."),
                  lambda _action=None: PopStashDialog(stash=self.get_selected_stash(), parent=dialogue.main_window).show()
                ),
                ("apply_selected_stash", icons.STOCK_STASH_APPLY, _("Apply"), None,
                  _("Apply the selected stash."),
                  lambda _action=None: ApplyStashDialog(stash=self.get_selected_stash(), parent=dialogue.main_window).show()
                ),
                ("branch_selected_stash", icons.STOCK_STASH_BRANCH, _("Branch"), None,
                  _("Branch the selected stash."),
                  lambda _action=None: BranchStashDialog(stash=self.get_selected_stash(), parent=dialogue.main_window).show()
                ),
                ("drop_selected_stash", icons.STOCK_STASH_DROP, _("Drop"), None,
                  _("Drop the selected stash."),
                  lambda _action=None: drop_named_stash(stash=self.get_selected_stash())
                ),
            ])
    def get_selected_stash(self):
        store, selection = self.get_selection().get_selected_rows()
        if not selection:
            return None
        else:
            assert len(selection) == 1
        return store.get_stash_name(store.get_iter(selection[0]))
    def get_selected_stashes(self):
        store, selection = self.get_selection().get_selected_rows()
        return [store.get_stash_name(store.get_iter(x)) for x in selection]
    def _get_table_db(self):
        return ifce.SCM.get_stashes_table_data()
    def handle_control_c_key_press_cb(self):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        sel = utils.quoted_join(self.get_selected_stashes())
        clipboard.set_text(sel, len(sel))

class StashList(table.TableWidget):
    VIEW = StashListView

class CreateStashDialog(dialogue.Dialog):
    def __init__(self, parent=None):
        dialogue.Dialog.__init__(self, title=_("gwsmgitd: Stash Current State"), parent=parent, buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self.connect("response", self._response_cb)
        self.keep_index = Gtk.CheckButton("--keep-index")
        self.vbox.pack_start(self.keep_index, expand=False, fill=False, padding=0)
        self.include_untracked = Gtk.CheckButton("--include-untracked")
        self.vbox.pack_start(self.include_untracked, expand=False, fill=False, padding=0)
        self.include_all = Gtk.CheckButton("--all")
        self.vbox.pack_start(self.include_all, expand=False, fill=False, padding=0)
        for check_button in [self.include_untracked, self.include_all]:
            check_button.connect("toggled", self._include_toggled_cb)
        hbox = Gtk.HBox()
        hbox.pack_start(Gtk.Label(_("Message")), expand=False, fill=False, padding=0)
        self.vbox.pack_start(hbox, expand=False, fill=True, padding=0)
        self.message = text_edit.MessageWidget()
        self.vbox.pack_start(self.message, expand=False, fill=False, padding=0)
        self.show_all()
    def _include_toggled_cb(self, check_button):
        if check_button.get_active():
            if check_button is self.include_untracked:
                self.include_all.set_active(False)
            else:
                self.include_untracked.set_active(False)
    def _response_cb(self, dialog, response_id):
        self.hide()
        if response_id == Gtk.ResponseType.OK:
            with dialogue.main_window.showing_busy():
                result = ifce.SCM.do_stash_save(keep_index=self.keep_index.get_active(), include_untracked=self.include_untracked.get_active(), include_all=self.include_all.get_active(), msg=self.message.get_contents())
            dialogue.main_window.report_any_problems(result)
        self.destroy()

class PopStashDialog(dialogue.Dialog):
    TITLE = _("gwsmgitd: Pop Stash")
    CMD = "do_stash_pop"
    def __init__(self, stash=None, parent=None):
        self._stash = stash
        if stash:
            title = self.TITLE + " \"{0}\"".format(stash)
        else:
            title = self.TITLE
        dialogue.Dialog.__init__(self, title=title, parent=parent, buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self.connect("response", self._response_cb)
        self.reinstate_index = Gtk.CheckButton("--index")
        self.vbox.pack_start(self.reinstate_index, expand=False, fill=False, padding=0)
        self.show_all()
    def _response_cb(self, dialog, response_id):
        self.hide()
        if response_id == Gtk.ResponseType.OK:
            with dialogue.main_window.showing_busy():
                result = getattr(ifce.SCM, self.CMD)(reinstate_index=self.reinstate_index.get_active(), stash=self._stash)
            dialogue.main_window.report_any_problems(result)
        self.destroy()

class ApplyStashDialog(PopStashDialog):
    TITLE = _("gwsmgitd: Apply Stash")
    CMD = "do_stash_apply"

class BranchStashDialog(dialogue.ReadTextDialog):
    TITLE = _("gwsmgitd: Branch Stash")
    def __init__(self, stash=None, parent=None):
        self._stash = stash
        if stash:
            title = self.TITLE + " \"{0}\"".format(stash)
        else:
            title = self.TITLE
        dialogue.ReadTextDialog.__init__(self, title=title, prompt=_("Branch Name:"), parent=None)
        self.connect("response", self._response_cb)
    def _response_cb(self, dialog, response_id):
        self.hide()
        if response_id == Gtk.ResponseType.OK:
            branch_name = self.entry.get_text()
            with dialogue.main_window.showing_busy():
                result = ifce.SCM.do_stash_branch(branch_name=branch_name, stash=self._stash)
            dialogue.main_window.report_any_problems(result)
        self.destroy()

class StashDiffNotebook(diff.DiffTextsWidget):
    def __init__(self, stash=None):
        self._stash = stash if stash else "stash@{0}"
        diff.DiffTextsWidget.__init__(self)
    def _get_diff_text(self):
        try:
            return ifce.SCM.get_stash_diff(self._stash)
        except CmdFailure as failure:
            dialogue.main_window.report_failure(failure)
            return failure.result.stdout
    @property
    def window_title(self):
        return _("Stash \"{0}\" diff: {1}").format(self._stash, utils.cwd_rel_home())

class StashDiffDialog(diff.GenericDiffDialog):
    DIFFS_WIDGET = StashDiffNotebook

def drop_named_stash(stash):
    if dialogue.main_window.ask_ok_cancel(_("Confirm Drop Stash: {0}?").format(stash)):
        with dialogue.main_window.showing_busy():
            result = ifce.SCM.do_stash_drop(stash=stash)
        dialogue.main_window.report_any_problems(result)

actions.CLASS_INDEP_AGS[scm.gui.actions.AC_IN_SCM_PGND].add_actions(
    [
        ("git_stash_current_state", icons.STOCK_STASH_SAVE, _("Save"), None,
         _("Stash the current state."),
         lambda _action=None: CreateStashDialog().show()
        ),
    ])
