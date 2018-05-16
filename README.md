## Sublime Text 3 Configuration

This repo contains the useful (mostly non-generated) files in the `~/Library/Application\ Support/Sublime\ Text\ 3/Packages/User/` directory. Check [.gitignore](.gitignore) to see which files belong in version control.

__Sublime Text__ is a highly extensible, amazing text editor. Check [Package Control.sublime-settings](Package%20Control.sublime-settings) to see which packages I've installed.

The bread and butter config files are [Preferences.sublime-settings](Preferences.sublime-settings) and [Default (OSX).sublime-keymap](Default%20(OSX).sublime-keymap).

For chaining commands, I use [run_multiple_commands.py](run_multiple_commands.py), which I found on the Sublime Text forums. This module allows you to enable some fancy keyboard shortcuts. I'm particularly fond of using `alt + up/down` to move the cursor up or down 5 lines at at a time.


### Miscellaneous

If you're using OSX, run this in the shell to enable key repeat for Sublime Text 3.
```sh
defaults write com.sublimetext.3 ApplePressAndHoldEnabled -bool false
```
