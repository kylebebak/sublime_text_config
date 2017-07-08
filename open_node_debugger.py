import sublime_plugin

import webbrowser


class OpenNodeDebuggerCommand(sublime_plugin.WindowCommand):
    """Open requests quickstart in web browser.
    """
    def run(self):
        webbrowser.open_new_tab('about:inspect')
