import sublime_plugin

from urllib.parse import unquote


class UnescapeUrlCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        view = self.view
        for region in self.view.sel():
            if not region.empty():
                s = view.substr(region)
                view.replace(edit, region, unquote(s))
