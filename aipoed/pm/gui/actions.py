### Copyright (C) 2011-2015 Peter Williams <pwil3058@gmail.com>
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

'''
Workspace status action groups
'''

from aipoed import enotify
from aipoed import pm

from aipoed.gui import actions

AC_NOT_IN_PM_PGND, AC_IN_PM_PGND, AC_IN_PM_PGND_MUTABLE, AC_IN_PM_PGND_MASK = actions.ActionCondns.new_flags_and_mask(3)
AC_NOT_PMIC, AC_PMIC, AC_PMIC_MASK = actions.ActionCondns.new_flags_and_mask(2)

def get_in_pm_pgnd_condns():
    if pm.gui.ifce.PM.in_valid_pgnd:
        if pm.gui.ifce.PM.pgnd_is_mutable:
            conds = AC_IN_PM_PGND | AC_IN_PM_PGND_MUTABLE
        else:
            conds = AC_IN_PM_PGND
    else:
        conds = AC_NOT_IN_PM_PGND
    return actions.MaskedCondns(conds, AC_IN_PM_PGND_MASK)

def get_pmic_condns():
    return actions.MaskedCondns(AC_PMIC if pm.gui.ifce.PM.is_poppable else AC_NOT_PMIC, AC_PMIC_MASK)

def _update_class_indep_pm_pgnd_cb(**kwargs):
    condns = get_in_pm_pgnd_condns()
    actions.CLASS_INDEP_AGS.update_condns(condns)
    actions.CLASS_INDEP_BGS.update_condns(condns)

def _update_class_indep_pmic_cb(**kwargs):
    condns = get_pmic_condns()
    actions.CLASS_INDEP_AGS.update_condns(condns)
    actions.CLASS_INDEP_BGS.update_condns(condns)

enotify.add_notification_cb(enotify.E_CHANGE_WD|pm.E_NEW_PM, _update_class_indep_pm_pgnd_cb)
enotify.add_notification_cb(pm.E_PATCH_STACK_CHANGES|pm.E_NEW_PM|enotify.E_CHANGE_WD, _update_class_indep_pmic_cb)

class WDListenerMixin:
    def __init__(self):
        self.add_notification_cb(enotify.E_CHANGE_WD|pm.E_NEW_PM, self.pm_pgnd_condns_change_cb)
        self.add_notification_cb(pm.E_PATCH_STACK_CHANGES|pm.E_NEW_PM|enotify.E_CHANGE_WD, self.pmic_condns_change_cb)
        condn_set = get_in_pm_pgnd_condns() | get_pmic_condns()
        self.action_groups.update_condns(condn_set)
        try:
            self.button_groups.update_condns(condn_set)
        except AttributeError:
            pass
    def pm_pgnd_condns_change_cb(self, **kwargs):
        condns = get_in_pm_pgnd_condns()
        self.action_groups.update_condns(condns)
        try:
            self.button_groups.update_condns(condns)
        except AttributeError:
            pass
    def pmic_condns_change_cb(self, **kwargs):
        condns = get_pmic_condns()
        self.action_groups.update_condns(condns)
        try:
            self.button_groups.update_condns(condns)
        except AttributeError:
            pass
