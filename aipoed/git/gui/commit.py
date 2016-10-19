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

from gi.repository import Gtk

from aipoed import enotify
from aipoed import CmdFailure
from aipoed import scm
from aipoed import utils

from aipoed.patch_diff import patchlib

from aipoed.gui import actions
from aipoed.gui import dialogue
from aipoed.gui import gutils
from aipoed.gui import textview
from aipoed.gui import text_edit
from aipoed.gui import icons

from aipoed.patch_diff.gui import diff

from aipoed.git.gui import ifce

class StagedDiffNotebook(diff.DiffTextsWidget):
    def __init__(self):
        diff.DiffTextsWidget.__init__(self)
    def _get_diff_text(self):
        # TODO: think about making -M a selectable option
        try:
            return ifce.SCM.get_diff('-M', '--staged')
        except CmdFailure as failure:
            dialogue.main_window.report_failure(failure)
            return failure.result.stdout

class MessageWidget(text_edit.MessageWidget):
    UI_DESCR = \
        '''
        <ui>
          <menubar name="commit_summary_menubar">
            <menu name="commit_summary_menu" action="menu_summary">
              <menuitem action="text_edit_save_to_file"/>
              <menuitem action="text_edit_save_as"/>
              <menuitem action="text_edit_load_fm_file"/>
              <menuitem action="text_edit_load_from"/>
              <menuitem action="text_edit_insert_from"/>
            </menu>
          </menubar>
          <toolbar name="commit_summary_toolbar">
            <toolitem action="text_edit_ack"/>
            <toolitem action="text_edit_sign_off"/>
            <toolitem action="text_edit_author"/>
          </toolbar>
        </ui>
        '''
    get_user_name_and_email = lambda _self: ifce.SCM.get_author_name_and_email()
    def populate_action_groups(self):
        self.action_groups[0].add_actions(
            [
                ("menu_summary", None, _('_Message')),
            ])
    def set_initial_contents(self):
        self.set_contents(ifce.SCM.get_commit_template())

class CommitWidget(Gtk.VPaned, enotify.Listener):
    DIFF_NOTEBOOK = StagedDiffNotebook
    def __init__(self):
        Gtk.VPaned.__init__(self)
        enotify.Listener.__init__(self)
        # TextView for change message
        self.msg_widget = MessageWidget()
        vbox = Gtk.VBox()
        hbox = Gtk.HBox()
        menubar = self.msg_widget.ui_manager.get_widget('/commit_summary_menubar')
        hbox.pack_start(menubar, fill=False, expand=False, padding=0)
        auto_save_action = self.msg_widget.action_groups.get_action("text_edit_toggle_auto_save")
        hbox.pack_end(gutils.ActionCheckButton(auto_save_action), fill=False, expand=False, padding=0)
        toolbar = self.msg_widget.ui_manager.get_widget('/commit_summary_toolbar')
        toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        toolbar.set_orientation(Gtk.Orientation.HORIZONTAL)
        hbox.pack_end(toolbar, fill=False, expand=False, padding=0)
        vbox.pack_start(hbox, expand=False, fill=False, padding=0)
        vbox.pack_start(self.msg_widget, expand=True, fill=True, padding=0)
        self.add1(vbox)
        # diffs of files in the commit
        self.note_book = self.DIFF_NOTEBOOK()
        vbox = Gtk.VBox()
        hbox = Gtk.HBox()
        hbox.pack_start(Gtk.Label(_('Diffs')), fill=True, expand=False, padding=0)
        hbox.pack_end(self.note_book.tws_display, expand=False, fill=False, padding=0)
        vbox.pack_start(hbox, expand=False, fill=True, padding=0)
        vbox.pack_start(self.note_book, expand=True, fill=True, padding=0)
        vbox.show_all()
        self.add2(vbox)
        self.show_all()
        self.add_notification_cb(scm.E_INDEX_MOD, self._update_cb)
        self.set_focus_child(self.msg_widget)
    def get_msg(self):
        return self.msg_widget.get_contents()
    def do_commit(self):
        result = ifce.SCM.do_commit_staged_changes(self.get_msg())
        dialogue.main_window.report_any_problems(result)
        return result.is_less_than_error
    def _update_cb(self, **kwargs):
        self.note_book.update()

class CommitDialog(dialogue.ListenerDialog):
    COMMIT_WIDGET = CommitWidget
    def __init__(self, parent=None):
        flags = Gtk.DialogFlags.DESTROY_WITH_PARENT
        dialogue.ListenerDialog.__init__(self, None, parent, flags)
        self.set_title(_('Commit Staged Changes: %s') % utils.cwd_rel_home())
        self.commit_widget = self.COMMIT_WIDGET()
        self.vbox.pack_start(self.commit_widget, expand=True, fill=True, padding=0)
        self.set_focus_child(self.commit_widget.msg_widget)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                       Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self.connect('response', self._handle_response_cb)
    def _finish_up(self, clear_save=False):
        with self.showing_busy():
            self.commit_widget.msg_widget.finish_up(clear_save)
        self.destroy()
    def _handle_response_cb(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            if self.commit_widget.do_commit():
                self._finish_up(clear_save=True)
            else:
                dialog.update_diffs()
        elif self.commit_widget.msg_widget.bfr.get_modified():
            if self.commit_widget.msg_widget.get_auto_save():
                self._finish_up()
            else:
                qtn = _('Unsaved changes to summary will be lost.\n\nCancel anyway?')
                if dialogue.main_window.ask_yes_no(qtn):
                    self._finish_up()
        else:
            self._finish_up()
    def update_diffs(self):
        self.commit_widget.note_book.update()

class AmendCommitWidget(CommitWidget):
    def __init__(self):
        CommitWidget.__init__(self)
        last_msg = ifce.SCM.get_commit_message()
        if last_msg:
            self.msg_widget.set_contents(last_msg)
    def do_commit(self):
        result = ifce.SCM.do_amend_commit(self.get_msg())
        dialogue.main_window.report_any_problems(result)
        return result.is_less_than_error

class AmendCommitDialog(CommitDialog):
    COMMIT_WIDGET = AmendCommitWidget
    def __init__(self, parent=None):
        CommitDialog.__init__(self, parent)
        self.set_title(_('Amend Last Commit: %s') % utils.cwd_rel_home())

class ShowCommitData:
    def __init__(self, commit_hash):
        self.source_name = commit_hash
        self.num_strip_levels = 1
        lines = ifce.SCM.get_commit_show(commit_hash).splitlines(True)
        diff_starts_at = None
        self.diff_pluses = list()
        index = 0
        last_diff_plus = None
        while index < len(lines):
            raise_if_malformed = diff_starts_at is not None
            starts_at = index
            diff_plus, index = patchlib.DiffPlus.get_diff_plus_at(lines, index, raise_if_malformed)
            if diff_plus:
                if diff_starts_at is None:
                    diff_starts_at = starts_at
                self.diff_pluses.append(diff_plus)
                last_diff_plus = diff_plus
                continue
            elif last_diff_plus:
                last_diff_plus.trailing_junk.append(lines[index])
            index += 1
        self.header = ''.join(lines[0:diff_starts_at])
    def __str__(self):
        string = '' if self.header is None else str(self.header)
        for diff_plus in self.diff_pluses:
            string += str(diff_plus)
        return string
    def get_file_paths(self, strip_level=None):
        strip_level = self._adjusted_strip_level(strip_level)
        return [diff_plus.get_file_path(strip_level=strip_level) for diff_plus in self.diff_pluses]
    def get_file_paths_plus(self, strip_level=None):
        strip_level = self._adjusted_strip_level(strip_level)
        return [diff_plus.get_file_path_plus(strip_level=strip_level) for diff_plus in self.diff_pluses]
    def get_diffstat_stats(self, strip_level=None):
        strip_level = self._adjusted_strip_level(strip_level)
        return patchlib.DiffStat.PathStatsList([patchlib.DiffStat.PathStats(diff_plus.get_file_path(strip_level=strip_level), diff_plus.get_diffstat_stats()) for diff_plus in self.diff_pluses])
    def report_trailing_whitespace(self, strip_level=None):
        strip_level = self._adjusted_strip_level(strip_level)
        reports = []
        for diff_plus in self.diff_pluses:
            bad_lines = diff_plus.report_trailing_whitespace()
            if bad_lines:
                path = diff_plus.get_file_path(strip_level=strip_level)
                reports.append(_FILE_AND_TWS_LINES(path, bad_lines))
        return reports

class ShowCommitWidget(Gtk.VPaned):
    def __init__(self, commit_hash):
        Gtk.VPaned.__init__(self)
        commit_data = ShowCommitData(commit_hash)
        # Simple display of header data for the time being
        vbox = Gtk.VBox()
        hbox = Gtk.HBox()
        hbox.pack_start(Gtk.Label(_('Header')), fill=True, expand=False, padding=0)
        vbox.pack_start(hbox, expand=False, fill=True, padding=0)
        self.header = textview.Widget(aspect_ratio=0.25)
        self.header.set_contents(commit_data.header)
        self.header.view.set_editable(False)
        self.header.view.set_cursor_visible(False)
        vbox.pack_start(self.header, expand=True, fill=True, padding=0)
        self.add1(vbox)
        # diffs of files in the commit
        self.note_book = diff.DiffPlusNotebook(commit_data.diff_pluses)
        vbox = Gtk.VBox()
        hbox = Gtk.HBox()
        hbox.pack_start(Gtk.Label(_('Diffs')), fill=True, expand=False, padding=0)
        hbox.pack_end(self.note_book.tws_display, expand=False, fill=False, padding=0)
        vbox.pack_start(hbox, expand=False, fill=True, padding=0)
        vbox.pack_start(self.note_book, expand=True, fill=True, padding=0)
        vbox.show_all()
        self.add2(vbox)
        self.show_all()

class ShowCommitDialog(dialogue.ListenerDialog):
    def __init__(self, parent, commit_hash):
        flags = Gtk.DialogFlags.DESTROY_WITH_PARENT
        dialogue.ListenerDialog.__init__(self, None, parent, flags, buttons=(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))
        self.set_title(_('Show Commit: {}: {}').format(commit_hash, utils.cwd_rel_home()))
        self.vbox.pack_start(ShowCommitWidget(commit_hash), expand=True, fill=True, padding=0)
        self.connect('response', self._handle_response_cb)
    def _handle_response_cb(self, dialog, response_id):
        self.destroy()

actions.CLASS_INDEP_AGS[scm.gui.actions.AC_IN_SCM_PGND].add_actions(
    [
        # TODO: be more fussy about when staged commit enabled?
        ('git_commit_staged_changes', icons.STOCK_COMMIT, _('Commit'), None,
         _('Commit the staged changes'),
         lambda _action: CommitDialog().show()
        ),
        # TODO: be more fussy about when amend commit enabled?
        ('git_amend_last_commit', icons.STOCK_AMEND_COMMIT, _('Amend'), None,
         _('Amend the last commit'),
         lambda _action: AmendCommitDialog().show()
        ),
    ])
