import sublime, sublime_plugin

class ToggleColorSchemeCommand(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):

        preferences = sublime.load_settings('Preferences.sublime-settings')
        scheme = self.view.settings().get("color_scheme")

        try:
            schemes = kwargs.get("color_schemes")
            i = schemes.index(scheme)
            preferences.set(
                'color_scheme', schemes[ (i+1) % len(schemes) ])
        except ValueError:
            print("Your current color scheme doesn't match any of your args.")
        except Exception:
            print("Something went wrong.")
