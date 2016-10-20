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

def create_flag_generator():
    """
    Create a new flag generator
    """
    next_flag_num = 0
    while True:
        yield 2 ** next_flag_num
        next_flag_num += 1

def path_rel_home(path):
    """Return the given path as a path relative to user's home directory."""
    import os
    import urllib.parse
    pr = urllib.parse.urlparse(path)
    if pr.scheme and pr.scheme != "file":
        return path
    if pr.path.startswith("~" + os.sep):
        return pr.path
    return os.path.join("~", os.path.relpath(os.path.abspath(pr.path), os.getenv("HOME")))

def cwd_rel_home():
    """Return path of current working directory relative to user's home
    directory.
    """
    import os
    return path_rel_home(os.getcwd())

quote_if_needed = lambda string: string if string.count(" ") == 0 else "\"" + string + "\""

quoted_join = lambda strings, joint=" ": joint.join((quote_if_needed(file_path) for file_path in strings))

def strings_to_quoted_list_string(strings):
    if len(strings) == 1:
        return quote_if_needed(strings[0])
    return quoted_join(strings[:-1], ", ") + _(" and ") + quote_if_needed(strings[-1])

def get_first_in_envar(envar_list, default=""):
    import os
    for envar in envar_list:
        try:
            value = os.environ[envar]
            if value != '':
                return value
        except KeyError:
            continue
    return default

def is_utf8_compliant(text):
    try:
        text.encode('utf-8')
    except UnicodeError:
        return False
    return True

ISO_8859_CODECS = ['iso-8859-{0}'.format(x) for x in range(1, 17)]
ISO_2022_CODECS = ['iso-2022-jp', 'iso-2022-kr'] + \
    ['iso-2022-jp-{0}'.format(x) for x in list(range(1, 3)) + ['2004', 'ext']]

def make_utf8_compliant(text):
    '''Return a UTF-8 compliant version of text'''
    if text is None:
        return ""
    if isinstance(text, bytes):
        return text.decode("utf-8")
    elif is_utf8_compliant(text):
        return text
    for codec in ISO_8859_CODECS + ISO_2022_CODECS:
        try:
            text = unicode(text, codec).encode('utf-8')
            return text
        except UnicodeError:
            continue
    raise UnicodeError
