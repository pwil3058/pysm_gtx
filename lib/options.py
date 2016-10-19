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

'''Manage configurable options'''

# TODO: add mechanism for setting both global and local options
import os
import collections
import configparser

from aipoed import CmdResult

_GLOBAL_CFG_FILE_PATH = ""
GLOBAL_OPTIONS = configparser.SafeConfigParser()

def load_global_options():
    global GLOBAL_OPTIONS
    GLOBAL_OPTIONS = configparser.SafeConfigParser()
    try:
        GLOBAL_OPTIONS.read(_GLOBAL_CFG_FILE_PATH)
    except configparser.ParsingError as edata:
        return CmdResult.error(stderr=_("Error reading global options: {0}\n").format(str(edata)))
    return CmdResult.ok()

def reload_global_options():
    global GLOBAL_OPTIONS
    new_version = configparser.SafeConfigParser()
    try:
        new_version.read(_GLOBAL_CFG_FILE_PATH)
    except configparser.ParsingError as edata:
        return CmdResult.error(stderr=_("Error reading global options: {0}\n").format(str(edata)))
    GLOBAL_OPTIONS = new_version
    return CmdResult.ok()

_PGND_CFG_FILE_PATH = ""
PGND_OPTIONS = configparser.SafeConfigParser()

def load_pgnd_options():
    global PGND_OPTIONS
    PGND_OPTIONS = configparser.SafeConfigParser()
    try:
        PGND_OPTIONS.read(_PGND_CFG_FILE_PATH)
    except configparser.ParsingError as edata:
        return CmdResult.error(stderr=_("Error reading playground options: {0}\n").format(str(edata)))
    return CmdResult.ok()

def reload_pgnd_options():
    global PGND_OPTIONS
    new_version = configparser.SafeConfigParser()
    try:
        new_version.read(_PGND_CFG_FILE_PATH)
    except configparser.ParsingError as edata:
        return CmdResult.error(stderr=_("Error reading playground options: {0}\n").format(str(edata)))
    PGND_OPTIONS = new_version
    return CmdResult.ok()

def initialize(global_config_dir_path, pgnd_config_dir_path=None):
    global _GLOBAL_CFG_FILE_PATH
    global _PGND_CFG_FILE_PATH
    _GLOBAL_CFG_FILE_PATH = os.path.join(global_config_dir_path, "options.cfg") if global_config_dir_path else ""
    _PGND_CFG_FILE_PATH = os.path.join(pgnd_config_dir_path, "options.cfg") if pgnd_config_dir_path else ""
    load_global_options()
    load_pgnd_options()
    define("user", "name", Defn(str, None, _("User's display name e.g. Fred Bloggs")))
    define("user", "email", Defn(str, None, _("User's email address e.g. fred@bloggs.com")))

class OptionError(Exception): pass
class DuplicateDefn(OptionError): pass
class OptionsNotConfigured(OptionError): pass

Defn = collections.namedtuple("Defn", ["str_to_val", "default", "help"])

DEFINITIONS = {}

def define(section, oname, odefn):
    if not section in DEFINITIONS:
        DEFINITIONS[section] = {oname: odefn,}
    elif oname in DEFINITIONS[section]:
        raise DuplicateDefn("{0}:{1} already defined".format(section, oname))
    else:
        DEFINITIONS[section][oname] = odefn

def str_to_bool(string):
    lowstr = string.lower()
    if lowstr in ["true", "yes", "on", "1"]:
        return True
    elif lowstr in ["false", "no", "off", "0"]:
        return False
    else:
        return None

def get(section, oname, pgnd_only=False):
    # This should cause an exception if section:oname is not known
    # which is what we want
    str_to_val = DEFINITIONS[section][oname].str_to_val
    value = None
    if PGND_OPTIONS.has_option(section, oname):
        value = str_to_val(PGND_OPTIONS.get(section, oname))
    elif not pgnd_only and GLOBAL_OPTIONS.has_option(section, oname):
        value = str_to_val(GLOBAL_OPTIONS.get(section, oname))
    return value if value is not None else DEFINITIONS[section][oname].default

def _set_option(options, cfg_file_path, section, oname, value):
    # if the application doesn't set this value then it doesn't want global options
    if not cfg_file_path:
        raise OptionsNotConfigured()
    # Make sure the option has been defined
    assert section in DEFINITIONS and oname in DEFINITIONS[section]
    # NB: just because it's defined doesn't meant that GLOBAL_OPTIONS knows about it
    if not options.has_section(section):
        options.add_section(section)
    if isinstance(value, str) or isinstance(value, bytes):
        from aipoed import utils
        svalue = utils.make_utf8_compliant(value)
    elif isinstance(value, bool):
        svalue = "true" if value else "false"
    else:
        svalue = str(value)
    options.set(section, oname, svalue)
    with open(cfg_file_path, "w") as f_obj:
        options.write(f_obj)

def set_global(section, oname, value):
    return _set_option(GLOBAL_OPTIONS, _GLOBAL_CFG_FILE_PATH, section, oname, value)

def set_pgnd(section, oname, value):
    return _set_option(PGND_OPTIONS, _PGND_CFG_FILE_PATH, section, oname, value)
