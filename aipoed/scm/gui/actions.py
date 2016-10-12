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
from aipoed import scm

from aipoed.gui import actions

AC_NOT_IN_SCM_PGND, AC_IN_SCM_PGND, AC_IN_SCM_PGND_MASK = actions.ActionCondns.new_flags_and_mask(2)

def get_in_scm_pgnd_condns():
    return actions.MaskedCondns(AC_IN_SCM_PGND if scm.gui.ifce.SCM.in_valid_pgnd else AC_NOT_IN_SCM_PGND, AC_IN_SCM_PGND_MASK)

def _update_class_indep_scm_pgnd_cb(**kwargs):
    condns = get_in_scm_pgnd_condns()
    actions.CLASS_INDEP_AGS.update_condns(condns)
    actions.CLASS_INDEP_BGS.update_condns(condns)

enotify.add_notification_cb(enotify.E_CHANGE_WD|scm.E_NEW_SCM, _update_class_indep_scm_pgnd_cb)

class WDListenerMixin:
    def __init__(self):
        self.add_notification_cb(enotify.E_CHANGE_WD|scm.E_NEW_SCM, self.scm_pgnd_conds_change_cb)
        self.scm_pgnd_conds_change_cb()
    def scm_pgnd_conds_change_cb(self, **kwargs):
        condns = get_in_scm_pgnd_condns()
        self.action_groups.update_condns(condns)
        try:
            self.button_groups.update_condns(condns)
        except AttributeError:
            pass
