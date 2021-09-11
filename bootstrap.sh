#!/usr/bin/env bash
###############################################################################
#                      V0.01, meant to install dot-config                                                                       #
###############################################################################

set -eo pipefail

default_repo_dir=~/scripts/dot-config/
default_bin_dir=~/.local/bin/

repo_dir=""
bin_dir=""
branch="main"
url="git@github.com:upsetshrimp/dot-config.git"

clone_repo(){
    if [ -z "$1" ]; then
        echo "no repo url provided, Aborting!"
        return 1
    fi
    echo "Cloning repo into $2"
    git clone "$1" "$2" && return 0
}

symlink_bin(){
    echo "Creating symlink to bin folder: ${bin_dir}"
    ln -s ${repo_dir}config.py ${bin_dir}config && return 0 || return 1
}

verify_dependencies(){
    echo "TODO"
}

set_dirs(){
    if [ -z "$1" ];then
        repo_dir="$default_repo_dir"
        # echo "repo_dir: ${repo_dir}"
    else
        repo_dir="$1"
    fi
    if [ -z "$2" ];then
        bin_dir="$default_bin_dir"
        # echo "bin_dir: ${bin_dir}"
    else
        bin_dir="$2"
    fi
}

parse_args(){
    # TODO make this not suck, but good 'nuf for v0.01
    if [ $# -eq 0 ]; then
        echo "No directory arguments passed, using defaults"
        set_dirs
    elif [ $# -ne 2 ]; then
        echo "Invalid number of arguments!"
        echo "Usage: "
        echo "bootstrap *repo_dir *bin_dir"
        exit 1
    else
        set_dirs "$1" "$2"
    fi
}
parse_args "$@"

clone_repo "$url" "$repo_dir"
symlink_bin "$bin_dir"
echo "Bootstrap succesful"
echo "Runing first config run to append path"
python "${bin_dir}config" --add-to-path "${bin_dir}" && exit 0
echo "Error adding to path, check manually" && exit 1
