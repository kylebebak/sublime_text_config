# Sublime Text 4 Configuration

This repo contains the useful (mostly non-generated) files in the `~/Library/Application Support/Sublime Text/Packages/User/` directory. Check [.gitignore](.gitignore) to see which files go in version control.

**Sublime Text** is a highly extensible text editor. Check [Package Control.sublime-settings](Package%20Control.sublime-settings) to see which packages I've installed.

The bread and butter config files are [Preferences.sublime-settings](Preferences.sublime-settings) and [Default (OSX).sublime-keymap](<Default%20(OSX).sublime-keymap>).

For chaining commands, I use [run_multiple_commands.py](run_multiple_commands.py). This module allows you to enable some fancy keyboard shortcuts, e.g. using `alt + up/down` to move the cursor up or down 5 lines at a time.

## Setup

```sh
# Symlink this repo into .../Packages/User
rm -dr ~/Library/Application\ Support/Sublime\ Text/Packages/User
ln -s ~/Repos/sublime_text_config ~/Library/Application\ Support/Sublime\ Text/Packages/User

# Get a `subl` executable
sudo mkdir /usr/local/bin
sudo ln -s "/Applications/Sublime Text.app/Contents/SharedSupport/bin/subl" /usr/local/bin/subl
```

To install custom packages from git repos, do `cd ~/Library/Application\ Support/Sublime\ Text/Packages`, and `git clone ...` these packages.

## `PATH`

Modify paths in `~/.zprofile`, not in `~/.zshrc`, to make sure Sublime picks them up, e.g. for LSP.
