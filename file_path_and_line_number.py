try:
    from typing import Any, Optional, List, Tuple
except Exception:
    pass

import sublime  # type: ignore
import sublime_plugin  # type: ignore

import os


def truncate(s: str, n: int) -> str:
    if len(s) > n:
        return '{}…'.format(s[:n])
    return s


class CopyFilePathAndLineNumberCommand(sublime_plugin.TextCommand):

    def run(self, edit, strip: bool = True, max_len: int = 50) -> None:
        path = self.view.file_name()  # type: Optional[str]
        if not path:
            return
        project_path = self.project_path()
        if project_path:
            path = os.path.relpath(path, project_path)

        lines = []  # type: List[Tuple[int, int, str]]
        for r in self.view.sel():
            lines.append(self.get_line_number_and_text(r.begin(), strip, max_len))
        text = '\n'.join('{}:{}:{}    {}'.format(path, str(line[0] + 1), str(line[1] + 1), line[2]) for line in lines)
        sublime.set_clipboard(text)
        self.view.window().status_message('copied - {}'.format(truncate(text, 80)))

    def project_path(self):
        # type: (Any) -> Optional[str]
        project = self.view.window().project_data()
        if project is None:
            return None
        try:
            return os.path.expanduser(project['folders'][0]['path'])
        except Exception:
            return None

    def get_line_number_and_text(self, point, strip, max_len):
        # type: (Any, int, bool, int) -> Tuple[int, int, str]
        row, col = self.view.rowcol(point)
        line = self.view.substr(self.view.line(point))  # type: str
        if strip:
            line = line.strip()
        return row, col, truncate(line, max_len)
