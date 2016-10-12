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

'''
Provide an interface for the GUI to access the SCM controlling the source
'''

_BACKEND = {}
_MISSING_BACKEND = {}

def add_back_end(newifce):
    if newifce.is_available:
        _BACKEND[newifce.name] = newifce
    else:
        _MISSING_BACKEND[newifce.name] = newifce

def backend_requirements():
    msg = _('No back ends are available. SCM systems:') + os.linesep
    for key in list(_MISSING_BACKEND.keys()):
        msg += '\t' + _MISSING_BACKEND[key].requires() + os.linesep
    msg += _("are the ones that are usnderstood.")
    return msg

def report_backend_requirements():
    from aipoed.gui import dialogue
    dialogue.main_window.inform_user(backend_requirements(), parent=parent)

def avail_backends():
    return list(_BACKEND.keys())

def playground_type(dir_path=None):
    # TODO: cope with nested playgrounds of different type and go for closest
    # TODO: give preference to quilt if both found to allow quilt to be used on hg?
    for bname in list(_BACKEND.keys()):
        if _BACKEND[bname].dir_is_in_valid_pgnd(dir_path):
            return bname
    return None

def create_new_playground(pgnd_dir, backend):
    if backend:
        return _BACKEND[backend].do_init_dir(pgnd_dir)
    else:
        return SCM.do_init_dir(pgnd_dir)

def clone_repo_as(repo_path, dir_path, backend):
    return _BACKEND[backend].do_clone_as(repo_path, dir_path)

def choose_scm_backend():
    bel = avail_backends()
    if len(bel) == 0:
        report_backend_requirements()
        return None
    elif len(bel) == 1:
        return bel[0]
    from aipoed.gui import dialogue
    return dialogue.SelectFromListDialog(olist=bel, prompt=_('Choose SCM back end:')).make_selection()

class DummyTableData:
    is_current = True
    def reset(self):
        return self
    @staticmethod
    def iter_rows():
        for row in []:
            yield row

class _NULL_BACKEND:
    name = "os"
    cmd_label = "null"
    in_valid_pgnd = False
    pgnd_is_mutable = False
    @staticmethod
    def copy_clean_version_to(filepath, target_name):
        '''
        Copy a clean version of the named file to the specified target
        '''
        assert False, "Should not be called for null interface"
    @staticmethod
    def do_import_patch(patch_filepath):
        '''
        Copy a clean version of the named file to the specified target
        '''
        assert False, "Should not be called for null interface"
    @staticmethod
    def get_author_name_and_email():
        return None
    @staticmethod
    def get_branches_table_data():
        return DummyTableData()
    @staticmethod
    def get_log_table_data():
        return DummyTableData()
    @staticmethod
    def get_commit_message(commit=None):
        return None
    @staticmethod
    def get_commit_show(commit):
        return None
    @staticmethod
    def get_diff(*args):
        return ""
    @staticmethod
    def get_extension_enabled(extension):
        return False
    @staticmethod
    def get_file_status_digest():
        '''
        Get the Sha1 digest of the SCM view of the files' status
        '''
        return None
    @staticmethod
    def get_files_with_uncommitted_changes(files=None):
        '''
        Get the subset of files which have uncommitted SCM changes.  If files
        is None assume all files in current directory.
        '''
        return []
    @staticmethod
    def get_heads_data():
        return []
    @staticmethod
    def get_history_data(rev=None, maxitems=None):
        return []
    @staticmethod
    def get_index_file_db():
        from aipoed.gui import fsdb
        return fsdb.NullFileDb()
    @staticmethod
    def get_parents_data(rev=None):
        return []
    @staticmethod
    def get_path_table_data():
        return []
    @staticmethod
    def get_playground_root():
        return None
    @staticmethod
    def get_remotes_table_data():
        return DummyTableData()
    @staticmethod
    def get_revision(filepath=None):
        '''
        Return the SCM revision for the named file or the whole playground
        if the filepath is None
        '''
        return None
    @staticmethod
    def get_stashes_table_data():
        return DummyTableData()
    @staticmethod
    def get_tags_table_data():
        return DummyTableData()
    @staticmethod
    def get_wd_file_db():
        '''
        Get the SCM view of the current directory
        '''
        from aipoed.gui import fsdb
        return fsdb.OsFileDb()
    @staticmethod
    def is_ready_for_import():
        '''
        Is the SCM in a position to accept an import?
        '''
        return (False, _("No (or unsupported) underlying SCM."))

SCM = _NULL_BACKEND

def get_ifce(dir_path=None):
    global SCM
    pgt = playground_type(dir_path)
    SCM = _NULL_BACKEND if pgt is None else _BACKEND[pgt]
    return SCM

def check_interfaces(args):
    from aipoed import enotify
    events = 0
    curr_scm = SCM
    get_ifce()
    if curr_scm != SCM:
        from aipoed.scm.events import E_NEW_SCM
        events |= E_NEW_SCM
        if SCM.in_valid_pgnd:
            import os
            from aipoed import options
            from aipoed.gui import recollect
            from aipoed.scm.gui import wspce
            newdir = SCM.get_playground_root()
            if not os.path.samefile(newdir, os.getcwd()):
                os.chdir(newdir)
                events |= enotify.E_CHANGE_WD
            wspce.add_workspace_path(newdir)
            recollect.set("workspace", "last_used", newdir)
            options.load_pgnd_options()
    from aipoed.pm.gui import ifce as pm_ifce
    curr_pm = pm_ifce.PM
    pm_ifce.get_ifce()
    if curr_pm != pm_ifce.PM and not enotify.E_CHANGE_WD & events:
        from aipoed.pm.events import E_NEW_PM
        events |= E_NEW_PM
    return events

def init_current_dir(backend):
    import os
    from aipoed import enotify
    result = create_new_playground(os.getcwd(), backend)
    events = 0
    curr_scm = SCM
    get_ifce()
    if curr_scm != SCM:
        from aipoed.scm.events import E_NEW_SCM
        events |= E_NEW_SCM
    from aipoed.pm.gui import ifce as pm_ifce
    curr_pm = pm_ifce.PM
    pm_ifce.get_ifce()
    if curr_pm != pm_ifce.PM:
        from aipoed.pm.events import E_NEW_PM
        events |= E_NEW_PM
    if SCM.in_valid_pgnd:
        from aipoed.scm.gui import wspce
        from aipoed.gui import recollect
        curr_dir = os.getcwd()
        wspce.add_workspace_path(curr_dir)
        recollect.set("workspace", "last_used", curr_dir)
    if events:
        enotify.notify_events(events)
    return result

def init():
    import os
    from aipoed import options
    from aipoed import enotify
    orig_dir = os.getcwd()
    options.load_global_options()
    get_ifce()
    if SCM.in_valid_pgnd:
        root = SCM.get_playground_root()
        os.chdir(root)
        from aipoed.scm.gui import wspce
        from aipoed.gui import recollect
        wspce.add_workspace_path(root)
        recollect.set("workspace", "last_used", root)
    from aipoed.pm.gui import ifce as pm_ifce
    pm_ifce.get_ifce()
    curr_dir = os.getcwd()
    options.reload_pgnd_options()
    from aipoed.gui.console import LOG
    LOG.start_cmd("Working Directory: {0}\n".format(curr_dir))
    if SCM.in_valid_pgnd:
        LOG.append_stdout('In valid repository\n')
    else:
        LOG.append_stderr('NOT in valid repository\n')
    LOG.end_cmd()
    # NB: need to send either enotify.E_CHANGE_WD or E_NEW_SCM|E_NEW_PM to ensure action sates get set
    if not os.path.samefile(orig_dir, curr_dir):
        enotify.notify_events(enotify.E_CHANGE_WD, new_wd=curr_dir)
    else:
        from aipoed.scm.events import E_NEW_SCM
        from aipoed.pm.events import E_NEW_PM
        enotify.notify_events(E_NEW_SCM|E_NEW_PM)
    from aipoed.gui import auto_update
    auto_update.set_initialize_event_flags(check_interfaces)
