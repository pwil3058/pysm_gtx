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

"""
Wrappers for common (but complex) "do" operations.
"""

from gi.repository import Gtk

from aipoed.gui import dialogue

# TODO: remove inheritence to make mix and match easier
class DoOperationMixin(dialogue.ClientMixin):
    def ask_destination(self, file_paths, prompt=_("Enter destination path:")):
        if len(file_paths) > 1:
            return self.ask_dir_path(prompt, suggestion=os.path.relpath(os.getcwd()), existing=False)
        else:
            return self.ask_file_path(prompt, suggestion=file_paths[0], existing=False)
    def get_renamed_destn(self, destn, prompt=_("Enter new destination path:")):
        if os.path.isdir(destn):
            return self.ask_dir_path(prompt, suggestion=destn, existing=False)
        else:
            return self.ask_file_path(prompt, suggestion=destn, existing=False)
    @staticmethod
    def expand_destination(destn, file_paths):
        return [os.path.join(destn, os.path.basename(file_path)) for file_path in file_paths]
    def do_op_rename_overwrite_force_or_cancel(self, target, do_op, get_new_name=None):
        overwrite = False
        force = False
        while True:
            with self.showing_busy():
                result = do_op(target, overwrite=overwrite, force=force)
            if (not overwrite and result.suggests_overwrite) or (not force and result.suggests_force):
                resp = self.ask_rename_overwrite_force_or_cancel(result)
                if resp == Gtk.ResponseType.CANCEL:
                    return None
                elif resp == dialogue.Response.OVERWRITE:
                    overwrite = True
                elif resp == dialogue.Response.FORCE:
                    force = True
                elif resp == dialogue.Response.RENAME:
                    target = get_new_name(target) if get_new_name else self.ask_text(_("Name"), name)
                    if target is None:
                        break
                continue
            break
        self.report_any_problems(result)
        return target # let the caller know if a rename occured
    def do_op_rename_overwrite_or_cancel(self, target, do_op, get_new_name=None):
        overwrite = False
        while True:
            with self.showing_busy():
                result = do_op(target, overwrite=overwrite)
            if not overwrite and result.suggests_overwrite:
                resp = self.ask_rename_overwrite_or_cancel(result)
                if resp == Gtk.ResponseType.CANCEL:
                    return None
                elif resp == dialogue.Response.OVERWRITE:
                    overwrite = True
                elif resp == dialogue.Response.RENAME:
                    target = get_new_name(target) if get_new_name else self.ask_text(_("Name"), name)
                    if target is None:
                        break
                continue
            break
        self.report_any_problems(result)
        return target # let the caller know if a rename occured
    def do_op_rename_force_or_cancel(self, name, do_op, get_new_name=None):
        force = False
        while True:
            with self.showing_busy():
                result = do_op(name, force=force)
            if not force and result.suggests_force:
                resp = self.ask_rename_force_or_cancel(result)
                if resp == Gtk.ResponseType.CANCEL:
                    return None
                elif resp == dialogue.Response.FORCE:
                    force = True
                elif resp == dialogue.Response.RENAME:
                    name = get_new_name(name) if get_new_name else self.ask_text(_("Name"), name)
                    if name is None:
                        break
                continue
            break
        self.report_any_problems(result)
        return name
    def do_op_force_or_cancel(self, do_op):
        force = False
        while True:
            with self.showing_busy():
                result = do_op(force=force)
            if not force and result.suggests_force:
                if self.ask_force_or_cancel(result) == dialogue.Response.FORCE:
                    force = True
                    continue
                else:
                    break
            self.report_any_problems(result)
            break
        return result.is_ok
    def do_op_rename_or_cancel(self, name, do_op, get_new_name=None):
        while True:
            with self.showing_busy():
                result = do_op(name)
            if result.suggests_rename:
                if self.ask_rename_or_cancel(result) == dialogue.Response.RENAME:
                    name = get_new_name(name) if get_new_name else self.ask_text(_("Name"), name)
                    if not name:
                        break
                else:
                    return None
            self.report_any_problems(result)
            break
        return name
    def do_op_cache_force_or_cancel(self, do_op):
        force = False
        cache = False
        while True:
            with self.showing_busy():
                result = do_op(force=force, cache=cache)
            if not (cache or force) and result.suggests(result.Suggest.FORCE_OR_CACHE):
                resp = self.accept_suggestion_or_cancel(result, suggestions=[result.Suggest.CACHE, result.Suggest.FORCE])
                if resp == Gtk.ResponseType.CANCEL:
                    return CmdResult.ok() # we don't want to be a nag
                elif resp == dialogue.Response.FORCE:
                    force = True
                elif resp == dialogue.Response.CACHE:
                    cache = True
                continue
            self.report_any_problems(result)
            break
        return result
