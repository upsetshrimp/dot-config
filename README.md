# dot config
# This is a WIP, somee things don't yet work
For a semi Working version, the dev branch is better.

A python wrapper to manage my git bare repository to manage all settings easily

inspired by this: https://www.atlassian.com/git/tutorials/dotfiles

# Installation
First, move to a folder where you wish this script to live.
```
mkdir ~/scripts
cd ~/scripts
```
Now, let's get the script installed on our system
This adds a function to your .bashrc / .zshrc file
so that it's possible to access from anywhere within the shell.
feel free to choose any name instead of _config_ after the --install argument.
That will be the command you call upon from your shell to invoke this tool.
```
wget https://gitlab.com/upsetshrimp/dot-config/-/raw/main/conf.py
python conf.py --install config

```
