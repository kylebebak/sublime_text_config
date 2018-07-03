import sublime, sublime_plugin

import os


package = """{{
  "name": "{component}",
  "version": "0.0.0",
  "private": true,
  "main": "./{component}.js"
}}
"""

module = """import React from 'react'
import PropTypes from 'prop-types'

import Styles from './{component}.css'


class {component} extends React.Component {{
  constructor(props) {{
    super(props)
    this.state = {{
    }}
  }}

  render() {{
    return (
      null
    )
  }}
}}

{component}.propTypes = {{
}}

export default {component}
"""

module_stateless = """import React from 'react'
import PropTypes from 'prop-types'

import Styles from './{component}.css'


const {component} = ({{  }}) => {{
  return (
    null
  )
}}

{component}.propTypes = {{
}}

export default {component}
"""


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

    with open('package.json', 'w') as file:
        file.write(package.format(component=name))

    with open('{}.js'.format(name), 'w') as file:
        if stateless:
            file.write(module_stateless.format(component=name))
        else:
            file.write(module.format(component=name))

    open('{}.css'.format(name), 'a').close()
