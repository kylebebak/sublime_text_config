import sublime
import sublime_plugin

import os


module = """import React from 'react'

import Styles from './{component}.module.scss'
"""


class ReactComponentCommand(sublime_plugin.WindowCommand):
    def run(self):
        file_name = self.window.active_view().file_name()
        if file_name is None:
            file_name = ''

        def choose_path(path):
            self._path = path
            self.window.show_input_panel('component name', '', choose_name, None, None)

        def choose_name(name):
            make_component(self._path, name)

        self.window.show_input_panel('component directory', file_name, choose_path, None, None)


def make_component(directory, name):
    path = os.path.join(directory, name)
    if not os.path.isabs(path):
        raise Exception('you must provide an absolute path')
    if os.path.exists(path):
        raise Exception('component already exists')

    os.makedirs(path)
    os.chdir(path)

    with open('{}.tsx'.format(name), 'w') as file:
        file.write(module.format(component=name))

    open('{}.module.scss'.format(name), 'a').close()
