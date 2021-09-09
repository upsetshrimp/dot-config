#!/usr/bin/env bash
###############################################################################
#                      V0.01, meant to install dot-config                                                                       #
###############################################################################

# TODO
# FIX BROKEN LOGIC, url is written as if it's for the dotfiles repo
# but it should be for  the dot config
# minor fix - just set a static url, and change argparse logic EZZ
set -eo pipefail

default_repo_dir=~/scripts/dot-config/
default_bin_dir=~/.local/bin/

repo_dir=""
bin_dir=""
branch="main"
url="https://raw.githubusercontent.com/upsetshrimp/dot-config/${branch}/bootstrap.sh"

clone_repo(){
    if [ -z "$1" ]; then
        echo "no repo url provided, skipping clone step"
        echo "Use the config tool to initialize your repo.."
        return 0
    fi
    if [ -z "$2" ]; then
        echo "no repo dir supplied, defaulting to $default_repo_dir"
        echo "If you see thhis error, there's a problem in the code"
    else
        repo_dir="$2"
    fi
    echo "Cloning repo into $repo_dir"
    git clone "$1" "$2" && return 0
}

symlink_bin(){
    if [ -z "$1" ]; then
        echo "No alternate bin path provided, defaulting to $default_bin_dir"
        echo "If you see thhis error, there's a problem in the code"
    else
        bin_dir="$1"
    fi
    echo "Creating symlink to bin folder: ${bin_dir}"
    ln -s ${repo_dir}/config.py ${bin_dir}/config && return 0
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
        echo -n "No directory arguments passed, use default arguments? [Y/n]: " && read use_default
        #printf "%b\n" "${default_repo_dir}" "${defailt_bin_dir}"
        if [[ "$use_default" == "y" ]] || [ -z "$use_default" ]; then
            echo "Using defaults"
            set_dirs
        else
            echo "Aborting..."
            exit 1
        fi

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
