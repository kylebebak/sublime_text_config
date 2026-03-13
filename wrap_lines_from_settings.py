import sublime_plugin


class WrapLinesFromSettingsCommand(sublime_plugin.TextCommand):
    """
    Wraps selected regions using a configurable width.

    Reads `wrap_lines_width` from the settings hierarchy (User, Syntax, Project, etc.), falling back to default if the
    setting is absent, and calls `wrap_lines` built-in with this width.

    https://docs.sublimetext.io/reference/commands.html
    """

    DEFAULT_WIDTH = 120

    def run(self, edit):
        width = self.view.settings().get("wrap_lines_width", self.DEFAULT_WIDTH)

        # Coerce to int defensively, in case the setting was stored as a string
        try:
            width = int(width)  # type: ignore
        except Exception:
            width = self.DEFAULT_WIDTH

        self.view.run_command("wrap_lines", {"width": width})
