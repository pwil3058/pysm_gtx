### Copyright (C) 2005-2016 Peter Williams <pwil3058@gmail.com>
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

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Gio
from gi.repository import Gdk

class FramedScrollWindow(Gtk.Frame):
    __g_type_name__ = "FramedScrollWindow"
    def __init__(self, policy=(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)):
        Gtk.Frame.__init__(self)
        self._sw = Gtk.ScrolledWindow()
        Gtk.Frame.add(self, self._sw)
    def add(self, widget):
        self._sw.add(widget)
    def set_policy(self, hpolicy, vpolicy):
        return self._sw.set_policy(hpolicy, vpolicy)
    def get_hscrollbar(self):
        return self._sw.get_hscrollbar()
    def get_vscrollbar(self):
        return self._sw.get_hscrollbar()
    def set_min_content_width(self, width):
        return self._sw.set_min_content_width(width)
    def set_min_content_height(self, height):
        return self._sw.set_min_content_height(height)

def wrap_in_scrolled_window(widget, policy=(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC), with_frame=False, use_widget_size=False):
    scrw = FramedScrollWindow() if with_frame else Gtk.ScrolledWindow()
    scrw.set_policy(policy[0], policy[1])
    if isinstance(widget, Gtk.Container):
        scrw.add(widget)
    else:
        scrw.add_with_viewport(widget)
    if use_widget_size:
        vw, vh = widget.get_size_request()
        if vw > 0:
            scrw.set_min_content_width(vw)
        if vh > 0:
            scrw.set_min_content_height(vh)
    scrw.show_all()
    return scrw

def wrap_in_frame(widget, shadow_type=Gtk.ShadowType.NONE):
    """
    Wrap the widget in a frame with the requested shadow type
    """
    frame = Gtk.Frame()
    frame.set_shadow_type(shadow_type)
    frame.add(widget)
    return frame

class RadioButtonFramedVBox(Gtk.Frame):
    def __init__(self, title, labels):
        Gtk.Frame.__init__(self, title)
        self.vbox = Gtk.VBox()
        self.buttons = [Gtk.RadioButton(label=labels[0], group=None)]
        for label in labels[1:]:
            self.buttons.append(Gtk.RadioButton(label=label, group=self.buttons[0]))
        for button in self.buttons:
            self.vbox.pack_start(button, expand=True, fill=False, padding=0)
        self.buttons[0].set_active(True)
        self.add(self.vbox)
        self.show_all()
    def get_selected_index(self):
        for index in range(len(self.buttons)):
            if self.buttons[index].get_active():
                return index
        return None

class MappedManager:
    def __init__(self):
        self.is_mapped = False
        self.connect("map", self._map_cb)
        self.connect("unmap", self._unmap_cb)
    def _map_cb(self, widget=None):
        self.is_mapped = True
        self.map_action()
    def _unmap_cb(self, widget=None):
        self.is_mapped = False
        self.unmap_action()
    def map_action(self):
        pass
    def unmap_action(self):
        pass

class EntryWithHistory(Gtk.Entry):
    def __init__(self, max_chars=0):
        Gtk.Entry.__init__(self)
        self.set_max_width_chars(max_chars)
        self._history_list = []
        self._history_index = 0
        self._history_len = 0
        self._saved_text = ""
        self._key_press_cb_id = self.connect("key_press_event", self._key_press_cb)
    def _key_press_cb(self, widget, event):
        _KEYVAL_UP_ARROW = Gdk.keyval_from_name("Up")
        _KEYVAL_DOWN_ARROW = Gdk.keyval_from_name("Down")
        if event.keyval in [_KEYVAL_UP_ARROW, _KEYVAL_DOWN_ARROW]:
            if event.keyval == _KEYVAL_UP_ARROW:
                if self._history_index < self._history_len:
                    if self._history_index == 0:
                        self._saved_text = self.get_text()
                    self._history_index += 1
                    self.set_text(self._history_list[-self._history_index])
                    self.set_position(-1)
            elif event.keyval == _KEYVAL_DOWN_ARROW:
                if self._history_index > 0:
                    self._history_index -= 1
                    if self._history_index > 0:
                        self.set_text(self._history_list[-self._history_index])
                    else:
                        self.set_text(self._saved_text)
                    self.set_position(-1)
            return True
        else:
            return False
    def clear_to_history(self):
        self._history_index = 0
        # beware the empty command string
        text = self.get_text().rstrip()
        self.set_text("")
        # don't save empty entries or ones that start with white space
        if not text or text[0] in [" ", "\t"]:
            return
        # no adjacent duplicate entries allowed
        if (self._history_len == 0) or (text != self._history_list[-1]):
            self._history_list.append(text)
            self._history_len = len(self._history_list)
    def get_text_and_clear_to_history(self):
        text = self.get_text().rstrip()
        self.clear_to_history()
        return text

def _combo_entry_changed_cb(combo, entry):
    if combo.get_active() == -1:
        combo.saved_text = entry.get_text()
    else:
        text = combo.saved_text.rstrip()
        # no duplicates, empty strings or strings starting with white space
        if text and text[0] not in [" ", "\t"] and text not in combo.entry_set:
            combo.entry_set.add(text)
            combo.prepend_text(text)
        combo.saved_text = ""
    return False

def _combo_get_text(combo):
    return combo.get_child().get_text()

def _combo_set_text(combo, text):
    text = text.rstrip()
    if text and text[0] not in [" ", "\t"] and text not in combo.entry_set:
        combo.prepend_text(text)
        combo.set_active(0)
        combo.entry_set.add(text)
    else:
        combo.get_child().set_text(text)

# WORKAROUND: can't extend a ComboBox with entry
def new_mutable_combox_text_with_entry(entries=None):
    combo = Gtk.ComboBoxText.new_with_entry()
    combo.get_text = lambda : _combo_get_text(combo)
    combo.set_text = lambda text: _combo_set_text(combo, text)
    combo.saved_text = ""
    combo.entry_set = set()
    for entry in entries if entries else []:
        if entry not in combo.entry_set:
            combo.append_text(entry)
            combo.entry_set.add(entry)
    combo.set_active(-1)
    combo.get_child().connect("changed", lambda entry: _combo_entry_changed_cb(combo, entry))
    return combo

class ActionButton(Gtk.Button):
    def __init__(self, action, use_underline=True):
        Gtk.Button.__init__(self)
        label = action.get_label()
        icon_name = action.get_icon_name()
        stock_id = action.get_stock_id()
        if label:
            self.set_label(label)
            self.set_use_stock(False)
            if icon_name:
                self.set_image(Gtk.Image.new_from_icon_name(icon_name))
        elif stock_id:
            self.set_label(stock_id)
            self.set_use_stock(True)
        elif icon_name:
            self.set_image(Gtk.Image.new_from_icon_name(icon_name))
        self.set_use_underline(use_underline)
        self.set_tooltip_text(action.get_property("tooltip"))
        self.set_related_action(action)

class ActionCheckButton(Gtk.CheckButton):
    def __init__(self, action, use_underline=True):
        Gtk.CheckButton.__init__(self, label=action.get_property("label"), use_underline=use_underline)
        self.set_tooltip_text(action.get_property("tooltip"))
        self.set_related_action(action)

def creat_button_from_action(action, use_underline=True):
    if isinstance(action, Gtk.ToggleAction):
        return ActionCheckButton(action)
    else:
        return ActionButton(action, use_underline)

class ActionButtonList:
    def __init__(self, action_group_list, action_name_list=None, use_underline=True):
        self.list = []
        self.dict = {}
        if action_name_list:
            for a_name in action_name_list:
                for a_group in action_group_list:
                    action = a_group.get_action(a_name)
                    if action:
                        button = creat_button_from_action(action, use_underline)
                        self.list.append(button)
                        self.dict[a_name] = button
                        break
        else:
            for a_group in action_group_list:
                for action in a_group.list_actions():
                    button = creat_button_from_action(action, use_underline)
                    self.list.append(button)
                    self.dict[action.get_name()] = button

class ActionHButtonBox(Gtk.HBox):
    def __init__(self, action_group_list, action_name_list=None,
                 use_underline=True, expand=True, fill=True, padding=0):
        Gtk.HBox.__init__(self)
        self.button_list = ActionButtonList(action_group_list, action_name_list, use_underline)
        for button in self.button_list.list:
            self.pack_start(button, expand=expand, fill=fill, padding=padding)

class TimeOutController:
    ToggleData = collections.namedtuple("ToggleData", ["name", "label", "tooltip", "stock_id"])
    def __init__(self, toggle_data, function=None, is_on=True, interval=10000):
        self._interval = abs(interval)
        self._timeout_id = None
        self._function = function
        self.toggle_action = Gtk.ToggleAction(
                toggle_data.name, toggle_data.label,
                toggle_data.tooltip, toggle_data.stock_id
            )
        # TODO: find out how to do this in PyGTK3
        #self.toggle_action.set_menu_item_type(Gtk.CheckMenuItem)
        #self.toggle_action.set_tool_item_type(Gtk.ToggleToolButton)
        self.toggle_action.connect("toggled", self._toggle_acb)
        self.toggle_action.set_active(is_on)
    def _toggle_acb(self, _action=None):
        if self.toggle_action.get_active():
            self._restart_cycle()
        else:
            self._stop_cycle()
    def _timeout_cb(self):
        if self._function:
            self._function()
        return self.toggle_action.get_active()
    def _stop_cycle(self):
        if self._timeout_id:
            GObject.source_remove(self._timeout_id)
            self._timeout_id = None
    def _restart_cycle(self):
        self._stop_cycle()
        self._timeout_id = GObject.timeout_add(self._interval, self._timeout_cb)
    def set_function(self, function):
        self._stop_cycle()
        self._function = function
        self._toggle_acb()
    def set_interval(self, interval):
        if interval > 0 and interval != self._interval:
            self._interval = interval
            self._toggle_acb()
    def get_interval(self):
        return self._interval

TOC_DEFAULT_REFRESH_TD = TimeOutController.ToggleData("auto_refresh_toggle", _("Auto _Refresh"), _("Turn data auto refresh on/off"), Gtk.STOCK_REFRESH)

class RefreshController(TimeOutController):
    def __init__(self, toggle_data=None, function=None, is_on=True, interval=10000):
        if toggle_data is None:
            toggle_data = TOC_DEFAULT_REFRESH_TD
        TimeOutController.__init__(self, toggle_data, function=function, is_on=is_on, interval=interval)

TOC_DEFAULT_SAVE_TD = TimeOutController.ToggleData("auto_save_toggle", _("Auto _Save"), _("Turn data auto save on/off"), Gtk.STOCK_SAVE)

class SaveController(TimeOutController):
    def __init__(self, toggle_data=None, function=None, is_on=True, interval=10000):
        if toggle_data is None:
            toggle_data = TOC_DEFAULT_SAVE_TD
        TimeOutController.__init__(self, toggle_data, function=function, is_on=is_on, interval=interval)

class LabelledEntry(Gtk.HBox):
    def __init__(self, label="", max_chars=0, text=""):
        Gtk.HBox.__init__(self)
        self.label = Gtk.Label(label=label)
        self.pack_start(self.label, expand=False, fill=True, padding=0)
        self.entry = EntryWithHistory(max_chars)
        self.pack_start(self.entry, expand=True, fill=True, padding=0)
        self.entry.set_text(text)
    def get_text_and_clear_to_history(self):
        return self.entry.get_text_and_clear_to_history()
    def set_label(self, text):
        self.label.set_text(text)

class LabelledText(Gtk.HBox):
    def __init__(self, label="", text="", min_chars=0):
        Gtk.HBox.__init__(self)
        self.label = Gtk.Label(label=label)
        self.pack_start(self.label, expand=False, fill=True, padding=0)
        self.entry = Gtk.Entry()
        self.entry.set_width_chars(min_chars)
        self.pack_start(self.entry, expand=True, fill=True, padding=0)
        self.entry.set_text(text)
        self.entry.set_editable(False)

class SplitBar(Gtk.HBox):
    __g_type_name__ = "SplitBar"
    def __init__(self, expand_lhs=True, expand_rhs=False):
        Gtk.HBox.__init__(self)
        self.lhs = Gtk.HBox()
        self.pack_start(self.lhs, expand=expand_lhs, fill=True, padding=0)
        self.rhs = Gtk.HBox()
        self.pack_end(self.rhs, expand=expand_rhs, fill=True, padding=0)

def _ui_manager_connect_proxy(_ui_mgr, action, widget):
    tooltip = action.get_property("tooltip")
    if isinstance(widget, Gtk.MenuItem) and tooltip:
        widget.set_tooltip_text(tooltip)

def yield_to_pending_events():
    while True:
        Gtk.main_iteration()
        if not Gtk.events_pending():
            break

class UIManager(Gtk.UIManager):
    def __init__(self):
        Gtk.UIManager.__init__(self)
        self.connect("connect-proxy", _ui_manager_connect_proxy)

class FlagButton(Gtk.CheckButton):
    def __init__(self, flag_text, tt_text=None):
        Gtk.CheckButton.__init__(self, label=flag_text)
        if tt_text:
            self.set_tooltip_text(tt_text)

class FlagButtonList:
    def __init__(self, flag_btn_specs):
        cbtns_iter = ((flag_text, FlagButton(flag_text, tt_text)) for flag_text, tt_text in flag_btn_specs)
        self.__flag_btns = collections.OrderedDict(cbtns_iter)
    def __iter__(self):
        return iter(self.__flag_btns.values())
    def __contains__(self, flag_text):
        return flag_text in self.__flag_btns
    def __getitem__(self, index):
        if isinstance(index, str):
            return self.__flag_btns[index]
        elif isinstance(index, int):
            for i, fbtn in enumerate(self.__flag_btns.values()):
                if i == index:
                    return fbtn
            raise IndexError
        else: # if not isinstance(index, slice) this should blow up which is what we want
            assert index.step is None, "FlagButtonList doesn't do stepped slices"
            if index.start is None:
                if index.stop is None:
                    return list(self.__flag_btns.values())
                else:
                    return [fbtn for i, fbtn in enumerate(self.__flag_btns.values()) if i < index.stop]
            elif index.stop is None:
                return [fbtn for i, fbtn in enumerate(self.__flag_btns.values()) if i >= index.start]
            else:
                return [fbtn for i, fbtn in enumerate(self.__flag_btns.values()) if i >= index.start and i < index.stop]
    def flag_is_active(self, flag_text):
        return self.__flag_btns[flag_text].get_active()
    def get_active_flags(self):
        return [flag_btn.get_label() for flag_btn in self.__flag_btns.values() if flag_btn.get_active()]


class ProgressThingy(Gtk.ProgressBar):
    __g_type_name__ = "ProgressThingy"
    def set_expected_total(self, total):
        nsteps = min(100, max(total, 1))
        self._numerator = 0.0
        self._denominator = max(float(total), 1.0)
        self._step = self._denominator / float(nsteps)
        self._next_kick = self._step
        self.set_fraction(0.0)
        yield_to_pending_events()
    def increment_count(self, by=1):
        self._numerator += by
        if self._numerator >= self._next_kick:
            self.set_fraction(min(self._numerator / self._denominator, 1.0))
            self._next_kick += self._step
            yield_to_pending_events()
    def finished(self):
        self.set_fraction(1.0)
        yield_to_pending_events()
    def start(self, only_every=1):
        self._pulse_count = 0
        self._only_every = only_every
        self.set_fraction(0.0)
        yield_to_pending_events()
    def pulse(self):
        self._pulse_count += 1
        if self._pulse_count % self._only_every == 0:
            Gtk.ProgressBar.pulse(self)
            yield_to_pending_events()

class PretendWOFile(Gtk.ScrolledWindow):
    __g_type_name__ = "PretendWOFile"
    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self._view = Gtk.TextView()
        self.add(self._view)
        self.show_all()
    def write(self, text):
        bufr = self._view.get_buffer()
        bufr.insert(bufr.get_end_iter(), text)
    def write_lines(self, lines):
        # take advantage of default "insert-text" handler's updating the iterator
        bufr = self._view.get_buffer()
        bufr_iter = bufr.get_end_iter()
        for line in lines:
            bufr.insert(bufr_iter, line)

class NotebookWithDelete(Gtk.Notebook):
    __g_type_name__ = "NotebookWithDelete"
    def __init__(self, tab_delete_tooltip=_("Delete this page."), **kwargs):
        self._tab_delete_tooltip = tab_delete_tooltip
        Gtk.Notebook.__init__(self, **kwargs)
    def append_deletable_page(self, page, tab_label):
        label_widget = self._make_label_widget(page, tab_label)
        return self.append_page(page, label_widget)
    def append_deletable_page_menu(self, page, tab_label, menu_label):
        tab_label_widget = self._make_label_widget(page, tab_label)
        return self.append_page_menu(page, tab_label_widget, menu_label)
    def _make_label_widget(self, page, tab_label):
        hbox = Gtk.HBox()
        hbox.pack_start(tab_label, expand=True, fill=True, padding=0)
        button = Gtk.Button()
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.set_focus_on_click(False)
        icon = Gio.ThemedIcon.new_with_default_fallbacks("window-close-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.MENU)
        image.set_tooltip_text(self._tab_delete_tooltip)
        button.add(image)
        button.set_name("notebook-tab-delete-button")
        hbox.pack_start(button, expand=False, fill=True, padding=0)
        button.connect("clicked", lambda _button: self._delete_page(page))
        hbox.show_all()
        return hbox
    def _prepare_for_delete(self, page):
        pass
    def _delete_page(self, page):
        self._prepare_for_delete(page)
        self.remove_page(self.page_num(page))
    def iterate_pages(self):
        for pnum in range(self.get_n_pages()):
            yield (pnum, self.get_nth_page(pnum))

class UpdatableComboBoxText(Gtk.ComboBoxText):
    __g_type_name__ = "UpdatableComboBoxText"
    def __init__(self):
        Gtk.ComboBoxText.__init__(self)
        self.update_contents()
        self.show_all()
    def remove_text_item(self, item):
        model = self.get_model()
        for index in range(len(model)):
            if model[index][0] == item:
                self.remove(index)
                return True
        return False
    def insert_text_item(self, item):
        model = self.get_model()
        if len(model) == 0 or model[-1][0] < item:
            self.append_text(item)
            return len(model) - 1
        index = 0
        while index < len(model) and model[index][0] < item:
            index += 1
        self.insert_text(index, item)
        return index
    def set_active_text(self, item):
        model = self.get_model()
        index = 0
        while index < len(model) and model[index][0] != item:
            index += 1
        self.set_active(index)
    def update_contents(self):
        updated_set = set(self._get_updated_item_list())
        for gone_away in (set([row[0] for row in self.get_model()]) - updated_set):
            self.remove_text_item(gone_away)
        for new_item in (updated_set - set([row[0] for row in self.get_model()])):
            self.insert_text_item(new_item)
    def _get_updated_item_list(self):
        assert False, "_get_updated_item_list() must be defined in child"

class YesNoWidget(Gtk.HBox):
    def __init__(self, question_text):
        Gtk.HBox.__init__(self)
        q_label = Gtk.Label(question_text)
        self.no_button = Gtk.Button.new_from_stock(Gtk.STOCK_NO)
        self.yes_button = Gtk.Button.new_from_stock(Gtk.STOCK_YES)
        self.pack_start(q_label, expand=True, fill=True, padding=0)
        self.pack_start(no_button, expand=False, padding=0)
        self.pack_start(yes_button, expand=False, padding=0)
        self.show_all()
    def set_button_sensitivity(self, no_sensitive, yes_sensitive):
        self.no_button.set_sensitive(no_sensitive)
        self.yes_button.set_sensitive(yes_sensitive)
