### -*- coding: utf-8 -*-
###
###  Copyright 2016 Peter Williams <pwil3058@gmail.com>
###
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

import os
import collections
import gettext

from . import i18n

HOME = os.path.expanduser("~")
PKG_NAME = "aipoed"
VERSION = "0.1.0"
LOCALE_DIR = i18n.find_locale_dir()

gettext.install(PKG_NAME, LOCALE_DIR)

class Result:
    OK = 0
    _NFLAGS = 2
    WARNING, \
    ERROR = [2 ** flag_num for flag_num in range(_NFLAGS)]
    MASK = OK | WARNING | ERROR

class Suggestion:
    NFLAGS = 12
    FORCE, \
    REFRESH, \
    RECOVER, \
    RENAME, \
    DISCARD, \
    ABSORB, \
    EDIT, \
    MERGE, \
    OVERWRITE, \
    CACHE, \
    SKIP, \
    SKIP_ALL = [2 ** flag_num for flag_num in range(Result._NFLAGS, NFLAGS + Result._NFLAGS)]
    ALL = 2 ** (NFLAGS + Result._NFLAGS) - 1 - Result.MASK
    # Some commonly used combinations
    OVERWRITE_OR_RENAME = OVERWRITE | RENAME
    FORCE_OR_REFRESH = FORCE | REFRESH
    FORCE_OR_ABSORB = FORCE | ABSORB
    FORCE_OR_CACHE = FORCE | CACHE
    FORCE_OR_RENAME = FORCE | RENAME
    FORCE_ABSORB_OR_REFRESH = FORCE | ABSORB | REFRESH
    MERGE_OR_DISCARD = MERGE | DISCARD

assert(Result.MASK & Suggestion.ALL == 0)

class _OperationsMixin:
    Suggest = Suggestion
    @property
    def is_ok(self):
        assert self.ecode == 0 or self.ecode & Result.MASK != 0
        return self.ecode == Result.OK
    @property
    def is_warning(self):
        return self.ecode & Result.MASK == Result.WARNING
    @property
    def is_error(self):
        return self.ecode & Result.MASK == Result.ERROR
    @property
    def is_less_than_error(self):
        return self.ecode & Result.MASK != Result.ERROR
    @property
    def suggests_force(self):
        return self.ecode & Suggestion.FORCE
    @property
    def suggests_refresh(self):
        return self.ecode & Suggestion.REFRESH
    @property
    def suggests_recover(self):
        return self.ecode & Suggestion.RECOVER
    @property
    def suggests_rename(self):
        return self.ecode & Suggestion.RENAME
    @property
    def suggests_discard(self):
        return self.ecode & Suggestion.DISCARD
    @property
    def suggests_absorb(self):
        return self.ecode & Suggestion.ABSORB
    @property
    def suggests_edit(self):
        return self.ecode & Suggestion.EDIT
    @property
    def suggests_overwrite(self):
        return self.ecode & Suggestion.OVERWRITE
    @property
    def suggests_force(self):
        return self.ecode & Suggestion.FORCE
    @property
    def suggests_cache(self):
        return self.ecode & Suggestion.CACHE
    @property
    def suggests_skip(self):
        return self.ecode & Suggestion.SKIP
    @property
    def suggests_skip_all(self):
        return self.ecode & Suggestion.SKIP_ALL
    def suggests(self, suggestion):
        return self.ecode & suggestion != 0

# result of running and external command
class CmdResult(collections.namedtuple('CmdResult', ['ecode', 'stdout', 'stderr']), Result, _OperationsMixin):
    def __str__(self):
        return "CmdResult(ecode={0:b}, stdout={1}, stderr={2})".format(self.ecode, self.stdout, self.stderr)
    def __or__(self, suggestions):
        assert suggestions & Suggestion.ALL == suggestions
        return self.__class__(self.ecode | suggestions, self.stdout, self.stderr)
    def __sub__(self, suggestions):
        assert suggestions & Suggestion.ALL == suggestions
        return self.__class__(self.ecode & ~suggestions, self.stdout, self.stderr)
    def mapped_for_warning(self, sanitize_stderr=None):
        if self.ecode == 0:
            if (self.stderr if sanitize_stderr is None else sanitize_stderr(self.stderr)):
                return self.__class__(Result.WARNING, self.stdout, self.stderr)
            else:
                return self.__class__(Result.OK, self.stdout, self.stderr)
        else:
            return self.__class__(Result.ERROR, self.stdout, self.stderr)
    def mapped_for_suggestions(self, suggestion_table):
        ecode = self.ecode
        for suggestion, criteria in suggestion_table:
            if criteria(self):
                ecode |= suggestion
        return self.__class__(ecode, self.stdout, self.stderr)
    @classmethod
    def ok(cls, stdout="", stderr=""):
        return cls(Result.OK, stdout, stderr)
    @classmethod
    def warning(cls, stdout="", stderr=""):
        return cls(Result.WARNING, stdout, stderr)
    @classmethod
    def error(cls, stdout="", stderr=""):
        return cls(Result.ERROR, stdout, stderr)
    @property
    def message(self):
        if self.stdout:
            return "\n".join([self.stdout, self.stderr]) if self.stderr else self.stdout
        else:
            return self.stderr

# result returned from an internal "action" function/method
class ActionResult(collections.namedtuple('ActionResult', ['ecode', 'message']), Result, _OperationsMixin):
    def __str__(self):
        return "ActionResult(ecode={0:b}, message={1})".format(self.ecode, self.message)
    def __or__(self, suggestions):
        assert suggestions & Suggestion.ALL == suggestions
        return self.__class__(self.ecode | suggestions, self.message)
    def __sub__(self, suggestions):
        assert suggestions & Suggestion.ALL == suggestions
        return self.__class__(self.ecode & ~suggestions, self.message)
    @classmethod
    def ok(cls, message=""):
        return cls(Result.OK, message)
    @classmethod
    def warning(cls, message=""):
        return cls(Result.WARNING, message)
    @classmethod
    def error(cls, message=""):
        return cls(Result.ERROR, message)

class CmdFailure(Exception):
    def __init__(self, result):
        self.result = result


if os.name == 'nt' or os.name == 'dos':
    def _which(cmd):
        """Return the path of the executable for the given command"""
        for dirpath in os.environ['PATH'].split(os.pathsep):
            potential_path = os.path.join(dirpath, cmd)
            if os.path.isfile(potential_path) and \
               os.access(potential_path, os.X_OK):
                return potential_path
        return None


    NT_EXTS = ['.bat', '.bin', '.exe']


    def which(cmd):
        """Return the path of the executable for the given command"""
        path = _which(cmd)
        if path:
            return path
        _, ext = os.path.splitext(cmd)
        if ext in NT_EXTS:
            return None
        for ext in NT_EXTS:
            path = _which(cmd + ext)
            if path is not None:
                return path
        return None
else:
    def which(cmd):
        """Return the path of the executable for the given command"""
        for dirpath in os.environ['PATH'].split(os.pathsep):
            potential_path = os.path.join(dirpath, cmd)
            if os.path.isfile(potential_path) and \
               os.access(potential_path, os.X_OK):
                return potential_path
        return None

# import some modules
from . import options
