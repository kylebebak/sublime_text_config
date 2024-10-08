"""
Adapted from: https://forum.sublimetext.com/t/run-multiple-commands-command/6848

Takes an array of commands (same as those you'd provide to a key binding) with an optional context (defaults to view)
and runs each command in order. Valid contexts are 'text', 'window', and 'app' for running a TextCommand, WindowCommand,
or ApplicationCommand respectively.
"""

from __future__ import annotations

import sublime
import sublime_plugin

from .utils import not_none


class RunMultipleCommandsCommand(sublime_plugin.TextCommand):
    def exec_command(self, command):
        if "command" not in command:
            raise Exception("No command name provided.")

        args = None
        if "args" in command:
            args = command["args"]

        # Default context is the view since it's easiest to get the other contexts from the view
        context = self.view
        if "context" in command:
            context_name = command["context"]
            if context_name == "window":
                context = not_none(context.window())
            elif context_name == "app":
                context = sublime
            elif context_name == "text":
                pass
            else:
                raise Exception('Invalid command context "' + context_name + '".')

        # Skip args if not needed
        if args is None:
            context.run_command(command["command"])
        else:
            context.run_command(command["command"], args)

    def run(self, edit, commands=None, repetitions=1):
        if commands is None:
            return  # Not an error
        for _ in range(repetitions):
            for command in commands:
                self.exec_command(command)
