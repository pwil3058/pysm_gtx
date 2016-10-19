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

from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import GObject

from aipoed import enotify
from aipoed import runext
from aipoed import scm
from aipoed import utils

from aipoed.gui import actions
from aipoed.gui import table
from aipoed.gui import icons

from aipoed.git.gui import ifce
from aipoed.git.gui import commit

LogListRow = collections.namedtuple("LogListRow",    ["commit", "abbrevcommit", "author", "when", "subject"])

class LogTableData(table.TableData):
    def _get_data_text(self, h):
        text = runext.run_get_cmd(["git", "log", "--pretty=format:%H%n%h%n%an%n%cr%n%s"], default="")
        h.update(text.encode())
        return text
    def _finalize(self, pdt):
        self._lines = pdt.splitlines()
    def iter_rows(self):
        for i, line in enumerate(self._lines):
            chooser = i % 5
            if chooser == 0:
                commit = line
            elif chooser == 1:
                abbrevcommit = line
            elif chooser == 2:
                author = line
            elif chooser == 3:
                when = line
            else:
                yield LogListRow(commit=commit, abbrevcommit=abbrevcommit, author=author, when=when, subject=line)

class LogListView(table.MapManagedTableView, scm.gui.actions.WDListenerMixin):
    class MODEL(table.MapManagedTableView.MODEL):
        ROW = LogListRow
        TYPES = ROW(commit=GObject.TYPE_STRING, abbrevcommit=GObject.TYPE_STRING, author=GObject.TYPE_STRING, when=GObject.TYPE_STRING, subject=GObject.TYPE_STRING,)
        def get_commit_sha1(self, plist_iter):
            return self.get_value_named(plist_iter, "commit")
        def get_commit_abbrev_sha1(self, plist_iter):
            return self.get_value_named(plist_iter, "abbrevcommit")
    PopUp = "/log_popup"
    SET_EVENTS = enotify.E_CHANGE_WD|scm.E_NEW_SCM
    REFRESH_EVENTS = scm.E_COMMIT|scm.E_CHECKOUT|scm.E_BRANCH|scm.E_MERGE|scm.E_LOG
    AU_REQ_EVENTS = scm.E_LOG
    UI_DESCR = """
    <ui>
      <popup name="log_popup">
        <menuitem action="show_selected_commit"/>
        <separator/>
        <menuitem action="table_refresh_contents"/>
      </popup>
    </ui>
    """
    SPECIFICATION = table.simple_text_specification(MODEL, ("Commit", "abbrevcommit", 0.0), ("Author", "author", 0.0), ("When", "when", 0.0), ("Subject", "subject", 0.0))
    def __init__(self, size_req=None):
        table.MapManagedTableView.__init__(self, size_req=size_req)
        scm.gui.actions.WDListenerMixin.__init__(self)
        self.set_contents()
    def populate_action_groups(self):
        self.action_groups[actions.AC_SELN_UNIQUE].add_actions(
            [
                ("show_selected_commit", icons.STOCK_CHECKOUT, _("Show"), None,
                 _("Show the details for the selected commit."), self._show_seln_acb),
            ])
    def get_selected_commit(self):
        store, selection = self.get_selection().get_selected_rows()
        if not selection:
            return None
        else:
            assert len(selection) == 1
        return store.get_commit_abbrev_sha1(store.get_iter(selection[0]))
    def get_selected_commits(self):
        store, selection = self.get_selection().get_selected_rows()
        return [store.get_commit_abbrev_sha1(store.get_iter(x)) for x in selection]
    def _get_table_db(self):
        return ifce.SCM.get_log_table_data()
    def _show_seln_acb(self, _action):
        # TODO: make show selected commit more user friendly
        commit_hash = self.get_selected_commit()
        commit.ShowCommitDialog(None, commit_hash).show()
    def handle_control_c_key_press_cb(self):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        sel = utils.quoted_join(self.get_selected_commits())
        clipboard.set_text(sel, len(sel))

class LogList(table.TableWidget):
    VIEW = LogListView
