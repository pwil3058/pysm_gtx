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
