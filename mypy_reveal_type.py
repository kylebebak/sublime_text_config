try:
    from typing import Any, Tuple, Optional, cast
except Exception:
    cast = lambda t, v: v

import os
import string
import logging
import threading
import subprocess

import sublime  # type: ignore
import sublime_plugin  # type: ignore


def log(s: str) -> None:
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("mypy_reveal_type: {}".format(s))


def parse_output(out: str, line_number: int) -> str:
    for line in out.splitlines():
        search = "{}: error: Revealed type is ".format(line_number)
        if search in line:
            log(line)
            return "<b>{}</b>".format(line.split(search)[1][1:-1])

    log(line)  # no revealed type found
    return line.split("{}: ".format(line_number))[1]


def parse_locals_output(out: str, line_number: int) -> str:
    lines = []
    for line in out.splitlines():
        search = "{}: error: ".format(line_number)
        if search in line and "Revealed local types are:" not in line:
            lines.append(line.split(search)[1])
    if len(lines) > 0:
        name_type_pairs = [line.split(": ") for line in lines]
        max_chars = max(len(pair[0]) for pair in name_type_pairs)
        lines = [
            "<b>{}</b> {}".format(
                pair[0].ljust(max_chars, "-").replace("-", "&nbsp;"), pair[1]
            )
            for pair in name_type_pairs
        ]
        return "<br>".join(lines)

    return "error"


class MypyRevealTypeCommand(sublime_plugin.TextCommand):
    def run(self, edit, locals=False) -> None:
        for r in self.view.sel():
            if locals:
                self.view.run_command("move_to", {"to": "eol"})
                self.view.run_command("insert", {"characters": "\nreveal_locals()"})
                contents = cast(
                    str, self.view.substr(sublime.Region(0, self.view.size()))
                )
                sublime.set_timeout_async(lambda: self.view.run_command("undo"), 0)
                self.run_mypy(
                    contents=contents,
                    line_number=self.view.rowcol(r.end())[0] + 2,
                    locals=True,
                )
            else:
                contents = cast(
                    str, self.view.substr(sublime.Region(0, self.view.size()))
                )
                bounds = self.get_bounds(r)
                self.run_mypy(
                    contents=self.get_modified_contents(self.get_bounds(r), contents),
                    line_number=self.view.rowcol(bounds[0])[0] + 1,
                    selection=contents[bounds[0] : bounds[1]],
                )
            break

    def show_popup(self, contents: str) -> None:
        self.view.show_popup(
            "<style>body {{ min-height: 100px }}</style><p>{}</p>".format(contents),
            max_width=800,
        )

    def get_modified_contents(self, bounds, contents):
        # type: (Tuple[int, int], str) -> str
        start, end = bounds
        return "{}reveal_type({}){}".format(
            contents[0:start], contents[start:end], contents[end:]
        )

    def get_modified_contents_locals(self, begin: int, contents: str) -> str:
        return contents

    def get_bounds(self, region):
        # type: (Any) -> Tuple[int, int]
        start = region.begin()  # type: int
        end = region.end()  # type: int

        if start != end:
            return start, end

        # nothing is selected, so expand selection
        view_size = self.view.size()  # type: int
        included = list("{}{}_".format(string.ascii_letters, string.digits))

        # move the selection back to the start of the url
        while start > 0:
            if cast(str, self.view.substr(start - 1)) not in included:
                break
            start -= 1

        # move end of selection forward to the end of the url
        while end < view_size:
            if cast(str, self.view.substr(end)) not in included:
                break
            end += 1
        return start, end

    def run_mypy(
        self, contents: str, line_number: int, selection: str = "", locals=False
    ) -> None:
        """Runs on another thread to avoid blocking main thread.
        """

        def sp() -> None:
            p = subprocess.Popen(
                ["mypy", "-c", contents],
                cwd=self.project_path(),
                stdout=subprocess.PIPE,
            )
            out, err = p.communicate()
            if locals:
                popup_contents = parse_locals_output(
                    out.decode("utf-8"), line_number
                )  # type: str
                self.show_popup(popup_contents)
            else:
                popup_contents = parse_output(out.decode("utf-8"), line_number)
                if selection:
                    popup_contents = '<p>"{}"</p><p>{}</p>'.format(
                        selection, popup_contents
                    )
                self.show_popup(popup_contents)

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
