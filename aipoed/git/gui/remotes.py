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

from gi.repository import Gtk
from gi.repository import GObject

from aipoed import enotify
from aipoed import runext
from aipoed import scm

from aipoed.gui import actions
from aipoed.gui import dialogue
from aipoed.gui import icons
from aipoed.gui import table

RemotesListRow = collections.namedtuple("RemotesListRow",    ["name", "inbound_url", "outbound_url"])

class RemoteRepoTableData(table.TableData):
    _VREMOTE_RE = re.compile(r"(\S+)\s+(\S+)\s*(\S*)")
    def _get_data_text(self, h):
        text = runext.run_get_cmd(["git", "remote", "-v"], default="")
        h.update(text.encode())
        return text
    def _finalize(self, pdt):
        self._lines = pdt.splitlines()
    def iter_rows(self):
        for i, line in enumerate(self._lines):
            m = self._VREMOTE_RE.match(line)
            if i % 2 == 0:
                name, inbound_url = m.group(1, 2)
            else:
                assert name == m.group(1)
                yield RemotesListRow(name=name, inbound_url=inbound_url, outbound_url=m.group(2))

class RemotesListView(table.MapManagedTableView, scm.gui.actions.WDListenerMixin):
    class MODEL(table.MapManagedTableView.MODEL):
        ROW = RemotesListRow
        TYPES = ROW(name=GObject.TYPE_STRING, inbound_url=GObject.TYPE_STRING, outbound_url=GObject.TYPE_STRING,)
        def get_remote_name(self, plist_iter):
            return self.get_value_named(plist_iter, "name")
        def get_inbound_url(self, plist_iter):
            return self.get_value_named(plist_iter, "inbound_url")
        def get_outbound_url(self, plist_iter):
            return self.get_value_named(plist_iter, "outbound_url")
    PopUp = "/remotes_popup"
    SET_EVENTS = enotify.E_CHANGE_WD|scm.E_NEW_SCM
    REFRESH_EVENTS = scm.E_REMOTE
    AU_REQ_EVENTS = scm.E_REMOTE
    UI_DESCR = """
    <ui>
      <popup name="remotes_popup">
        <menuitem action="table_refresh_contents"/>
      </popup>
    </ui>
    """
    SPECIFICATION = table.simple_text_specification(MODEL, (_("Name"), "name", 0.0), (_("Inbound URL"), "inbound_url", 0.0), (_("Outbound URL"), "outbound_url", 0.0))
    def __init__(self, size_req=None):
        table.MapManagedTableView.__init__(self, size_req=size_req)
        scm.gui.actions.WDListenerMixin.__init__(self)
        self.set_contents()
    def get_selected_remote(self):
        store, store_iter = self.get_selection().get_selected()
        return None if store_iter is None else store.get_remote_name(store_iter)
    def _get_table_db(self):
        return RemoteRepoTableData()

class RemotesList(table.TableWidget):
    VIEW = RemotesListView

class RemotesComboBox(Gtk.ComboBoxText):
    def __init__(self):
        Gtk.ComboBoxText.__init__(self)
        for line in runext.run_get_cmd(["git", "remote"], default="").splitlines():
            self.append_text(line)

class FetchWidget(Gtk.VBox):
    def __init__(self):
        from aipoed.git.gui import branches
        Gtk.VBox.__init__(self)
        self._all_flag = Gtk.CheckButton.new_with_label("--all")
        self._all_flag.set_tooltip_text(_("Fetch from all remotes"))
        self._all_flag.connect("toggled", self._all_toggle_cb)
        self._remote = RemotesComboBox()
        self._remote.connect("changed", self._remote_changed_cb)
        self._branch = branches.BranchesComboBox()
        hbox = Gtk.HBox()
        hbox.pack_start(self._all_flag, expand=False, fill=True, padding=0)
        hbox.pack_start(Gtk.Label(_("Remote:")), expand=False, fill=True, padding=0)
        hbox.pack_start(self._remote, expand=True, fill=True, padding=0)
        hbox.pack_start(Gtk.Label(_("Branch:")), expand=False, fill=True, padding=0)
        hbox.pack_start(self._branch, expand=True, fill=True, padding=0)
        self.pack_start(hbox, expand=False, fill=False, padding=0)
        self.show_all()
        self._all_toggle_cb(self._all_flag)
    def _all_toggle_cb(self, button):
        if button.get_active():
            for widget in [self._remote, self._branch]:
                widget.set_sensitive(False)
        else:
            self._remote.set_sensitive(True)
            self._remote_changed_cb(self._remote)
    def _remote_changed_cb(self, combo_box):
        valid_remote_seln = combo_box.get_active() != -1
        self._branch.set_sensitive(valid_remote_seln)
    def do_fetch(self):
        from aipoed.git.gui import ifce
        cmd = ["git", "fetch"]
        if self._all_flag.get_active():
            cmd += ["--all"]
        else:
            remote = self._remote.get_active_text()
            if remote:
                cmd += [remote]
                branch = self._branch.get_active_text()
                if branch:
                    cmd += [branch]
        return ifce.do_action_cmd(cmd, scm.E_FETCH, None, [])

class FetchDialog(dialogue.CancelOKDialog, dialogue.ClientMixin):
    def __init__(self, **kwargs):
        dialogue.CancelOKDialog.__init__(self, **kwargs)
        self.fetch_widget = FetchWidget()
        self.get_content_area().add(self.fetch_widget)
        self.connect("response", self._response_cb)
        self.show_all()
    def _response_cb(self, _dialog, response):
        if response == Gtk.ResponseType.CANCEL:
            self.destroy()
        else:
            assert response == Gtk.ResponseType.OK
            with self.showing_busy():
                result = self.fetch_widget.do_fetch()
            self.report_any_problems(result)
            if result.is_less_than_error:
                self.destroy()

actions.CLASS_INDEP_AGS[scm.gui.actions.AC_IN_SCM_PGND].add_actions(
    [
        ("git_fetch_from_remote", icons.STOCK_FETCH, _("Fetch"), None,
         _("Fetch from a selected remote repository"),
         lambda _action=None: FetchDialog().show()
        ),
    ])
