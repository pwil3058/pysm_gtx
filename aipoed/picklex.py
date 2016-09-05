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

class PickeExtensibleObject(object):
    '''A base class for pickleable objects that can cope with modifications'''
    RENAMES = dict()
    NEW_FIELDS = dict()
    def __setstate__(self, state):
        self.__dict__ = state
        for old_field in self.RENAMES:
            if old_field in self.__dict__:
                self.__dict__[self.RENAMES[old_field]] = self.__dict__.pop(old_field)
    def __getstate__(self):
        return self.__dict__
    def __getattr__(self, attr):
        if attr in self.NEW_FIELDS:
            return self.NEW_FIELDS[attr]
        raise AttributeError
