## Sublime Text 3 Configuration

This repo contains the useful (mostly non-generated) files in the `~/Library/Application\ Support/Sublime\ Text\ 3/Packages/User/` directory. Check [.gitignore](.gitignore) to see which files I've deemed "useful".

**Sublime Text** is a highly extensible, amazing text editor. Check [Package Control.sublime-settings](Package%20Control.sublime-settings) to see which packages I've installed.

The bread and butter config files are [Preferences.sublime-settings](Preferences.sublime-settings) and [Default (OSX).sublime-keymap](Default%20(OSX).sublime-keymap). Both are JSON, with the added benefit of allowing comments, which is not part of the JSON spec.

For chaining commands, I use [run_multiple_commands.py](run_multiple_commands.py), which I found on the Sublime Text forums. This module allows you to enable some fancy keyboard shortcuts. I'm particularly fond of using `alt + up/down` to move the cursor up or down 5 lines at at a time =)

On OSX, all ST3 configuration is under `~/Library/Application\ Support/Sublime\ Text\ 3/`, which contains `Packages` and `Installed\ Packages`. Placing all of this config in a Git repo wouldn't make much sense, because some packages are big, and most of their files are auto-generated.

However, backing up this directory with Dropbox or Google Drive is nice, because by simply copying it over you get ST3 fully set up and running on a new machine.

### Miscellaneous

To enable key repeat for Sublime Text 3, e.g. so that navigation with Vintage mode isn't a pain in the ass.
```sh
defaults write com.sublimetext.3 ApplePressAndHoldEnabled -bool false
```
