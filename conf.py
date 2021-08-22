import argparse
import subprocess
import os
import time
from subprocess import PIPE
from shutil import copy
from random import randint
"""
TODO:

*!*
clean up messy function roles, can probably get rid of a couple
 of functions (or make more)
"""
HOME = os.path.expanduser("~")
REPO = f'{HOME}/.cfg/'
EDITOR = os.environ['EDITOR']
SHELL = os.environ['SHELL']
SCRIPT_PATH = os.path.realpath(__file__)
BACKUP_PATH = f"{HOME}/old_dotfiles_backup"
lcb = '\u007b'              # {
rcb = '\u007d'              # }
divider = "----------------------------"


def get_parser():
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
    parser.add_argument('--install', nargs=1)
    parser.add_argument('--clone-and-checkout', '-c', nargs=1)
    parser.add_argument('--dev-test', action="store_true")
    return parser


def conf():
    parser = get_parser()
    args = vars(parser.parse_args())
    if args['install']:
        print("Here ", args['install'])
        if "list" in str(type(args['install'])):
            args['install'] = args['install'][0]
        add_to_path(args['install'])
    if args['info']:
        get_info()
    if args['init']:
        setup_bare_repo()
    if args['git_interface']:
        git_cmd = git_interface_call(args['git_interface'])  # (out, err)
        print(git_cmd)
    if args['show_tracked_files']:
        print_tracked_files()
        exit()
    if args['edit_file']:
        files = find_files(args['edit_file'][0])
        file_choice = option_picker(files)
        open_editor(file_choice)
        if args['apply_changes']:
            print("TODO")
    if args["dev_test"]:
        backup_old_files(get_clashing_files())
    if args["clone_and_checkout"]:
        git_url = args["clone_and_checkout"][0]
        clone_repo(git_url)
        git_settings_change()
        checkout()


def checkout():
    clashes = get_clashing_files()
    if clashes:
        backup_old_files(clashes)
        delete_files(clashes)
        get_clashing_files()


def add_to_path(name):
    print(f"Adding {name}() function to shell startup")
    shell_func_raw = f"{name}(){lcb}\n    python {SCRIPT_PATH} \"$@\"\n{rcb}\n"
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
        print(shell_func_raw)
        proceed = input(
            "Do you wish to append the above code to .bashrc? [y,N]: ")
        if proceed.lower() != 'y':
            print("Aborting...")
            exit()
    print(f"Adding to {rc_file}")
    f = open(rc_file, "a")
    f.write(shell_func_raw)
    f.close()
    print(divider)


def print_tracked_files():
    files = ls_tree()
    print(f"{len(files)} files tracked:\n")
    for file in files:
        print(file)
    print(divider)


def open_editor(file_path, editor=EDITOR) -> None:
    print(f"editing {file_path} with {editor}")
    time.sleep(1)
    os.system(editor+" "+file_path)


def ls_tree(target='HEAD'):
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
    if len(opts.keys()) == 1:
        print(f"1 result found: {opts[0]}")
        return opts[0]

    print("Multipile options found, which one to edit?")
    for key in opts.keys():
        print(f'{key} : {opts[key]}')
    print(divider)
    choice = input("Pick an option (default=0): ") or 0
    while int(choice) not in opts:
        print(f"Invalid choice ({choice}), please try again")
        choice = input("Pick an option (default=0): ")
        if choice == '':
            choice = 0
    return opts[int(choice)]


def get_info():
    status = git_interface_call(['status'])
    branches = git_interface_call(['branch'])
    print(f"conf installed at {SCRIPT_PATH}\n")
    print_tracked_files()
    print(status)
    print(divider)
    print(f"Available Branches:\n{branches}")


def delete_files(files: list):
    print("Deleting files..")
    accepted_all = False
    for file in files:
        rm = ['rm', '-rfv', file]
        if not accepted_all:
            confirm = input(
                f'Are you sure you want to delete {file}? (y,N,a):')
            confirm = confirm.lower()
            if confirm == 'y':
                subprocess.run(rm)
            elif confirm == 'a':
                accepted_all = True
                subprocess.run(rm)
            else:
                print("Aborting...")
                exit()
        else:
            subprocess.run(rm)


def setup_bare_repo() -> str:
    init = ['/usr/bin/git', 'init', '--bare', REPO]
    print("Setting up...")
    if len(os.listdir(REPO)) != 0:
        delete_files([REPO])
    git_init = git_interface_call(init, use_prefix=False)
    git_settings_change()
    return git_init.decode('utf-8')


def git_settings_change():
    print("Changing git settings.")
    set_untracked = ['config', '--local', 'status.showUntrackedFiles', 'no']
    untracked = git_interface_call(set_untracked)
    try:
        f = open(f'{REPO}.gitignore', "a")
        f.write(".cfg\n")
        f.close()
    except Exception as e:
        print("Couldn't add to gitignore... aborting")
        print(e)
        return
    print(divider)
    return untracked


def git_interface_call(cmd, use_prefix=True):
    git_bare_prefix = ['/usr/bin/git',
                       f'--git-dir={REPO}',
                       f'--work-tree={HOME}']
    cmd = git_bare_prefix + cmd if use_prefix else cmd
    out = subprocess.run(cmd, stdout=PIPE, stderr=subprocess.STDOUT).stdout
    return out.decode("utf-8")


def clone_repo(url):
    print(f"Cloning {url}")
    clone_cmd = ['/usr/bin/git',
                 'clone',
                 '--bare',
                 url,
                 REPO]
    if os.path.exists(REPO):
        delete_files([REPO])
    output = git_interface_call(clone_cmd, use_prefix=False)
    print(divider)
    return output


def get_clashing_files():
    cmd = ['checkout']
    # Adjust these if it captures the files wrong, kinda hackey but
    # eh, for now there are more important features
    start_of_files_marker = "checkout:"
    end_of_files_marker = "Please"
    out = git_interface_call(cmd)
    output = out.split()
    if "error:" not in output:
        print(f"Checkout succesful\n{divider}")
        return None
    start_index = output.index(start_of_files_marker) + 1
    end_index = output.index(end_of_files_marker)
    files = output[start_index:end_index]
    files = [f"{HOME}/{filename}" for filename in files]
    return files


def backup_old_files(files: list):
    print("Backing up...\n")
    if not files:
        print(f"No Files to backup\n{divider}")
        return
    path = BACKUP_PATH
    try:
        os.mkdir(path)
    except Exception:
        print(f"folder already exists! \t \t \t {path}")
        path = f"{BACKUP_PATH}-{randint(1,99)}"
        print(f"Creating backup folder at \t \t {path}\n{divider}")
        os.mkdir(path)
    filenames = []
    for file in files:
        i = file.rfind('/') + 1
        filenames.append(file[i:])
    for src, dst in zip(files, filenames):
        dst = f"{path}/{dst}"
        copy(src, dst)
        print(f"Copied {src} \n\t to {dst} \n{divider}")


def main():
    conf()


if __name__ == "__main__":
    main()
