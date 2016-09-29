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

from ...gui import doop

from .ifce import SCM

class DoOpnMixin(doop.DoOperationMixin):
    def git_do_checkout_branch(self, branch_name):
        with self.showing_busy():
            result = SCM.do_checkout_branch(branch=branch_name)
        self.report_any_problems(result)
    def git_do_create_branch(self, branch_name, target):
        do_op = lambda branch, force: SCM.do_create_branch(branch=branch, target=target, force=force)
        self.do_op_rename_force_or_cancel(branch_name, do_op)
