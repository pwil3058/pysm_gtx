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

"""SCM interface for Git (git)"""

import os
import re
import hashlib
import errno

from gi.repository import Pango

from aipoed import CmdResult
from aipoed import runext
from aipoed import enotify
from aipoed import scm
from aipoed import utils

from aipoed.decorators import singleton
from aipoed.patch_diff import patchlib

from aipoed.gui import table

from aipoed.git.gui import fsdb_git

def do_action_cmd(cmd, success_emask, fail_emask, eflag_modifiers):
    from aipoed.gui import console
    # TODO: improve do_action_cmd() and move to runext
    result = runext.run_cmd_in_console(console.LOG, cmd)
    # Because git uses stderr to report progress etc we should consider
    # a warning a success
    if result.is_less_than_error:
        if success_emask:
            enotify.notify_events(success_emask)
        return result
    else:
        if fail_emask:
            enotify.notify_events(fail_emask)
        eflags = CmdResult.ERROR
        for tgt_string, suggestion in eflag_modifiers:
            if result.stderr.find(tgt_string) != -1:
                eflags |= suggestion
        return CmdResult(eflags, result.stdout, result.stderr)

@singleton
class Interface:
    name = "git"
    @staticmethod
    def __getattr__(attr_name):
        if attr_name == "is_available":
            try:
                return runext.run_cmd(["git", "version"]).is_ok
            except OSError as edata:
                if edata.errno == errno.ENOENT:
                    return False
                else:
                    raise
        if attr_name == "in_valid_pgnd": return runext.run_cmd(["git", "config", "--local", "-l"]).is_ok
        raise AttributeError(attr_name)
    @staticmethod
    def copy_clean_version_to(filepath, target_name):
        contents = runext.run_get_cmd(["git", "cat-file", "blob", "HEAD:{}".format(filepath)])
        if contents:
            utils.ensure_file_dir_exists(target_name)
            with open(target_name, "w") as fobj:
                fobj.write(contents)
    @staticmethod
    def dir_is_in_valid_pgnd(dir_path=None):
        if dir_path:
            orig_dir_path = os.getcwd()
            os.chdir(dir_path)
        result = runext.run_cmd(["git", "config", "--local", "-l"])
        if dir_path:
            os.chdir(orig_dir_path)
        return result.is_ok
    @staticmethod
    def do_add_fsis_to_index(fsi_list, force=False):
        if force:
            cmd = ["git", "add", "-f", "--"] + fsi_list
        else:
            cmd = ["git", "add", "--"] + fsi_list
        return do_action_cmd(cmd, scm.E_INDEX_MOD|scm.E_FILE_CHANGES, None, [("Use -f if you really want to add them.", CmdResult.Suggest.FORCE)])
    @staticmethod
    def do_amend_commit(msg):
        cmd = ['git', 'commit', '--amend', '-m', msg]
        return do_action_cmd(cmd, scm.E_INDEX_MOD|scm.E_COMMIT|scm.E_FILE_CHANGES, None, [])
    @staticmethod
    def do_checkout_branch(branch):
        cmd = ["git", "checkout", branch]
        return do_action_cmd(cmd, scm.E_BRANCH|enotify.E_CHANGE_WD, None, [])
    @staticmethod
    def do_checkout_tag(tag):
        cmd = ["git", "checkout", tag]
        return do_action_cmd(cmd, scm.E_TAG|enotify.E_CHANGE_WD, None, [])
    @staticmethod
    def do_clone_as(repo, tgtdir=None):
        cmd = ["git", "clone", repo]
        if tgtdir is not None:
            cmd.append(tgtdir)
        return do_action_cmd(cmd, scm.E_CLONE, None, [])
    @staticmethod
    def do_commit_staged_changes(msg):
        cmd = ["git", "commit", "-m", msg]
        return do_action_cmd(cmd, scm.E_INDEX_MOD|scm.E_COMMIT|scm.E_FILE_CHANGES, None, [])
    @staticmethod
    def do_create_branch(branch, target=None, force=False):
        cmd = ["git", "branch"]
        if force:
            cmd.append("-f")
        cmd.append(branch)
        if target:
            cmd.append(target)
        return do_action_cmd(cmd, scm.E_BRANCH, None, [("already exists", CmdResult.Suggest.FORCE_OR_RENAME)])
    @classmethod
    def do_import_patch(cls, patch_filepath):
        ok_to_import, msg = cls.is_ready_for_import()
        if not ok_to_import:
            return CmdResult.error(stderr=msg)
        epatch = patchlib.Patch.parse_text_file(patch_filepath)
        description = epatch.get_description()
        if not description:
            return CmdResult.error(stderr="Empty description")
        result = runext.run_cmd(["git", "apply", patch_filepath])
        if not result.is_less_than_error:
            return result
        result = runext.run_cmd(["git", "add"] + epatch.get_file_paths(1))
        if not result.is_less_than_error:
            return result
        return runext.run_cmd(["git", "commit", "-q", "-m", description])
    @staticmethod
    def do_init_dir(tgtdir=None):
        cmd = ["git", "init"]
        if tgtdir is not None:
            cmd += ["--", tgtdir]
        return do_action_cmd(cmd, scm.E_NEW_SCM, None, [])
    @staticmethod
    def do_pull_from_repo(repo=None):
        cmd = ["git", "pull"]
        if repo is not None:
            cmd.append(repo)
        return do_action_cmd(cmd, scm.E_PULL, None, [])
    @staticmethod
    def do_push_to_repo(repo=None):
        cmd = ["git", "push"]
        if repo is not None:
            cmd.append(repo)
        return do_action_cmd(cmd, scm.E_PUSH, None, [])
    @staticmethod
    def do_remove_files_from_index(file_list):
        cmd = ["git", "reset", "HEAD", "--"] + file_list
        return do_action_cmd(cmd, scm.E_INDEX_MOD, None, [])
    @staticmethod
    def do_remove_files_in_index(file_list, force=False, cache=False):
        if force:
            assert not cache
            cmd = ["git", "rm", "-f", "--"] + file_list
        elif cache:
            assert not force
            cmd = ["git", "rm", "--cache", "--"] + file_list
        else:
            cmd = ["git", "rm", "--"] + file_list
        return do_action_cmd(cmd, scm.E_INDEX_MOD, None, [("--cache", CmdResult.Suggest.CACHE), ("or -f to force removal", CmdResult.Suggest.FORCE)])
    @staticmethod
    def do_rename_fsi_in_index(fsi_path, destn, overwrite=False):
        if overwrite:
            cmd = ["git", "mv", "-f", fsi_path, destn]
        else:
            cmd = ["git", "mv", fsi_path, destn]
        return do_action_cmd(cmd, scm.E_INDEX_MOD, None, [("or -f to force", CmdResult.Suggest.OVERWRITE)])
    @staticmethod
    def do_set_tag(tag, annotated=False, msg=None, signed=False, key_id=None, target=None, force=False):
        cmd = ["git", "tag"]
        if force:
            cmd.append("-f")
        if annotated:
            cmd += ["-m", msg]
            if signed:
                cmd.append("-s")
            if key_id:
                cmd += ["-u", key_id]
        cmd.append(tag)
        if target:
            cmd.append(target)
        return do_action_cmd(cmd, scm.E_TAG, None, [("already exists", CmdResult.Suggest.FORCE)])
    @staticmethod
    def do_stash_apply(reinstate_index=False, stash=None):
        cmd = ["git", "stash", "apply"]
        if reinstate_index:
            cmd.append("--index")
        if stash:
            cmd.append(stash)
        return do_action_cmd(cmd, scm.E_STASH|scm.E_FILE_CHANGES, None, [])
    @staticmethod
    def do_stash_branch(branch_name, stash=None):
        cmd = ["git", "stash", "branch", branch_name]
        if stash:
            cmd.append(stash)
        return do_action_cmd(cmd, scm.E_STASH, None, [])
    @staticmethod
    def do_stash_drop(stash=None):
        cmd = ["git", "stash", "drop"]
        if stash:
            cmd.append(stash)
        return do_action_cmd(cmd, scm.E_STASH, None, [])
    @staticmethod
    def do_stash_pop(reinstate_index=False, stash=None):
        cmd = ["git", "stash", "pop"]
        if reinstate_index:
            cmd.append("--index")
        if stash:
            cmd.append(stash)
        return do_action_cmd(cmd, scm.E_STASH, None, [])
    @staticmethod
    def do_stash_save(keep_index=False, include_untracked=False, include_all=False, msg=None):
        cmd = ["git", "stash", "save"]
        if keep_index:
            cmd.append("--keep-index")
        if include_untracked:
            cmd.append("--include-untracked")
        if include_all:
            cmd.append("--all")
        if msg:
            cmd.append(msg)
        return do_action_cmd(cmd, scm.E_STASH, None, [])
    @staticmethod
    def get_author_name_and_email():
        import email.utils
        email_addr = runext.run_get_cmd(["git", "config", "user.email"], default=None)
        if not email_addr:
            email_addr = os.environ.get("GIT_AUTHOR_EMAIL", None)
        if not email_addr:
            return None
        name = runext.run_get_cmd(["git", "config", "user.name"], default=None)
        if not name:
            name = utils.get_first_in_envar(["GIT_AUTHOR_NAME", "LOGNAME", "GECOS"], default=_("unknown"))
        return email.utils.formataddr((name, email_addr))
    @staticmethod
    def get_signing_key():
        return runext.run_get_cmd(["git", "config", "user.signingkey"], default="")
    @staticmethod
    def get_commit_template():
        file_path = runext.run_get_cmd(["git", "config", "commit.template"], default="")
        return open(file_path).read() if os.path.exists(file_path) else ""
    @staticmethod
    def get_clean_contents(file_path):
        return runext.run_get_cmd(["git", "cat-file", "blob", "HEAD:{}".format(file_path)], do_rstrip=False, default=None, decode_stdout=False)
    @staticmethod
    def get_log_table_data():
        from aipoed.git.gui import log
        return log.LogTableData()
    @staticmethod
    def get_commit_message(commit=None):
        cmd = ["git", "log", "-n", "1", "--pretty=format:%s%n%n%b"]
        if commit:
            cmd.append(commit)
        result = runext.run_cmd(cmd)
        if result.is_ok:
            return result.stdout
        return None
    @staticmethod
    def get_commit_show(commit):
        cmd = ["git", "show", commit]
        result = runext.run_cmd(cmd)
        if result.is_ok:
            return result.stdout
        return None
    @staticmethod
    def get_diff(*args):
        return runext.run_get_cmd(["git", "diff", "--no-ext-diff"] + list(args), do_rstrip=False)
    @staticmethod
    def get_file_status_digest():
        stdout = runext.run_get_cmd(["git", "status", "--porcelain", "--ignored", "--untracked=all"], default=None)
        return None if stdout is None else hashlib.sha1(stdout).digest()
    @staticmethod
    def get_files_with_uncommitted_changes(files=None):
        cmd = ["git", "status", "--porcelain", "--untracked-files=no",]
        if files:
            cmd += files
        return [line[3:] for line in runext.run_get_cmd(cmd).splitlines()]
    @staticmethod
    def get_index_file_db():
        return fsdb_git.IndexFileDb()
    @staticmethod
    def get_playground_root():
        if not runext.run_cmd(["git", "config", "--local", "-l"]).is_ok:
            return None
        dirpath = os.getcwd()
        while True:
            if os.path.exists(os.path.join(dirpath, ".git")):
                return dirpath
            else:
                dirpath, basename = os.path.split(dirpath)
                if not basename:
                    break
        return None
    def get_remotes_table_data():
        from aipoed.git.gui import remotes
        return remote.RemoteRepoTableData()
    @staticmethod
    def get_revision(filepath=None):
        cmd = ["git", "show",]
        if filepath:
            cmd.append(filepath)
        return runext.run_get_cmd(cmd).stdout.splitlines()[0][7:]
    @staticmethod
    def get_stash_diff(stash=None):
        return runext.run_get_cmd(["git", "stash", "show", "-p"] + runext.OPTNL_ARG(stash), default="", do_rstrip=False)
    @staticmethod
    def get_stashes_table_data():
        from aipoed.git.gui import stashes
        return stashes.StashTableData()
    @staticmethod
    def get_tags_table_data():
        from aipoed.git.gui import tags
        return tags.TagTableData()
    @staticmethod
    def get_wd_file_db():
        return fsdb_git.WsFileDb()
    @staticmethod
    def is_ready_for_import():
        return (True, "") if index_is_empty() else (False, _("Index is NOT empty\n"))
    @staticmethod
    def launch_difftool(*args):
        return runext.run_cmd_in_bgnd(["git", "difftool", "--noprompt"] + list(args))

def index_is_empty():
    stdout = runext.run_get_cmd(["git", "status", "--porcelain", "--untracked-files=no"])
    for line in stdout.splitlines():
        if line[0] != " ":
            return False
    return True

SCM = Interface()
from aipoed.scm.gui import ifce as scm_ifce
scm_ifce.add_back_end(SCM)
