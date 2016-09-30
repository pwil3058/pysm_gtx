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
from gi.repository import Gtk
from gi.repository import GObject

from ... import enotify
from ... import scm

from ...gui import actions
from ...gui import dialogue
from ...gui import table
from ...gui import text_edit
from ...gui import icons

from . import ifce

TagListRow = collections.namedtuple("TagListRow",    ["name", "annotation"])

class TagListView(table.MapManagedTableView, scm.gui.actions.WDListenerMixin):
    class MODEL(table.MapManagedTableView.MODEL):
        ROW = TagListRow
        TYPES = ROW(name=GObject.TYPE_STRING, annotation=GObject.TYPE_STRING,)
        def get_tag_name(self, plist_iter):
            return self.get_value_named(plist_iter, "name")
        def get_annotation(self, plist_iter):
            return self.get_value_named(plist_iter, "annotation")
    PopUp = "/tags_popup"
    SET_EVENTS = enotify.E_CHANGE_WD|scm.E_NEW_SCM
    REFRESH_EVENTS = scm.E_TAG
    AU_REQ_EVENTS = scm.E_TAG
    UI_DESCR = """
    <ui>
      <popup name="tags_popup">
        <menuitem action="checkout_selected_tag"/>
        <separator/>
        <menuitem action="table_refresh_contents"/>
      </popup>
    </ui>
    """
    SPECIFICATION = table.simple_text_specification(MODEL, (_("Name"), "name", 0.0), (_("Annotation"), "annotation", 0.0))
    def __init__(self, size_req=None):
        table.MapManagedTableView.__init__(self, size_req=size_req)
        scm.gui.actions.WDListenerMixin.__init__(self)
        self.set_contents()
    def populate_action_groups(self):
        self.action_groups[actions.AC_SELN_UNIQUE].add_actions(
            [
                ("checkout_selected_tag", icons.STOCK_CHECKOUT, _("Checkout"), None,
                 _("Checkout the selected tag in the current working directory"), self._checkout_seln_acb),
            ])
    def get_selected_tag(self):
        store, store_iter = self.get_selection().get_selected()
        return None if store_iter is None else store.get_tag_name(store_iter)
    def _get_table_db(self):
        return ifce.SCM.get_tags_table_data()
    def _checkout_seln_acb(self, _action):
        # TODO: make tag checkout more user friendly
        tag = self.get_selected_tag()
        with self.showing_busy():
            result = ifce.SCM.do_checkout_tag(tag=tag)
        dialogue.main_window.report_any_problems(result)

class TagList(table.TableWidget):
    VIEW = TagListView

class MessageWidget(text_edit.MessageWidget):
    UI_DESCR = \
    """
    <ui>
      <toolbar name="tag_message_toolbar">
        <toolitem action="text_edit_ack"/>
        <toolitem action="text_edit_sign_off"/>
        <toolitem action="text_edit_author"/>
      </toolbar>
    </ui>
    """
    get_user_name_and_email = lambda _self: ifce.get_author_name_and_email()

class AnnotationDataWidget(Gtk.VBox):
    def __init__(self):
        Gtk.VBox.__init__(self)
        self.signed = Gtk.CheckButton(label=_("Sign"))
        self.signed.set_active(False)
        self.key_id = Gtk.Entry()
        self.key_id.set_width_chars(32)
        hbox = Gtk.HBox()
        hbox.pack_start(self.signed, expand=False, fill=False, padding=0)
        hbox.pack_end(self.key_id, expand=False, fill=False, padding=0)
        hbox.pack_end(Gtk.Label(_("Key Id:")), expand=False, fill=False, padding=0)
        self.pack_start(hbox, expand=False, fill=True, padding=0)
        self.message = MessageWidget()
        hbox = Gtk.HBox()
        hbox.pack_start(Gtk.Label(_("Message")), expand=False, fill=False, padding=0)
        toolbar = self.message.ui_manager.get_widget("/tag_message_toolbar")
        toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        toolbar.set_orientation(Gtk.Orientation.HORIZONTAL)
        hbox.pack_end(toolbar, fill=False, expand=False, padding=0)
        self.pack_start(hbox, expand=False, fill=True, padding=0)
        self.pack_start(self.message, expand=True, fill=True, padding=0)
        self.show_all()
    def get_msg(self):
        return self.message.get_contents()
    def get_signed(self):
        return self.signed.get_active()
    def get_key_id(self):
        text = self.key_id.get_text()
        return None if not text else text
    def _toggled_cb(self, togglebutton):
        if togglebutton.get_active() and not self.key_id.get_text():
            self.key_id.set_text(ifce.SCM.get_signing_key())

class SetTagDialog(dialogue.ReadTextAndToggleDialog):
    def __init__(self, target=None, parent=None):
        self._target = target
        dialogue.ReadTextAndToggleDialog.__init__(self, title=_("gwsmgitd: Set Tag"),
            prompt=_("Tag:"), toggle_prompt=_("Annotated"), toggle_state=False, parent=parent)
        self.annotation_data = AnnotationDataWidget()
        self.vbox.pack_start(self.annotation_data, expand=True, fill=True, padding=0)
        self.toggle.connect("toggled", self._toggled_cb)
        self.connect("response", self._response_cb)
        self.show_all()
        self._toggled_cb(self.toggle)
    def _toggled_cb(self, togglebutton):
        self.annotation_data.set_sensitive(togglebutton.get_active())
    def _response_cb(self, dialog, response_id):
        self.hide()
        if response_id == Gtk.ResponseType.CANCEL:
            self.destroy()
        else:
            tag = self.entry.get_text()
            annotated = self.toggle.get_active()
            if annotated:
                msg = self.annotation_data.get_msg()
                signed = self.annotation_data.get_signed()
                key_id = self.annotation_data.get_key_id()
            else:
                msg = signed = key_id = None
            with self.showing_busy():
                result = ifce.SCM.do_set_tag(tag=tag, annotated=annotated, msg=msg, signed=signed, key_id=key_id, target=self._target, force=False)
            if result.suggests_force:
                ans = dialogue.main_window.ask_rename_force_or_cancel(result)
                if ans == dialogue.Response.RENAME:
                    self.show()
                    return
                if ans == dialogue.Response.FORCE:
                    with self.showing_busy():
                        result = ifce.SCM.do_set_tag(tag=tag, annotated=annotated, msg=msg, signed=signed, key_id=key_id, target=self._target, force=True)
                    dialogue.main_window.report_any_problems(result)
            else:
                dialogue.main_window.report_any_problems(result)
            self.destroy()

def tag_head_acb(_action=None):
    SetTagDialog(parent=dialogue.main_window).show()

# TODO: be more fussy about when set tag enabled?
actions.CLASS_INDEP_AGS[scm.gui.actions.AC_IN_SCM_PGND].add_actions(
    [
        ("git_tag_current_head", icons.STOCK_TAG, _("Tag"), None,
         _("Set a tag on the current HEAD"), tag_head_acb),
    ])
