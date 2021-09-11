#!/usr/bin/env python

"""
dot-config
Author
"""
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, REMAINDER
import subprocess
from subprocess import PIPE
import os
import sys
import time
from shutil import copy
from random import randint
import inspect
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
DIVIDER_CHAR = '='
DIVIDER = f"\n{bcolors.OKGREEN}{bcolors.BOLD}{42*DIVIDER_CHAR}{bcolors.ENDC}\n"
ENCODING = "utf-8"

Parser = ArgumentParser


def config() -> None:
    """
    main function, what gets called when you call it from the command line
    TODO make this return logging  info, and add a logger.
    """
    if git_mode():
        out = git_interface_call(sys.argv[1:])
        print(out)
        sys.exit()
    else:
        parser = get_parser()
        args = vars(parser.parse_args())
    # Order matters here! pay attention!!
    if args['init']:
        setup_bare_repo()
    if args["clone_and_checkout"]:
        git_url = args["clone_and_checkout"][0]
        print(clone_and_checkout(git_url))
    if args['add_to_path']:
        add_to_path(args['add_to_path'][0])
    # ========= DEV TEST CODE ================= #
    if args["dev_test"]:
        print(args)
        _do_nothing()
    # ========= END DEV TEST CODE ============= #
    if not repo_exists():
        error_exit("repository not found! clone or init one to get started")
    # All commands below here can only happen if the repo exists!

    if args['info']:
        print(get_info())
    if args['git_interface']:
        git_cmd = git_interface_call(args['git_interface'])  # (out, err)
        print(git_cmd)
    if args['show_tracked_files']:
        print(get_tracked_files())
        sys.exit()
    if args['edit_file']:
        files = find_files(args['edit_file'][0])
        file_choice = option_picker(files)
        open_editor(file_choice)
        if args['apply_changes']:
            print("TODO")


def git_mode() -> bool:
    """
    check if the first argumment is a git interface call
    and bypassing argparse if wee are
    it's hackey but hey it works
    """
    first_arg = sys.argv[1]
    if first_arg[0] == '-':
        return False
    return True


def find_variants() -> None:
    """
    comb through monolith dotfile and find optional bits
    optional bits will be comments that will later be uncommented per request
    """
    print("TODO")


def create_branch(changes: dict) -> None:
    """
    input: selections of what to merge from files
    output: branch named HOSTNAME with the changes on file
    """
    print("TODO", changes)


def restore_backup(url) -> None:
    """
    input: url containing an old dot-config bare repo
    result: the repo being reinstated in the curreent machine
    TODO make it verify all system changes like PATH and such.
    """
    clone_repo(url)


def get_parser() -> Parser:
    """
    the default parser for this program, contains all the relevent  arguments
    and parameters.
    """
    parser = ArgumentParser(
        description="""
        Manage dotfiles with a git bare repo and the help of this simple tool.
        """,
        formatter_class=ArgumentDefaultsHelpFormatter,)
    parser.add_argument('--info', '-i', action="store_true")
    # Capture everything after to pass to the git command
    parser.add_argument('--git-interface', '-g', nargs=REMAINDER)
    parser.add_argument('--init', action="store_true")
    parser.add_argument('--show-tracked-files', '-f', action="store_true")
    parser.add_argument('--edit-file', '-e', nargs=REMAINDER)
    parser.add_argument('--apply-changes', '-a', action='store_true')
    parser.add_argument('--add-to-path', nargs=1)
    parser.add_argument('--clone-and-checkout', '-c', nargs=1)
    parser.add_argument('--dev-test', action="store_true")
    return parser


def _do_nothing() -> None:
    """
    Does nothing
    """
    frame = inspect.stack()[1][0]
    info = inspect.getframeinfo(frame)
    line = str(info.lineno)
    line = f"{bcolors.FAIL}{bcolors.BOLD}{line}{bcolors.ENDC}"
    print("this does nothing")
    print(f"change that at line {line}")
    print("Exiting...")
    sys.exit()


def repo_exists():
    """
    checks if repo at .cfg exists
    """
    cmd = ['status']
    out = git_interface_call(cmd)
    if 'not a git repository' in out:
        return False
    return True


def clone_and_checkout(url: str) -> str:
    """
    meta-function to safely stash old configs when restoring a config.
    """
    clashes = get_clashing_files()
    if clashes:
        backup_old_files(clashes)
        delete_files(clashes)
        clashes = get_clashing_files()
        if clashes:
            error_exit("Couldn't fix clashing files!")
    out = clone_repo(url)
    out += git_interface_call(['checkout'])
    return out


def add_to_path(bin_path: str) -> None:
    """
    this function should add the path to this script to PATH.
    """
    print(f"Adding {HOME}/.local/bin to path")
    path_modification = f"path+={bin_path}"
    supported_shells = ['zsh', 'bash', 'csh', 'ksh']
    supported = False
    for shell in supported_shells:
        if shell in SHELL:
            supported = True
            rc_path = f"{HOME}/.{shell}rc"
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
    print(f"Adding to {rc_path}")
    with open(rc_path, "a") as rc_file:
        rc_file.write(path_modification)
    print(DIVIDER)


def get_tracked_files() -> str:
    """
    prints all tracked files
    TODO add different behaviour for whole folders.
    """
    files = ls_tree()
    if not files:
        return "No tracked files...  add some!"
    files = color_filenames(files)
    formatted_out = DIVIDER + '\n'
    formatted_out += f"{len(files)} files tracked:\n"
    formatted_out += '\n'.join(files)
    formatted_out += DIVIDER
    return formatted_out


def color_filenames(files: list) -> list['str']:
    """
    input: list of filepaths
    output: same but filenames are highlighted
    for comfort
    """
    colorized_paths = []
    for path in files:
        index = path.rfind('/')
        filename = path[index+1:]
        path = f"{path[:index+1]}{bcolors.OKBLUE}{bcolors.BOLD}"
        path += f"{filename}{bcolors.ENDC}"
        colorized_paths.append(path)
    return colorized_paths


def open_editor(file_path, editor=EDITOR, sleep_time=1) -> None:
    """
    open the given file with the system editor, unless specified otherwise
    sleep time can be passed as 0 for use with dmenu scripts for example.
    """
    print(f"editing {file_path} with {editor}")
    time.sleep(sleep_time)
    os.system(editor+" "+file_path)


def ls_tree(target='HEAD') -> list:
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
    for line in out:
        if 'error' in line.lower():
            return []
    files = [f'{HOME}/{relative_path}' for relative_path in out]
    if not files:
        return ['No tracked files.. add some!']
    return files


def find_files(partial_name) -> dict:
    """
    finds all file paths contaning the given string
    helper for the edit function
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


def option_picker(opts: dict) -> str:
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


def get_info() -> str:
    """
    gather all repo info and return it in a nice format.
    """
    status = replace_git_in_str(git_interface_call(['status']))
    branches = git_interface_call(['branch'])
    info = f"dot-config installed at {SCRIPT_PATH}\n"
    info += get_tracked_files() + '\n'
    info += status
    info += DIVIDER + '\n'
    info += f"Available Branches:\n{branches}"
    return info


def delete_files(files: list) -> str:
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
                out = _sp_try_block(rm_command, "rm")
            elif confirm == 'a':
                accepted_all = True
                out = _sp_try_block(rm_command, "rm")
            else:
                error_exit("Aborted by user")
        else:
            out = _sp_try_block(rm_command, "rm")
    return out


def _sp_try_block(cmd: list, cmd_name: str) -> str:
    """
    helper function for the delete_files function, to clean up the try block
    for each subprocess call.
    in the future this is gonna be for all sp calls, thats why it's decoupled.
    """
    try:
        out = subprocess.run(cmd,
                             check=True,
                             stdout=PIPE,
                             stderr=subprocess.STDOUT)
        return out.stdout.decode(ENCODING)
    except subprocess.CalledProcessError as exc:
        print(f"{cmd_name} \n\t failed! printing exception and aborting...")
        print(exc)
        sys.exit()


def setup_bare_repo() -> str:
    """
    setup basic bare repo, only needs to be done once
    (unless you're re-doing your repo).
    """
    init = ['/usr/bin/git', 'init', '--bare', REPO]
    print("Setting up...")
    if os.path.exists(REPO):
        delete_files([REPO])
    out = git_interface_call(init, use_prefix=False) + '\n'
    out += DIVIDER
    git_global_config()
    return out


def git_global_config() -> str:
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
    gitignore_populated = False
    try:
        with open(f'{REPO}.gitignore', "a+") as gitignore:
            # print(f'Opening \t {REPO}.gitignore')
            gitignore.seek(0)
            lines = gitignore.readlines()
            for line in lines:
                if '.cfg/' in line:
                    gitignore_populated = True

            if not gitignore_populated:
                gitignore.write('.cfg/')
                print("written to .gitignore")
            else:
                print("gitignore populated, skipping...")
    except Exception as exc:
        error_exit(f"writing to .gitignore\n{exc}")
    print(DIVIDER)
    return untracked


def git_interface_call(cmd: list, use_prefix=True) -> str:
    """
    Bread and butter of this program, whenever you need
    to call git (every time)
    this handles it correctly.
    """
    git_bare_prefix = ['/usr/bin/git',
                       f'--git-dir={REPO}',
                       f'--work-tree={HOME}']
    cmd = git_bare_prefix + cmd if use_prefix else cmd
    out = _sp_try_block(cmd, ' '.join(cmd))
    return out


def clone_repo(url: str) -> str:
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
    return output


def get_clashing_files() -> list['str']:
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
        return []
    start_index = output.index(start_of_files_marker) + 1
    end_index = output.index(end_of_files_marker)
    files = output[start_index:end_index]
    files = [f"{HOME}/{filename}" for filename in files]
    return files


def backup_old_files(files: list) -> None:
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


def replace_git_in_str(text: str) -> str:
    """
    so the suggested commmands  make sense
    """
    return text.replace('git', 'config')


def error_exit(error: str) -> None:
    """
    in case something jsut goes wrong.
    this is still not proffesional software lol
    """
    print(f"{bcolors.FAIL}{bcolors.BOLD}{error}\n")
    print(f"Aborting...{bcolors.ENDC}")
    sys.exit()
