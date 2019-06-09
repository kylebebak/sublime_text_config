import sublime
import sublime_plugin


class DisableWordCompletions(sublime_plugin.EventListener):
    """Disables word completions for all files, except those in `excluded_scopes`.
    """
    def on_query_completions(self, view, prefix, locations):
        excluded_scopes = ["markdown"]
        for scope in excluded_scopes:
            if scope in view.scope_name(locations[0]):
                return []
        return ([], sublime.INHIBIT_WORD_COMPLETIONS)
