import sublime_plugin

import subprocess
from os import getenv


class AutoflakeCommand(sublime_plugin.TextCommand):

    autoflake_path = '{}/{}'.format(
        getenv('HOME'), '/.local/bin/autoflake'
    )

    def run(self, edit, **kwargs):
        subprocess.check_call([
            self.autoflake_path, '--in-place', '--remove-all-unused-imports', self.view.file_name()
        ])
