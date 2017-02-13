import sublime, sublime_plugin
"""
Source:
https://forum.sublimetext.com/t/run-multiple-commands-command/6848

Takes an array of commands (same as those you'd provide to a key binding) with an
optional context (defaults to view) & runs each command in order. Valid contexts
are 'text', 'window', and 'app' for running a TextCommand, WindowCommands, or
ApplicationCommand respectively.
"""

class RunMultipleCommandsCommand(sublime_plugin.TextCommand):
    def exec_command(self, command):
        if not 'command' in command:
            raise Exception('No command name provided.')

        args = None
        if 'args' in command:
            args = command['args']

        # default context is the view since it's easiest to get the other contexts
        # from the view
        context = self.view
        if 'context' in command:
            context_name = command['context']
            if context_name == 'window':
                context = context.window()
            elif context_name == 'app':
                context = sublime
            elif context_name == 'text':
                pass
            else:
                raise Exception('Invalid command context "'+context_name+'".')

        # skip args if not needed
        if args is None:
            context.run_command(command['command'])
        else:
            context.run_command(command['command'], args)

    def run(self, edit, commands=None, repetitions=1):
        if commands is None:
            return # not an error
        for i in range(repetitions):
            for command in commands:
                self.exec_command(command)
