import sublime, sublime_plugin

class CycleColorSchemeCommand(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):

        preferences = sublime.load_settings('Preferences.sublime-settings')
        scheme = self.view.settings().get("color_scheme").split('/')[-1]

        try:
            scheme_directory = kwargs.get("scheme_directory")
            schemes = kwargs.get("color_schemes")
            i = schemes.index(scheme)
            new_scheme = schemes[ (i+1) % len(schemes) ]
            preferences.set('color_scheme', '{}/{}'.format(scheme_directory, new_scheme))
        except ValueError:
            print("Your current color scheme doesn't match any of your args.")
        except Exception:
            print("Something went wrong.")
