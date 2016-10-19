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
from gi.repository import Gdk
from gi.repository import GObject

from aipoed import enotify
from aipoed import runext
from aipoed import scm
from aipoed import utils

from aipoed.gui import actions
from aipoed.gui import dialogue
from aipoed.gui import table
from aipoed.gui import tlview
from aipoed.gui import icons

from aipoed.git.gui import do_opn

BranchListRow = collections.namedtuple("BranchListRow", ["name", "is_current", "is_merged", "rev", "synopsis"])

_MURow = collections.namedtuple("_MURow", ["name", "is_current", "is_merged", "rev", "synopsis", "icon", "markup"])

def _mark_up_row(row):
    if row.is_current == "*":
        icon = icons.STOCK_CURRENT_BRANCH
        markup = "<b><span foreground=\"green\">{0}</span></b>".format(row.name)
    elif row.is_merged:
        icon = None
        markup = "<span foreground=\"green\">{0}</span>".format(row.name)
    else:
        icon = None
        markup = row.name
    return _MURow(row.name, row.is_current, row.is_merged, row.rev, row.synopsis, icon, markup)

class BranchListModel(table.MapManagedTableView.MODEL):
    ROW = _MURow
    TYPES = ROW(
        name=GObject.TYPE_STRING,
        is_current=GObject.TYPE_STRING,
        is_merged=GObject.TYPE_BOOLEAN,
        rev=GObject.TYPE_STRING,
        synopsis=GObject.TYPE_STRING,
        icon=GObject.TYPE_STRING,
        markup=GObject.TYPE_STRING,
    )
    def get_branch_name(self, plist_iter):
        return self.get_value_named(plist_iter, "name")
    def get_branch_is_current(self, plist_iter):
        return self.get_value_named(plist_iter, "is_current") is "*"
    def get_branch_is_merged(self, plist_iter):
        return self.get_value_named(plist_iter, "is_merged")

class BranchTableData(table.TableData):
    RE = re.compile("(([^ (]+)|(\([^)]+\)))\s+([a-fA-F0-9]{7}[a-fA-F0-9]*)?\s*([^\s].*)")
    def _get_data_text(self, h):
        all_branches_text = runext.run_get_cmd(["git", "branch", "-vv"], default="")
        h.update(all_branches_text.encode())
        merged_branches_text = runext.run_get_cmd(["git", "branch", "--merged"], default="")
        h.update(merged_branches_text.encode())
        return (all_branches_text, merged_branches_text)
    def _finalize(self, pdt):
        all_branches_text, merged_branches_text = pdt
        self._lines = all_branches_text.splitlines()
        self._merged_branches = {line[2:].strip() for line in merged_branches_text.splitlines()}
    def iter_rows(self):
        for line in self._lines:
            is_current = line[0]
            name, rev, synopsis = self.RE.match(line[2:]).group(1, 4, 5)
            is_merged = name in self._merged_branches
            yield BranchListRow(name=name, is_current=is_current, is_merged=is_merged, rev=rev, synopsis=synopsis)

class BranchListView(table.MapManagedTableView, scm.gui.actions.WDListenerMixin, do_opn.DoOpnMixin):
    MODEL = BranchListModel
    PopUp = "/branches_popup"
    SET_EVENTS = enotify.E_CHANGE_WD|scm.E_NEW_SCM
    REFRESH_EVENTS = scm.E_BRANCH|scm.E_CHECKOUT
    AU_REQ_EVENTS = scm.E_BRANCH
    UI_DESCR = """
    <ui>
      <popup name="branches_popup">
        <menuitem action="checkout_selected_branch"/>
        <separator/>
        <menuitem action="table_refresh_contents"/>
      </popup>
    </ui>
    """
    SPECIFICATION = tlview.ViewSpec(
        properties={
            "enable-grid-lines" : False,
            "reorderable" : False,
            "rules_hint" : False,
            "headers-visible" : True,
        },
        selection_mode=Gtk.SelectionMode.MULTIPLE,
        columns=[
            tlview.simple_column("", tlview.stock_icon_cell(BranchListModel, "icon")),
            tlview.simple_column(_("Name"), tlview.mark_up_cell(BranchListModel, "markup")),
        ] + [tlview.simple_column(hdr, tlview.fixed_text_cell(BranchListModel, fld, xalign)) for hdr, fld, xalign in ((_("Rev"), "rev", 0.0), (_("Synopsis"), "synopsis", 0.0))]
    )
    def __init__(self, size_req=None):
        table.MapManagedTableView.__init__(self, size_req=size_req)
        scm.gui.actions.WDListenerMixin.__init__(self)
        self.set_contents()
    def populate_action_groups(self):
        self.action_groups[actions.AC_SELN_UNIQUE].add_actions(
            [
                ("checkout_selected_branch", icons.STOCK_CHECKOUT, _("Checkout"), None,
                 _("Checkout the selected branch in the current working directory"),
                 lambda _action: self.git_do_checkout_branch(self.get_selected_branch())
                ),
            ])
    def _fetch_contents(self, **kwargs):
        for row in table.MapManagedTableView._fetch_contents(self, **kwargs):
            yield _mark_up_row(row)
    def get_selected_branch(self):
        store, selection = self.get_selection().get_selected_rows()
        if not selection:
            return None
        else:
            assert len(selection) == 1
        return store.get_branch_name(store.get_iter(selection[0]))
    def get_selected_branches(self):
        store, selection = self.get_selection().get_selected_rows()
        return [store.get_branch_name(store.get_iter(x)) for x in selection]
    def _get_table_db(self):
        return BranchTableData()
    def handle_control_c_key_press_cb(self):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        sel = utils.quoted_join(self.get_selected_branches())
        clipboard.set_text(sel, len(sel))

class BranchList(table.TableWidget):
    VIEW = BranchListView

class CreateBranchDialog(dialogue.ReadTextAndToggleDialog, do_opn.DoOpnMixin):
    def __init__(self, target=None, parent=None):
        self._target = target
        dialogue.ReadTextAndToggleDialog.__init__(self, title=_("git: Set Branch"),
            prompt=_("Branch:"), toggle_prompt=_("Checkout"), toggle_state=False, parent=parent)
        self.connect("response", self._response_cb)
        self.show_all()
    def _response_cb(self, dialog, response_id):
        self.hide()
        if response_id == Gtk.ResponseType.CANCEL:
            self.destroy()
            return
        branch_name = self.git_do_create_branch(self.entry.get_text(), self._target)
        if branch_name and self.toggle.get_active():
            self.git_do_checkout_branch(branch_name)
        self.destroy()

# TODO: be more fussy about when set branch enabled?
actions.CLASS_INDEP_AGS[scm.gui.actions.AC_IN_SCM_PGND].add_actions(
    [
        ("git_branch_current_head", icons.STOCK_BRANCH, _("Branch"), None,
         _("Create a branch based on the current HEAD and (optionally) check it out"),
         lambda _action=None: CreateBranchDialog().show()
        ),
    ])

class BranchesComboBox(Gtk.ComboBoxText):
    def __init__(self):
        Gtk.ComboBoxText.__init__(self)
        current_branch_index = None
        for i, line in enumerate(runext.run_get_cmd(["git", "branch"], default="").splitlines()):
            if line.startswith("*"):
                current_branch_index = i
            self.append_text(line[2:])
        self.set_active(current_branch_index)
