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
import shlex

from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import GObject

from aipoed import enotify
from aipoed import runext
from aipoed import scm
from aipoed import utils

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
        store, selection = self.get_selection().get_selected_rows()
        if not selection:
            return None
        else:
            assert len(selection) == 1
        return store.get_remote_name(store.get_iter(selection[0]))
    def get_selected_remotes(self):
        store, selection = self.get_selection().get_selected_rows()
        return [store.get_remote_name(store.get_iter(x)) for x in selection]
    def _get_table_db(self):
        return RemoteRepoTableData()
    def handle_control_c_key_press_cb(self):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        sel = utils.quoted_join(self.get_selected_remotes())
        clipboard.set_text(sel, len(sel))

class RemotesList(table.TableWidget):
    VIEW = RemotesListView

class RemotesComboBox(Gtk.ComboBoxText):
    def __init__(self):
        Gtk.ComboBoxText.__init__(self)
        for line in runext.run_get_cmd(["git", "remote"], default="").splitlines():
            self.append_text(line)

class FetchWidget(Gtk.VBox):
    FLAGS = [
            ("--append",
             "Append ref names and object names of fetched refs to"
             + " the existing contents of .git/FETCH_HEAD. Without"
             + " this option old data in .git/FETCH_HEAD will be overwritten."
            ),
            ("--force",
             "When git fetch is used with <rbranch>:<lbranch> refspec,"
             + " it refuses to update the local branch <lbranch>"
             + " unless the remote branch <rbranch> it fetches is a"
             + " descendant of <lbranch>. This option overrides that check."
            ),
            ("--keep",
             "Keep downloaded pack."
            ),
            ("--prune",
             "Before fetching, remove any remote-tracking references"
             + " that no longer exist on the remote."
             + " Tags are not subject to pruning if they are fetched"
             + " only because of the default tag auto-following or"
             + " due to a --tags option. However, if tags are fetched"
             + " due to an explicit refspec (either on the command line"
             + " or in the remote configuration, for example if the remote"
             + " was cloned with the --mirror option), then they are"
             + " also subject to pruning."
            ),
            ("--no-tags",
             "By default, tags that point at objects that are"
             + " downloaded from the remote repository are fetched"
             + " and stored locally. This option disables this automatic"
             + " tag following. The default behavior for a remote may"
             + " be specified with the remote.<name>.tagOpt setting."
             + " See git-config[1]."
            ),
            ("--tags",
             "Fetch all tags from the remote (i.e., fetch remote"
             + " tags refs/tags/* into local tags with the same name),"
             + " in addition to whatever else would otherwise be fetched."
             + " Using this option alone does not subject tags to pruning,"
             + " even if --prune is used (though tags may be pruned anyway"
             + " if they are also the destination of an explicit refspec; see --prune)."
            ),
        ]
    REFSPEC_TT_TEXT = \
        "Specifies which refs to fetch and which local refs to update." \
        + " When no <refspec>s are given, the refs to fetch are read" \
        + " from remote.<repository>.fetch variables instead" \
        + " (see CONFIGURED REMOTE-TRACKING BRANCHES in 'git fetch --help').\n\n" \
        + "The format of a <refspec> parameter is an optional plus +," \
        + " followed by the source ref <src>, followed by a colon :," \
        + " followed by the destination ref <dst>." \
        + " The colon can be omitted when <dst> is empty.\n\n" \
        + " tag <tag> means the same as refs/tags/<tag>:refs/tags/<tag>;" \
        + " it requests fetching everything up to the given tag.\n\n" \
        + "The remote ref that matches <src> is fetched, and if <dst>" \
        + " is not empty string, the local ref that matches it is" \
        + " fast-forwarded using <src>. If the optional plus + is used," \
        + " the local ref is updated even if it does not result in a fast-forward update."
    def __init__(self):
        Gtk.VBox.__init__(self)
        self._all_flag = Gtk.CheckButton.new_with_label("--all")
        self._all_flag.set_tooltip_text(_("Fetch from all remotes"))
        self._all_flag.connect("toggled", self._all_toggle_cb)
        self._remote = RemotesComboBox()
        self._remote.connect("changed", self._remote_changed_cb)
        self._refspec = Gtk.Entry()
        self._refspec.set_tooltip_text(self.REFSPEC_TT_TEXT)
        hbox = Gtk.HBox()
        hbox.pack_start(self._all_flag, expand=False, fill=True, padding=0)
        hbox.pack_start(Gtk.Separator.new(Gtk.Orientation.VERTICAL), expand=False, fill=True, padding=5)
        hbox.pack_start(Gtk.Label(_("Remote:")), expand=False, fill=True, padding=2)
        hbox.pack_start(self._remote, expand=False, fill=True, padding=2)
        hbox.pack_start(Gtk.Label(_("RefSpec(s):")), expand=False, fill=True, padding=2)
        hbox.pack_start(self._refspec, expand=True, fill=True, padding=2)
        self.pack_start(hbox, expand=False, fill=False, padding=2)
        self.pack_start(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), expand=False, fill=True, padding=2)
        self._flags = list()
        hbox = Gtk.HBox()
        for flag_label, tt_text in self.FLAGS:
            chbtn = Gtk.CheckButton.new_with_label(flag_label)
            chbtn.set_tooltip_text(tt_text)
            self._flags.append(chbtn)
            hbox.pack_start(chbtn, expand=False, fill=True, padding=2)
        self.pack_start(hbox, expand=False, fill=False, padding=2)
        self.show_all()
        self._all_toggle_cb(self._all_flag)
    def _all_toggle_cb(self, button):
        if button.get_active():
            for widget in [self._remote, self._refspec]:
                widget.set_sensitive(False)
        else:
            self._remote.set_sensitive(True)
            self._remote_changed_cb(self._remote)
    def _remote_changed_cb(self, combo_box):
        valid_remote_seln = combo_box.get_active() != -1
        self._refspec.set_sensitive(valid_remote_seln)
    def do_fetch(self):
        from aipoed.git.gui import ifce
        flags = [chbtn.get_label() for chbtn in self._flags if chbtn.get_active()]
        cmd = ["git", "fetch"] + flags
        if self._all_flag.get_active():
            cmd += ["--all"]
        else:
            remote = self._remote.get_active_text()
            if remote:
                cmd += [remote] + shlex.split(self._refspec.get_text())
        return ifce.do_action_cmd(cmd, scm.E_FETCH, None, [])

class FetchDialog(dialogue.CancelOKDialog, dialogue.ClientMixin):
    def __init__(self, **kwargs):
        if "title" not in kwargs:
            kwargs["title"] = "fetch: {}".format(utils.cwd_rel_home())
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
