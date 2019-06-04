try:
    from typing import Any, Tuple, Optional
except Exception:
    pass

import os
import threading
import subprocess

import sublime  # type: ignore
import sublime_plugin  # type: ignore


class MypyRevealTypeCommand(sublime_plugin.TextCommand):
    def run(self, edit) -> None:
        contents = self.view.substr(sublime.Region(0, self.view.size()))
        for r in self.view.sel():
            bounds = self.get_bounds(r)
            self.run_mypy(
                self.get_modified_contents(self.get_bounds(r), contents),
                self.view.rowcol(bounds[0])[0] + 1,
            )
            break

    def get_modified_contents(self, bounds, contents):
        # type: (Tuple[int, int], str) -> str
        start, end = bounds
        return "{}reveal_type({}){}".format(
            contents[0:start], contents[start:end], contents[end:]
        )

    def get_bounds(self, region):
        # type: (Any) -> Tuple[int, int]
        start = region.begin()  # type: int
        end = region.end()  # type: int

        if start != end:
            return start, end

        # nothing is selected, so expand selection to nearest delimiters
        view_size = self.view.size()  # type: int
        delimiters = list(" \t\n\r\"'`,{}=:")

        # move the selection back to the start of the url
        while start > 0:
            if self.view.substr(start - 1) in delimiters:
                break
            start -= 1

        # move end of selection forward to the end of the url
        while end < view_size:
            if self.view.substr(end) in delimiters:
                break
            end += 1
        return start, end

    def run_mypy(self, contents: str, line_number: int):
        """Runs on another thread to avoid blocking main thread.
        """

        def sp():
            p = subprocess.Popen(
                ["mypy", "-c", contents],
                cwd=self.project_path(),
                stdout=subprocess.PIPE,
            )
            out, err = p.communicate()
            for line in out.decode("utf-8").splitlines():
                search = "{}: error: Revealed type is ".format(line_number)
                if search in line:
                    print(line)
                    self.view.show_popup(
                        "<style>body {{ height: 100px }}</style><p>{}</p>".format(
                            line.split(search)[1]
                        ),
                        max_width=800,
                    )
                    break

        threading.Thread(target=sp).start()

    def project_path(self):
        # type: () -> Optional[str]
        project = self.view.window().project_data()
        if project is None:
            return None
        try:
            return os.path.expanduser(project["folders"][0]["path"])
        except Exception:
            return None