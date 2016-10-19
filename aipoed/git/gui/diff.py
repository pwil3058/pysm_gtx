### Copyright (C) 2007-2015 Peter Williams <pwil3058@gmail.com>
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

import re
import os
import hashlib

from gi.repository import Gtk

from aipoed import CmdFailure
from aipoed import utils
from aipoed import runext

from aipoed.patch_diff.gui import diff

from aipoed.gui import dialogue
from aipoed.gui import gutils
from aipoed.gui import actions
from aipoed.gui import icons

class WdDiffTextWidget(diff.DiffTextsWidget, diff.FileAndRefreshActions):
    DIFF_MODES = ["git diff", "git diff --staged", "git diff HEAD"]
    def __init__(self):
        self.mode_button = {}
        button = None
        for mode in self.DIFF_MODES:
            self.mode_button[mode] = button = Gtk.RadioButton.new_with_label_from_widget(button, mode)
            button.connect("toggled", self._diff_mode_toggled_cb)
        diff.DiffTextsWidget.__init__(self)
        diff.FileAndRefreshActions.__init__(self)
        self.a_name_list = ["diff_save", "diff_save_as", "diff_refresh"]
        self.diff_buttons = gutils.ActionButtonList([self._action_group], self.a_name_list)
    def _get_diff_text(self):
        # TODO: think about making -M a selectable option
        cmd = ["git", "diff", "--no-ext-diff", "-M"]
        if self.mode_button["git diff --staged"].get_active():
            cmd.append("--staged")
        elif self.mode_button["git diff HEAD"].get_active():
            cmd.append("HEAD")
        try:
            return runext.run_get_cmd(cmd, do_rstrip=False)
        except CmdFailure as failure:
            dialogue.main_window.report_failure(failure)
            return failure.result.stdout
    def _diff_mode_toggled_cb(self, _data=None):
        self.update()
    def _refresh_acb(self, _action):
        self.update()
    def _get_text_to_save(self):
        return str(self)

class WdDiffTextDialog(dialogue.ListenerDialog):
    def __init__(self, parent=None):
        flags = Gtk.DialogFlags.DESTROY_WITH_PARENT
        dialogue.ListenerDialog.__init__(self, None, parent, flags, ())
        title = "diff: %s" % utils.cwd_rel_home()
        self.set_title(title)
        dtw = WdDiffTextWidget()
        hbox = Gtk.HBox()
        hbox.pack_start(Gtk.Label(_("Mode:")), expand=False, fill=True, padding=0)
        for key in dtw.DIFF_MODES:
            hbox.pack_start(dtw.mode_button[key],  expand=False, fill=True, padding=0)
        self.vbox.pack_start(hbox, expand=False, fill=True, padding=0)
        self.vbox.pack_start(dtw, expand=True, fill=True, padding=0)
        tws_display = dtw.tws_display
        self.action_area.pack_end(tws_display, expand=False, fill=False, padding=0)
        for button in dtw.diff_buttons.list:
            self.action_area.pack_start(button, expand=True, fill=True, padding=0)
        self.add_buttons(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        self.connect("response", self._close_cb)
        self.show_all()
    def _close_cb(self, dialog, response_id):
        dialog.destroy()

from aipoed.scm.gui.actions import AC_IN_SCM_PGND

actions.CLASS_INDEP_AGS[AC_IN_SCM_PGND].add_actions(
    [
        ("git_wd_diff_dialog", icons.STOCK_DIFF, _("_Diff"), None,
         _("View diffs for the working directory"),
         lambda _action: WdDiffTextDialog()
        ),
    ])
