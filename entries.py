#  Copyright 2017 Peter Williams <pwil3058@gmail.com>
#
# This software is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License only.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; if not, write to:
#  The Free Software Foundation, Inc., 51 Franklin Street,
#  Fifth Floor, Boston, MA 02110-1301 USA

"""Extensions to Gtk.Entry and friends
"""

__all__ = []
__author__ = "Peter Williams <pwil3058@gmail.com>"

from gi.repository import Gtk
from gi.repository import GObject

from ..bab import str_utils


class EntryCompletionMultiWord(Gtk.EntryCompletion):
    """
    Extend EntryCompletion to handle mult-word text.
    """
    def __init__(self, model=None):
        """
        model: an argument to allow the TreeModel to be set at creation.
        """
        Gtk.EntryCompletion.__init__(self)
        if model is not None:
            self.set_model(model)
        self.set_match_func(self.match_func)
        self.connect("match-selected", self.match_selected_cb)
        self.set_popup_set_width(False)
    @staticmethod
    def match_func(completion, key_string, model_iter, _data=None):
        """
        Does the (partial) word in front of the cursor match the item?
        """
        cursor_index = completion.get_entry().get_position()
        pword_start = str_utils.find_start_last_word(text=key_string, before=cursor_index)
        pword = key_string[pword_start:cursor_index].lower()
        if not pword:
            return False
        text_col = completion.get_text_column()
        model = completion.get_model()
        mword = model.get_value(model_iter, text_col)
        return mword and mword.lower().startswith(pword)
    @staticmethod
    def match_selected_cb(completion, model, model_iter):
        """
        Handle "match-selected" signal.
        """
        entry = completion.get_entry()
        cursor_index = entry.get_position()
        # just in case get_text() is overloaded e.g. to add learning
        text = Gtk.Entry.get_text(entry)
        #
        text_col = completion.get_text_column()
        mword = model.get_value(model_iter, text_col)
        new_text = str_utils.replace_last_word(text=text, new_word=mword, before=cursor_index)
        entry.set_text(new_text)
        # move the cursor behind the new word
        entry.set_position(cursor_index + len(new_text) - len(text))
        return True

class TextEntryAutoComplete(Gtk.Entry):
    def __init__(self, lexicon=None, learn=True, multiword=True, **kwargs):
        """
        multiword: if True use individual words in entry as the target of autocompletion
        """
        Gtk.Entry.__init__(self, **kwargs)
        self.__multiword = multiword
        if self.__multiword:
            completion = EntryCompletionMultiWord()
        else:
            completion = Gtk.EntryCompletion()
        self.set_completion(completion)
        cell = Gtk.CellRendererText()
        completion.pack_start(cell, expand=True)
        completion.set_text_column(0)
        self.set_lexicon(lexicon)
        self.set_learn(learn)
    def set_lexicon(self, lexicon):
        if lexicon is not None:
            self.get_completion().set_model(lexicon)
    def set_learn(self, enable):
        """
        Set whether learning should happen
        """
        self.learn = enable
    def get_text(self):
        text = Gtk.Entry.get_text(self)
        if self.learn:
            completion = self.get_completion()
            model = completion.get_model()
            text_col = completion.get_text_column()
            lexicon = [row[text_col] for row in model]
            lexicon.sort()
            if self.__multiword:
                new_words = []
                for word in str_utils.extract_words(text):
                    if not str_utils.contains(lexicon, word):
                        new_words.append(word)
                for word in new_words:
                    model.append([word])
                self.emit("new-words", new_words)
            else:
                text = text.strip()
                if text not in lexicon:
                    model.append([text])
                    self.emit("new-words", [text])
        return text
GObject.signal_new("new-words", TextEntryAutoComplete, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,))
