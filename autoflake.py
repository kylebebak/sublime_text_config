import sublime_plugin

import subprocess


class AutoflakeRemoveUnusedImportsCommand(sublime_plugin.TextCommand):

    def run(self, edit, **kwargs):
        subprocess.check_call([
            '/usr/local/bin/autoflake', '--in-place', '--remove-all-unused-imports', self.view.file_name(),
        ])
