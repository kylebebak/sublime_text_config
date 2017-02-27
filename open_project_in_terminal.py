import sublime, sublime_plugin
import subprocess


class OpenProjectInTerminal(sublime_plugin.TextCommand):
    TERMINAL_APP = '/Applications/iTerm.app'

    def run(self, edit, **kwargs):
        subprocess.check_call([ 'open', '-a', self.TERMINAL_APP, self.get_project_root() ])

    def get_project_root(self):
        project = self.view.window().project_data()
        if project is not None:
          try:
            return project['folders'][0]['path']
          except (KeyError, IndexError):
            return None
        else:
          return None
