import sublime, sublime_plugin

def open_file(window, filename):
    window.open_file(filename, sublime.ENCODED_POSITION)

class OpenFileByNameCommand(sublime_plugin.WindowCommand):
    def run(self):
        fname = self.window.active_view().file_name()
        if fname == None:
            fname = ""

        def done(filename):
            open_file(self.window, filename)

        self.window.show_input_panel(
            "file to open: ", fname, done, None, None)
