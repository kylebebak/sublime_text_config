# Sublime Text 3 Configuration

This repo contains the useful (mostly non-generated) files in the `~/Library/Application\ Support/Sublime\ Text/Packages/User/` directory. Check [.gitignore](.gitignore) to see which files belong in version control.

**Sublime Text** is a highly extensible, amazing text editor. Check [Package Control.sublime-settings](Package%20Control.sublime-settings) to see which packages I've installed.

The bread and butter config files are [Preferences.sublime-settings](Preferences.sublime-settings) and [Default (OSX).sublime-keymap](<Default%20(OSX).sublime-keymap>).

For chaining commands, I use [run_multiple_commands.py](run_multiple_commands.py), which I found on the Sublime Text forums. This module allows you to enable some fancy keyboard shortcuts. I'm particularly fond of using `alt + up/down` to move the cursor up or down 5 lines at at a time.

## `PATH`

Modify paths in `~/.zprofile`, not in `~/.zshrc`, to make sure Sublime picks them up, e.g. for LSP.

## `GitSavvy.sublime-settings`

Reproduced here because they have an API token and can't go in version control.

```json
{
    "api_tokens": {
        "github.com": "..."
    },
    "global_flags": {
        "commit": ["--cleanup=strip"]
    },
    "log_follow_rename": true,
    "blame_follow_rename": true,
}
```
