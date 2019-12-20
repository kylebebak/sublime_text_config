import sublime
import sublime_plugin

import os


class ReactComponentCommand(sublime_plugin.WindowCommand):
    def run(self, stateless):
        file_name = self.window.active_view().file_name()
        if file_name is None:
            file_name = ''

        def choose_path(path):
            self._path = path
            self.window.show_input_panel('component name', '', choose_name, None, None)

        def choose_name(name):
            make_component(self._path, name, stateless)

        self.window.show_input_panel('component directory', file_name, choose_path, None, None)


def make_component(directory, name, stateless=True):
    path = os.path.join(directory, name)
    if not os.path.isabs(path):
        raise Exception('you must provide an absolute path')
    if os.path.exists(path):
        raise Exception('component already exists')

    os.makedirs(path)
    os.chdir(path)

    open('{}.tsx'.format(name), 'a').close()
    open('{}.module.scss'.format(name), 'a').close()
