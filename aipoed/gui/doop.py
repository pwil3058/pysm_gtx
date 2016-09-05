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

from . import dialogue

class DoOperationMixin(dialogue.ClientMixin):
    def do_op_rename_overwrite_force_or_cancel(self, target, do_op, rename_target):
        overwrite = False
        force = False
        while True:
            with self.showing_busy():
                result = do_op(target, overwrite=overwrite, force=force)
            if (not overwrite and result.suggests_overwrite) or (not force and result.suggests_force):
                resp = self.ask_rename_overwrite_force_or_cancel(result)
                if resp == Gtk.ResponseType.CANCEL:
                    return CmdResult.ok() # we don't want to be a nag
                elif resp == dialogue.Response.OVERWRITE:
                    overwrite = True
                elif resp == dialogue.Response.FORCE:
                    force = True
                elif resp == dialogue.Response.RENAME:
                    target = rename_target(target)
                    if target is None:
                        break
                continue
            break
        self.report_any_problems(result)
        return result
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
