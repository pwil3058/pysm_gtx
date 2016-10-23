### -*- coding: utf-8 -*-
###
###  Copyright (C) 2016 Peter Williams <pwil3058@gmail.com>
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

import html
import os

from contextlib import contextmanager

from gi.repository import Gtk
from gi.repository import Gdk

from ... import ISSUES_URL, ISSUES_EMAIL, ISSUES_VERSION

from ..bab import enotify
from ..bab.decorators import singleton

from ..gui import yield_to_pending_events

BUG_REPORT_REQUEST_MSG = \
_("""<b>Please report this problem by either:
  submitting a bug report at &lt;{url}&gt;
or:
  e-mailing &lt;{email}&gt;
quoting version \"{version}\" and including a copy of the details
below this message.

Thank you.</b>
""").format(url=html.escape(ISSUES_URL), email=html.escape(ISSUES_EMAIL), version=html.escape(ISSUES_VERSION))


# parent for windows/dialogs that would otherwise be orphans
main_window = None

class BusyIndicator:
    def __init__(self, parent=None):
        self._bi_parent = parent
        self._bi_depth = 0
        self.connect("destroy", lambda _widget: self._turn_off_busy())
    def _turn_off_busy(self):
        while self.is_busy:
            self.unshow_busy()
    def show_busy(self):
        if self._bi_parent and self.get_modal():
            self._bi_parent.show_busy()
        self._bi_depth += 1
        if self._bi_depth == 1:
            window = self.get_window()
            if window is not None:
                window.set_cursor(Gdk.Cursor.new(Gdk.CursorType.WATCH))
                yield_to_pending_events()
    def unshow_busy(self):
        if self._bi_parent and self.get_modal():
            self._bi_parent.unshow_busy()
        self._bi_depth -= 1
        assert self._bi_depth >= 0
        if self._bi_depth == 0:
            window = self.get_window()
            if window is not None:
                window.set_cursor(None)
                yield_to_pending_events()
    @contextmanager
    def showing_busy(self):
        self.show_busy()
        try:
            yield
        finally:
            self.unshow_busy()
    @property
    def is_busy(self):
        return self._bi_depth > 0

class BusyIndicatorUser:
    @contextmanager
    def showing_busy(self):
        # NB: need to cater for the case where called before all the packing is complete
        tl = self.get_toplevel()
        if tl.is_toplevel():
            tl.show_busy()
            try:
                yield
            finally:
                tl.unshow_busy()
        else:
            yield

class Window(Gtk.Window, BusyIndicator):
    def __init__(self, *args, **kwargs):
        if not kwargs.get("parent", None):
            kwargs["parent"] = main_window
        Gtk.Window.__init__(self, *args, **kwargs)
        BusyIndicator.__init__(self)

class Dialog(Gtk.Dialog, BusyIndicator):
    def __init__(self, *args, **kwargs):
        if not kwargs.get("parent", None):
            kwargs["parent"] = main_window
        Gtk.Dialog.__init__(self, *args, **kwargs)
        BusyIndicator.__init__(self, )

class ListenerDialog(Dialog, enotify.Listener):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        enotify.Listener.__init__(self)
        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)
        self.add_notification_cb(enotify.E_CHANGE_WD, self._self_destruct_cb)
        self.set_modal(False)
    def _self_destruct_cb(self, **kwargs):
        self.destroy()

class QuestionDialog(Dialog):
    def __init__(self, qtn="", expln="", **kwargs):
        Dialog.__init__(self, **kwargs)
        self.set_skip_taskbar_hint(True)
        self.set_destroy_with_parent(True)
        grid = Gtk.Grid()
        self.vbox.add(grid)
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_DIALOG_QUESTION, Gtk.IconSize.DIALOG)
        grid.add(image)
        q_label = Gtk.Label()
        q_label.set_markup("<big><b>" + qtn + "</b></big>")
        q_label.set_justify(Gtk.Justification.LEFT)
        q_label.set_line_wrap(True)
        grid.attach_next_to(q_label, image, Gtk.PositionType.RIGHT, 1, 1)
        if expln:
            e_label = Gtk.Label(expln)
            e_label.set_justify(Gtk.Justification.FILL)
            e_label.set_line_wrap(True)
            grid.attach_next_to(e_label, q_label, Gtk.PositionType.BOTTOM, 1, 1)
        self.show_all()

class CancelOKDialog(Dialog):
    def __init__(self, title=None, parent=None):
        flags = Gtk.DialogFlags.DESTROY_WITH_PARENT
        buttons = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        Dialog.__init__(self, title=title, parent=parent, flags=flags, buttons=buttons)

class ReadTextWidget(Gtk.HBox):
    def __init__(self, prompt=None, suggestion="", width_chars=32):
        Gtk.HBox.__init__(self)
        if prompt:
            p_label = Gtk.Label()
            p_label.set_markup(prompt)
            self.pack_start(p_label, expand=False, fill=True, padding=0)
        self.entry = Gtk.Entry()
        if suggestion:
            self.entry.set_text(suggestion)
            self.entry.set_width_chars(max(width_chars, len(suggestion)))
        else:
            self.entry.set_width_chars(width_chars)
        self.pack_start(self.entry, expand=True, fill=True, padding=0)
        self.show_all()
    def _do_pulse(self):
        self.entry.progress_pulse()
        return True
    def start_busy_pulse(self):
        self.entry.set_progress_pulse_step(0.2)
        self._timeout_id = GObject.timeout_add(100, self._do_pulse, priority=GObject.PRIORITY_HIGH)
    def stop_busy_pulse(self):
        GObject.source_remove(self._timeout_id)
        self._timeout_id = None
        self.entry.set_progress_pulse_step(0)

class ReadTextDialog(CancelOKDialog):
    def __init__(self, title=None, prompt=None, suggestion="", parent=None):
        CancelOKDialog.__init__(self, title=title, parent=parent)
        self._rtw = ReadTextWidget(prompt, suggestion, width_chars=32)
        self.entry.set_activates_default(True)
        self.vbox.pack_start(self._rtw, expand=False, fill=True, padding=0)
        self.show_all()
    @property
    def entry(self):
        return self._rtw.entry

class ReadTextAndToggleDialog(ReadTextDialog):
    def __init__(self, title=None, prompt=None, suggestion="", toggle_prompt=None, toggle_state=False, parent=None):
        ReadTextDialog.__init__(self, title=title, prompt=prompt, suggestion=suggestion, parent=parent)
        self.toggle = Gtk.CheckButton(label=toggle_prompt)
        self.toggle.set_active(toggle_state)
        self._rtw.pack_start(self.toggle, expand=True, fill=True, padding=0)
        self.show_all()

class ReadTextAndTogglesDialog(ReadTextDialog):
    PROMPT = None
    TOGGLE_PROMPT_LIST = []
    def __init__(self, title=None, suggestion="", toggle_start_states=None, parent=None):
        toggle_start_states = toggle_start_states if toggle_start_states else {}
        ReadTextDialog.__init__(self, title=title, prompt=self.PROMPT, suggestion=suggestion, parent=parent)
        self.toggles = {}
        for toggle_prompt in self.TOGGLE_PROMPT_LIST:
            self.toggles[toggle_prompt] = Gtk.CheckButton(label=toggle_prompt)
            self.toggles[toggle_prompt].set_active(toggle_start_states.get(toggle_prompt, False))
            self._rtw.pack_start(self.toggles[toggle_prompt], expand=False, fill=True, padding=0)
        self.show_all()

class PathSelectorMixin:
    # TODO: fix relative paths in PathSelectorMixin results i.e. use "./" at start
    def select_file(self, prompt, suggestion=None, existing=True, absolute=False):
        if existing:
            mode = Gtk.FileChooserAction.OPEN
            if suggestion and not os.path.exists(suggestion):
                suggestion = None
        else:
            mode = Gtk.FileChooserAction.SAVE
        dialog = Gtk.FileChooserDialog(prompt, self.get_toplevel(), mode,
                                   (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                    Gtk.STOCK_OK, Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)
        if suggestion:
            if os.path.isdir(suggestion):
                dialog.set_current_folder(suggestion)
            else:
                dirname, basename = os.path.split(suggestion)
                if dirname:
                    dialog.set_current_folder(dirname)
                else:
                    dialog.set_current_folder(os.getcwd())
                if basename:
                    dialog.set_current_name(basename)
        else:
            dialog.set_current_folder(os.getcwd())
        response = dialog.run()
        if dialog.run() == Gtk.ResponseType.OK:
            if absolute:
                new_file_path = dialog.get_filename()
            else:
                new_file_path = os.path.relpath(dialog.get_filename())
        else:
            new_file_path = None
        dialog.destroy()
        return new_file_path
    def select_directory(self, prompt, suggestion=None, existing=True, absolute=False):
        if existing:
            if suggestion and not os.path.exists(suggestion):
                suggestion = None
        dialog = Gtk.FileChooserDialog(prompt, self.get_toplevel(), Gtk.FileChooserAction.SELECT_FOLDER,
                                   (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                    Gtk.STOCK_OK, Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)
        if suggestion:
            if os.path.isdir(suggestion):
                dialog.set_current_folder(suggestion)
            else:
                dirname = os.path.dirname(suggestion)
                if dirname:
                    dialog.set_current_folder(dirname)
                else:
                    dialog.set_current_folder(os.getcwd())
        else:
            dialog.set_current_folder(os.getcwd())
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            if absolute:
                new_dir_path = dialog.get_filename()
            else:
                new_dir_path = os.path.relpath(dialog.get_filename())
        else:
            new_dir_path = None
        dialog.destroy()
        return new_dir_path
    def select_uri(self, prompt, suggestion=None):
        if suggestion and not os.path.exists(suggestion):
            suggestion = None
        dialog = Gtk.FileChooserDialog(prompt, self.get_toplevel(), Gtk.FileChooserAction.SELECT_FOLDER,
                                   (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                    Gtk.STOCK_OK, Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_local_only(False)
        if suggestion:
            if os.path.isdir(suggestion):
                dialog.set_current_folder(suggestion)
            else:
                dirname = os.path.dirname(suggestion)
                if dirname:
                    dialog.set_current_folder(dirname)
        else:
            dialog.set_current_folder(os.getcwd())
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            uri = os.path.relpath(dialog.get_uri())
        else:
            uri = None
        dialog.destroy()
        return uri

# TODO: put auto completion into the text entry component
class _EnterPathWidget(Gtk.HBox, PathSelectorMixin):
    SELECT_FUNC = None
    SELECT_TITLE = None
    def __init__(self, prompt=None, suggestion=None, existing=True, width_chars=32, parent=None):
        Gtk.HBox.__init__(self)
        self._parent = parent
        self._path = ReadTextWidget(prompt=prompt, suggestion=suggestion, width_chars=width_chars)
        self._path.entry.set_activates_default(True)
        self._existing = existing
        self.b_button = Gtk.Button.new_with_label(_("Browse"))
        self.b_button.connect("clicked", self._browse_cb)
        self.pack_start(self._path, expand=True, fill=True, padding=0)
        self.pack_end(self.b_button, expand=False, fill=True, padding=0)
        self.show_all()
    @property
    def path(self):
        return os.path.expanduser(self._path.entry.get_text())
    def set_sensitive(self, sensitive):
        self._path.entry.set_editable(sensitive)
        self.b_button.set_sensitive(sensitive)
    def _browse_cb(self, button=None):
        suggestion = self._path.entry.get_text()
        path = self.SELECT_FUNC(self.SELECT_TITLE, suggestion=suggestion, existing=self._existing, absolute=False)
        if path:
            self._path.entry.set_text(path)
    def start_busy_pulse(self):
        self._path.start_busy_pulse()
    def stop_busy_pulse(self):
        self._path.stop_busy_pulse()

class _EnterPathDialog(CancelOKDialog):
    WIDGET = None
    def __init__(self, title=None, prompt=None, suggestion="", existing=True, parent=None):
        CancelOKDialog.__init__(self, title, parent)
        self.entry = self.WIDGET(prompt, suggestion, existing, parent=self)
        self.get_content_area().add(self.entry)
        self.set_default_response(Gtk.ResponseType.OK)
        self.set_position(Gtk.WindowPosition.MOUSE)
        self.show_all()
    @property
    def path(self):
        return self.entry.path
    def start_busy_pulse(self):
        ok_button = self.get_widget_for_response(Gtk.ResponseType.OK)
        ok_button.set_label("Wait...")
        self.entry.start_busy_pulse()
    def stop_busy_pulse(self):
        self.entry.stop_busy_pulse()

class EnterDirPathWidget(_EnterPathWidget):
    SELECT_FUNC = PathSelectorMixin.select_directory
    SELECT_TITLE = _("Browse for Directory")

class EnterDirPathDialog(_EnterPathDialog):
    WIDGET = EnterDirPathWidget

class EnterFilePathWidget(_EnterPathWidget):
    SELECT_FUNC = PathSelectorMixin.select_file
    SELECT_TITLE = _("Browse for File")

class EnterFilePathDialog(_EnterPathDialog):
    WIDGET = EnterFilePathWidget

class ReadMultiTextDialog(CancelOKDialog):
    def __init__(self, prompts_and_suggestions, title=None, parent=None):
        CancelOKDialog.__init__(self, title, parent)
        self.set_default_response(Gtk.ResponseType.OK)
        self.hbox = Gtk.HBox()
        self.vbox.pack_start(self.hbox, expand=False, fill=True, padding=0)
        self.hbox.show()
        self.entries = []
        for prompt, suggestion in prompts_and_suggestions:
            self.hbox.pack_start(Gtk.Label(prompt), fill=False, expand=False, padding=0)
            entry = Gtk.Entry()
            if suggestion:
                entry.set_text(suggestion)
                entry.set_position(len(suggestion))
                entry.select_region(0, -1)
            entry.set_width_chars(16)
            self.entries.append(entry)
            self.hbox.pack_start(entry, expand=True, fill=True, padding=0)
        self.entries[-1].set_activates_default(True)
        self.show_all()
    def get_texts(self):
        return [entry.get_text() for entry in self.entries]

class SelectFromListDialog(CancelOKDialog):
    def __init__(self, prompt, olist, **kwargs):
        CancelOKDialog.__init__(self, **kwargs)
        self.combo_box = Gtk.ComboBoxText()
        for option in olist:
            self.combo_box.append_text(option)
        hbox = Gtk.HBox()
        hbox.pack_start(Gtk.Label(prompt), expand=False, fill=True, padding=0)
        hbox.pack_start(self.combo_box, expand=False, fill=True, padding=0)
        self.show_all()
    def get_selection(self):
        return self.combo_box.get_active_text()
    def make_selection(self):
        if self.run() == Gtk.ResponseType.OK:
            return self.get_selection()
        else:
            return None

CANCEL_OK_BUTTONS = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
NO_YES_BUTTONS = (Gtk.STOCK_NO, Gtk.ResponseType.NO, Gtk.STOCK_YES, Gtk.ResponseType.YES)

from ..bab import Suggestion
Response = Suggestion

SUGGESTION_LABEL_MAP = {
    Suggestion.FORCE : _("Force"),
    Suggestion.REFRESH : _("Refresh"),
    Suggestion.RECOVER : _("Recover"),
    Suggestion.RENAME : _("Rename"),
    Suggestion.DISCARD : _("Discard"),
    Suggestion.ABSORB : _("Absorb"),
    Suggestion.EDIT : _("Edit"),
    Suggestion.MERGE : _("Merge"),
    Suggestion.OVERWRITE : _("Overwrite"),
    Suggestion.CACHE : _("Cache"),
    Suggestion.SKIP : _("Skip"),
    Suggestion.SKIP_ALL : _("Skip All"),
}

ALL_SUGGESTIONS = [key for key in sorted(SUGGESTION_LABEL_MAP.keys())]

assert len(SUGGESTION_LABEL_MAP) == Suggestion.NFLAGS

def response_str(response):
    if response > 0:
        return SUGGESTION_LABEL_MAP[response]
    else:
        return _("Gtk.Response({})".format(response))

class AskerMixin:
    def ask_question(self, qtn, expln="", buttons=CANCEL_OK_BUTTONS):
        dialog = QuestionDialog(parent=self.get_toplevel(), buttons=buttons, qtn=qtn, expln=expln)
        response = dialog.run()
        dialog.destroy()
        return response
    def ask_ok_cancel(self, qtn, expln=""):
        return self.ask_question(qtn, expln) == Gtk.ResponseType.OK
    def ask_yes_no(self, qtn, expln=""):
        buttons = (Gtk.STOCK_NO, Gtk.ResponseType.NO, Gtk.STOCK_YES, Gtk.ResponseType.YES)
        return self.ask_question(qtn, expln, buttons) == Gtk.ResponseType.YES
    def ask_dir_path(self, prompt, suggestion=None, existing=True):
        dialog = EnterDirPathDialog(title=_("Enter Directory Path"), prompt=prompt, suggestion=suggestion, existing=existing, parent=self.get_toplevel())
        dir_path = dialog.path if dialog.run() == Gtk.ResponseType.OK else None
        dialog.destroy()
        return dir_path
    def ask_file_path(self, prompt, suggestion=None, existing=True):
        dialog = EnterFilePathDialog(title=_("Enter File Path"), prompt=prompt, suggestion=suggestion, existing=existing, parent=self.get_toplevel())
        file_path = dialog.path if dialog.run() == Gtk.ResponseType.OK else None
        dialog.destroy()
        return file_path
    def ask_multiple_texts(self, prompts_and_suggestions):
        dialog = ReadMultiTextDialog(prompts_and_suggestions, parent=self.get_toplevel())
        if dialog.run() == Gtk.ResponseType.OK:
            texts = dialog.get_texts()
        else:
            texts = [None for i in range(len(prompts_and_suggestions))]
        dialog.destroy()
        return texts
    def ask_text(self, prompt, suggestion=None):
        return self.ask_multiple_texts([(prompt, suggestion)])[0]
    def confirm_list_action(self, alist, qtn):
        return self.ask_ok_cancel("\n".join(alist + ["\n", qtn]))
    def accept_suggestion_or_cancel(self, result, expln="", suggestions=ALL_SUGGESTIONS):
        buttons = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        for suggestion in suggestions:
            if result.suggests(suggestion):
                buttons += (SUGGESTION_LABEL_MAP[suggestion], suggestion)
        return self.ask_question(result.message, expln, buttons)
    def choose_from_list(self, alist, prompt):
        return dialogue.SelectFromListDialog(olist=alist, prompt=prompt, parent=self.get_toplevel()).make_selection()
    # Commonly encountered suggestion combinations
    def ask_edit_force_or_cancel(self, result, expln=""):
        return self.accept_suggestion_or_cancel(result, expln, [Suggestion.EDIT, Suggestion.FORCE])
    def ask_force_or_cancel(self, result, expln=""):
        return self.accept_suggestion_or_cancel(result, expln, [Suggestion.FORCE])
    def ask_force_refresh_absorb_or_cancel(self, result, expln=""):
        return self.accept_suggestion_or_cancel(result, expln, [Suggestion.FORCE, Suggestion.REFRESH, Suggestion.ABSORB])
    def ask_recover_or_cancel(self, result, expln=""):
        return self.accept_suggestion_or_cancel(result, expln, [Suggestion.RECOVER])
    def ask_rename_or_cancel(self, result, expln=""):
        return self.accept_suggestion_or_cancel(result, expln, [Suggestion.RENAME])
    def ask_rename_force_or_cancel(self, result, expln=""):
        return self.accept_suggestion_or_cancel(result, expln, [Suggestion.RENAME, Suggestion.FORCE])
    def ask_rename_force_or_skip(self, result, expln=""):
        return self.accept_suggestion_or_cancel(result, expln, [Suggestion.RENAME, Suggestion.FORCE, Suggestion.SKIP, Suggestion.SKIP_ALL])
    def ask_rename_overwrite_force_or_cancel(self, result, expln=""):
        return self.accept_suggestion_or_cancel(result, expln, [Suggestion.RENAME, Suggestion.OVERWRITE, Suggestion.FORCE])
    def ask_rename_overwrite_or_cancel(self, result, expln=""):
        return self.accept_suggestion_or_cancel(result, expln, [Suggestion.RENAME, Suggestion.OVERWRITE])

class ReporterMixin:
    def inform_user(self, msg, expln=None, problem_type=Gtk.MessageType.INFO):
        dialog = Gtk.MessageDialog(parent=self.get_toplevel(),
                               flags=Gtk.DialogFlags.MODAL|Gtk.DialogFlags.DESTROY_WITH_PARENT,
                               type=problem_type, buttons=(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE),
                               text=msg)
        if expln:
            dialog.format_secondary_text(expln)
        dialog.run()
        dialog.destroy()
        return problem_type == Gtk.MessageType.ERROR
    def alert_user(self, msg, expln=None):
        return self.inform_user(msg=msg, expln=expln, problem_type=Gtk.MessageType.ERROR)
    def report_failure(self, failure):
        return self.inform_user(msg=failure.result, problem_type=Gtk.MessageType.ERROR)
    def report_exception_as_error(self, edata):
        return self.alert_user(msg=str(edata))
    def report_any_problems(self, result):
        if result.is_ok:
            return
        elif result.is_warning:
            problem_type = Gtk.MessageType.WARNING
        else:
            problem_type = Gtk.MessageType.ERROR
        return self.inform_user(msg=result.message, problem_type=problem_type)

class ClientMixin(BusyIndicatorUser, PathSelectorMixin, AskerMixin, ReporterMixin):
    pass

@singleton
class MainWindow(Gtk.Window, BusyIndicator, AskerMixin, ReporterMixin, PathSelectorMixin):
    def __init__(self, *args, **kwargs):
        global main_window
        kwargs["type"] = Gtk.WindowType.TOPLEVEL
        Gtk.Window.__init__(self, *args, **kwargs)
        BusyIndicator.__init__(self)
        main_window = self

def ask_for_bug_report(exc_data):
    """Ask the user to report an uncaught exception."""
    # TODO: add buttons for copyng info to the clipboard
    import traceback
    dialog = Gtk.MessageDialog(main_window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE)
    dialog.set_markup(BUG_REPORT_REQUEST_MSG)
    dialog.format_secondary_text("".join(traceback.format_exception(exc_data[0], exc_data[1], exc_data[2])))
    dialog.run()
