import sublime
import sublime_plugin

from urllib.parse import quote, unquote
import re


def snake_to_camel_case(s):
    """https://stackoverflow.com/questions/19053707/converting-snake-case-to-lower-camel-case-lowercamelcase
    """
    components = s.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def camel_to_snake_case(s):
    """https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


functions = {
    'escape_url': quote,
    'unescape_url': unquote,
    'snake_to_camel_case': snake_to_camel_case,
    'camel_to_snake_case': camel_to_snake_case,
}


class TransformStringCommand(sublime_plugin.TextCommand):
    def run(self, edit, func=''):

        transform = functions.get(func)
        if not transform:
            sublime.error_message('Transform String Error: transform method {} does not exist'.format(func))
            return

        view = self.view
        for region in self.view.sel():
            if not region.empty():
                s = view.substr(region)
                view.replace(edit, region, transform(s))
