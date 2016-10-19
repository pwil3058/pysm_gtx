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

from aipoed import enotify

E_FILE_ADDED, E_FILE_DELETED, E_FILE_MODIFIED, E_FILE_CHANGES = enotify.new_event_flags_and_mask(3)
E_FILE_MOVED = E_FILE_ADDED|E_FILE_DELETED

E_INDEX_MOD, E_COMMIT, E_BACKOUT, E_BRANCH, E_TAG, E_PUSH, E_PULL, E_INIT, E_CLONE, E_STASH, E_FETCH, E_CS_CHANGES = enotify.new_event_flags_and_mask(11)
E_NEW_SCM = E_INIT|E_CLONE

E_CHECKOUT, E_BISECT, E_MERGE, E_UPDATE, E_WD_CHANGES = enotify.new_event_flags_and_mask(4)

E_PGND_RC_CHANGED, E_USER_RC_CHANGED, E_RC_CHANGED = enotify.new_event_flags_and_mask(2)

E_LOG = enotify.new_event_flag()
E_REMOTE = enotify.new_event_flag()
