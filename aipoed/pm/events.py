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

E_NEW_PM = enotify.new_event_flag()

E_PUSH, E_POP, E_NEW_PATCH, E_PATCH_STACK_CHANGES = enotify.new_event_flags_and_mask(3)
E_DELETE_PATCH, E_MODIFY_PATCH, E_MODIFY_GUARDS, E_PATCH_QUEUE_CHANGES = enotify.new_event_flags_and_mask(3)
E_PATCH_LIST_CHANGES = E_PATCH_STACK_CHANGES|E_PATCH_QUEUE_CHANGES

E_FILE_ADDED, E_FILE_DELETED, E_PATCH_REFRESH, E_FILE_CHANGES = enotify.new_event_flags_and_mask(3)
E_FILE_MOVED = E_FILE_ADDED|E_FILE_DELETED
