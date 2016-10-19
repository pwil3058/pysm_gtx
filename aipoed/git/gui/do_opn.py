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

import os

from aipoed.gui import doop

from .ifce import SCM

class DoOpnMixin(doop.DoOperationMixin):
    def git_do_checkout_branch(self, branch_name):
        with self.showing_busy():
            result = SCM.do_checkout_branch(branch=branch_name)
        self.report_any_problems(result)
    def git_do_create_branch(self, branch_name, target):
        do_op = lambda branch, force: SCM.do_create_branch(branch=branch, target=target, force=force)
        return self.do_op_rename_force_or_cancel(branch_name, do_op)
    def git_do_add_fsis_to_index(self, fsi_paths):
        do_op = lambda force=False: SCM.do_add_fsis_to_index(fsi_paths, force=force)
        return self.do_op_force_or_cancel(do_op)
    def git_do_copy_file_to_index(self, file_path):
        # TODO: move nuts and bolts down to scm_ifce_git
        # TODO: use os_utils function for most of this
        PROMPT = _('Enter target path for copy of "{0}"'.format(file_path))
        as_file_path = self.ask_file_path(PROMPT, existing=False, suggestion=file_path)
        if as_file_path is None or os.path.relpath(as_file_path) == file_path:
            return
        while os.path.exists(as_file_path):
            from gi.repository import Gtk
            from aipoed import CmdResult
            from aipoed.gui import dialogue
            result = CmdResult.error(stderr="{0}: already exists".format(as_file_path)) | CmdResult.Suggest.OVERWRITE_OR_RENAME
            resp = self.ask_rename_overwrite_or_cancel(result)
            if resp == Gtk.ResponseType.CANCEL:
                return
            elif resp == dialogue.Response.OVERWRITE:
                break
            elif resp == dialogue.Response.RENAME:
                as_file_path = self.ask_file_path(PROMPT, existing=False, suggestion=as_file_path)
                if as_file_path is None:
                    return
        import shutil
        from aipoed.gui import console
        console.LOG.start_cmd('cp -p {0} {1}'.format(file_path, as_file_path))
        try:
            shutil.copy2(file_path, as_file_path)
        except IOError as edata:
            console.LOG.append_stderr(str(edata))
            console.LOG.end_cmd()
            self.report_exception_as_error(edata)
            return
        console.LOG.end_cmd()
        self.git_do_add_fsis_to_index([as_file_path])
    def git_do_rename_fsi_in_index(self, fsi_path):
        destn = self.ask_destination([fsi_path])
        if not destn:
            return
        do_op = lambda destn, overwrite=False : SCM.do_rename_fsi_in_index(fsi_path, destn, overwrite=overwrite)
        return self.do_op_rename_overwrite_or_cancel(destn, do_op)
    def git_do_remove_files_in_index(self, file_paths):
        do_op = lambda force=False, cache=False: SCM.do_remove_files_in_index(file_paths, force=force, cache=cache)
        return self.do_op_cache_force_or_cancel(do_op)
