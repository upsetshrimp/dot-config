#!/usr/bin/env python
import argparse
import subprocess
from subprocess import PIPE
import os
import sys
import time
from shutil import copy
from random import randint
from inspect import currentframe
from classes import bcolors

# TODO:
#
# *!*
# clean up messy function roles, can probably get rid of a couple
# of functions (or make more)


HOME = os.path.expanduser("~")
REPO = f'{HOME}/.cfg/'
EDITOR = os.environ['EDITOR']
SHELL = os.environ['SHELL']
SCRIPT_PATH = os.path.realpath(__file__)
BACKUP_PATH = f"{HOME}/old_dotfiles_backup"
LCB = '\u007b'              # {
RCB = '\u007d'              # }
DIVIDER = "----------------------------"
ENCODING = "utf-8"


def find_variants():
    """
    comb through monolith dotfile and find optional bits
    optional bits will be comments that will later be uncommented per request
    """
    print("TODO")


def create_branch(changes: dict):
    """
    input: selections of what to merge from files
    output: branch named HOSTNAME with the changes on file
    """
    print("TODO", changes)


def restore_backup(url):
    """
    input: url containing an old dot-config bare repo
    result: the repo being reinstated in the curreent machine
    TODO make it verify all system changes like PATH and such.
    """
    clone_repo(url)


def get_parser():
    """
    the default parser for this program, contains all the relevent  arguments and parameters.
    """
    parser = argparse.ArgumentParser(
        description="""
        Manage dotfiles with a git bare repo and the help of this simple tool.
        """,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,)
    parser.add_argument('--info', '-i', action="store_true")
    # Capture everything after to pass to the git command
    parser.add_argument('--git-interface', '-g', nargs=argparse.REMAINDER)
    parser.add_argument('--init', action="store_true")
    parser.add_argument('--show-tracked-files', '-f', action="store_true")
    parser.add_argument('--edit-file', '-e', nargs=argparse.REMAINDER)
    parser.add_argument('--apply-changes', '-a', action='store_true')
    parser.add_argument('--add-to-path', action="store_true")
    parser.add_argument('--clone-and-checkout', '-c', nargs=1)
    parser.add_argument('--dev-test', action="store_true")
    return parser


def _do_nothing():
    line = f"{bcolors.FAIL}{bcolors.BOLD}{currentframe().f_back.f_lineno}{bcolors.ENDC}"
    print("this does nothing")
    print(f"change that at line {line}")
    print("Exiting...")
    sys.exit()


def conf():
    """
    main function, what gets called when you call it from the command line
    """
    parser = get_parser()
    args = vars(parser.parse_args())
    if args['add-to-path']:
        add_to_path()
    if args['install']:
        if "list" in str(type(args['install'])):
            args['install'] = args['install'][0]
    if args['info']:
        get_info()
    if args['init']:
        setup_bare_repo()
    if args['git_interface']:
        git_cmd = git_interface_call(args['git_interface'])  # (out, err)
        print(git_cmd)
    if args['show_tracked_files']:
        print_tracked_files()
        sys.exit()
    if args['edit_file']:
        files = find_files(args['edit_file'][0])
        file_choice = option_picker(files)
        open_editor(file_choice)
        if args['apply_changes']:
            print("TODO")
    if args["dev_test"]:
        # Only here for testing new functions quickly
        _do_nothing()
    if args["clone_and_checkout"]:
        git_url = args["clone_and_checkout"][0]
        clone_repo(git_url)
        git_settings_change()
        checkout()


def checkout():
    """
    meta-function to safely stash old configs when restoring a config.
    """
    clashes = get_clashing_files()
    if clashes:
        backup_old_files(clashes)
        delete_files(clashes)
        get_clashing_files()


def add_to_path():
    """
    this function should add the path to this script to PATH.
    """
    print(f"Adding {HOME}/.local/bin to path")
    # shell_func_raw = f"{name}(){LCB}\n    python {SCRIPT_PATH} \"$@\"\n{RCB}\n"
    path_modification = f"path+={SCRIPT_PATH}"
    supported_shells = ['zsh', 'bash', 'csh', 'ksh']
    supported = False
    for shell in supported_shells:
        if shell in SHELL:
            supported = True
            rc_file = f"{HOME}/.{shell}rc"
            break
    if not supported:
        print("Shell not supported, defaulting to bash.\n")
        print("Or add the following to your shell's startup file manually:")
        print(path_modification)
        proceed = input(
            "Do you wish to append the above code to .bashrc? [y,N]: ")
        if proceed.lower() != 'y':
            print("Aborting...")
            sys.exit()
    print(f"Adding to {rc_file}")
    with open(rc_file, "a", ENCODING) as rc_file:
        rc_file.write(path_modification)
    print(DIVIDER)


def print_tracked_files():
    """
    prints all tracked files
    TODO add different behaviour for whole folders.
    """
    files = ls_tree()
    print(f"{len(files)} files tracked:\n")
    for file in files:
        print(file)
    print(DIVIDER)


def open_editor(file_path, editor=EDITOR, sleep_time=1) -> None:
    """
    open the given file with the system editor, unless specified otherwise
    sleep time can be passed as 0 for use with dmenu scripts for example.
    """
    print(f"editing {file_path} with {editor}")
    time.sleep(sleep_time)
    os.system(editor+" "+file_path)


def ls_tree(target='HEAD'):
    """
    get all the file paths (full path) in a nice format
    """
    cmd = ['ls-tree',
           '-r',
           '--full-name',
           '--full-tree',
           '--name-status',
           target]
    out = git_interface_call(cmd).split()
    files = [f'{HOME}/{relative_path}' for relative_path in out]
    return files


def find_files(partial_name):
    """
    finds all file paths contaning the given string
    helper for teh edit function
    """
    partial_name = partial_name.lower()
    tracked_files = ls_tree()
    found = {}
    index = 0
    for path in tracked_files:
        if partial_name in path:
            found[index] = path
            index += 1
    return found


def option_picker(opts: dict):
    """
    general option picker to be used when having multi option to edit.
    """
    if len(opts.keys()) == 1:
        print(f"1 result found: {opts[0]}")
        return opts[0]

    print("Multipile options found, which one to edit?")
    for key in opts.keys():
        print(f'{key} : {opts[key]}')
    print(DIVIDER)
    choice = input("Pick an option (default=0): ") or 0
    while int(choice) not in opts:
        print(f"Invalid choice ({choice}), please try again")
        choice = input("Pick an option (default=0): ")
        if choice == '':
            choice = 0
    return opts[int(choice)]


def get_info():
    """
    gather all repo info and return it in a nice format.
    """
    status = git_interface_call(['status'])
    branches = git_interface_call(['branch'])
    print(f"conf installed at {SCRIPT_PATH}\n")
    print_tracked_files()
    print(status)
    print(DIVIDER)
    print(f"Available Branches:\n{branches}")


def delete_files(files: list):
    """
    delete files, with the option of confirming one by one, or accept all.
    """
    print("Deleting files..")
    accepted_all = False
    for file in files:
        rm_command = ['rm', '-rfv', file]
        if not accepted_all:
            confirm = input(
                f'Are you sure you want to delete {file}? (y,N,a):')
            confirm = confirm.lower()
            if confirm == 'y':
                _sp_try_block(rm_command, "rm")
            elif confirm == 'a':
                accepted_all = True
                _sp_try_block(rm_command, "rm")
            else:
                print("Aborting...")
                sys.exit()
        else:
            _sp_try_block(rm_command, "rm")


def _sp_try_block(cmd, cmd_name):
    """
    helper function for the delete_files function, to clean up the try block
    for each subprocess call.
    in the future this is gonna be for all sp calls, thats why it's decoupled.
    """
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"{cmd_name} failed! printing exception and aborting...")
        print(exc)
        sys.exit()


def setup_bare_repo() -> str:
    """
    setup basic bare repo, only needs to be done once (unless you're redoing your repo).
    """
    init = ['/usr/bin/git', 'init', '--bare', REPO]
    print("Setting up...")
    if os.path.exists(REPO):
        delete_files([REPO])
    git_init = git_interface_call(init, use_prefix=False)
    git_settings_change()
    return git_init


def git_settings_change():
    """
    change the git seettings for the bare repo so that it doesnt
    show untracked files and add the repo itself to gitignore to avoid
    recursion-in-working-tree
        (since working tree includes the ,cfg folder itself).
    TODO fix up stout, stderr (standardize)
    """
    print("Changing git settings.")
    set_untracked = ['config', '--local', 'status.showUntrackedFiles', 'no']
    untracked = git_interface_call(set_untracked)
    try:
        with open(f'{REPO}.gitignore', "a", ENCODING) as gitignore:
            gitignore.write(".cfg\n")
    except Exception as exc:
        print("Couldn't add to gitignore... aborting")
        print(exc)
        return 0
    print(DIVIDER)
    return untracked


def git_interface_call(cmd, use_prefix=True):
    """
    Bread and butter of this program, whenever you need  to call git (every time)
    this handles it correctly.
    """
    git_bare_prefix = ['/usr/bin/git',
                       f'--git-dir={REPO}',
                       f'--work-tree={HOME}']
    cmd = git_bare_prefix + cmd if use_prefix else cmd
    out = subprocess.run(cmd, stdout=PIPE, stderr=subprocess.STDOUT).stdout
    return out.decode(ENCODING)


def clone_repo(url):
    """
    clones a repo given a remote URL.
    """
    print(f"Cloning {url}")
    clone_cmd = ['/usr/bin/git',
                 'clone',
                 '--bare',
                 url,
                 REPO]
    if os.path.exists(REPO):
        delete_files([REPO])
    output = git_interface_call(clone_cmd, use_prefix=False)
    print(DIVIDER)
    return output


def get_clashing_files():
    """
    Part of the toolchain to not destroy old configs,
    this function finds the clashes from the git error meessage.
    TODO makee it  more robust at detecting them, maybe using ls-tree
        insteead of the error message?
    """
    cmd = ['checkout']
    # Adjust these if it captures the files wrong, kinda hackey but
    # eh, for now there are more important features
    start_of_files_marker = "checkout:"
    end_of_files_marker = "Please"
    out = git_interface_call(cmd)
    output = out.split()
    if "error:" not in output:
        print(f"Checkout succesful\n{DIVIDER}")
        return None
    start_index = output.index(start_of_files_marker) + 1
    end_index = output.index(end_of_files_marker)
    files = output[start_index:end_index]
    files = [f"{HOME}/{filename}" for filename in files]
    return files


def backup_old_files(files: list):
    """

    Part of the toolchain to not destroy old configs,
    this uses the clashhes found before, and stashes them.
    """
    print("Backing up...\n")
    if not files:
        print(f"No Files to backup\n{DIVIDER}")
        return
    path = BACKUP_PATH
    try:
        os.mkdir(path)
    except OSError:
        print(f"folder already exists! \t \t \t {path}")
        path = f"{BACKUP_PATH}-{randint(1,99)}"
        print(f"Creating backup folder at \t \t {path}\n{DIVIDER}")
        os.mkdir(path)
    filenames = []
    for file in files:
        i = file.rfind('/') + 1
        filenames.append(file[i:])
    for src, dst in zip(files, filenames):
        dst = f"{path}/{dst}"
        copy(src, dst)
        print(f"Copied {src} \n\t to {dst} \n{DIVIDER}")


def main():
    """
    main
    """
    conf()


if __name__ == "__main__":
    main()
