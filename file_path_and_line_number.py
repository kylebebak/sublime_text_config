try:
    from typing import Any, Optional, List, NamedTuple, cast
except Exception:
    NamedTuple = lambda name, values: ''  # type: ignore # noqa
    cast = lambda t, val: val  # noqa

import sublime  # type: ignore
import sublime_plugin  # type: ignore

from collections import namedtuple
import os


BookmarkType = NamedTuple('Point', [('row', int), ('col', int), ('text', str)])
Bookmark = namedtuple('Bookmark', ['row', 'col', 'text'])


def truncate(s: str, n: int) -> str:
    if len(s) > n:
        return '{}…'.format(s[:n])
    return s


def format_bookmark(path, b, include_text):
    # type: (str, BookmarkType, bool) -> str
    if include_text:
        return '{}:{}:{}    {}'.format(path, str(b.row + 1), str(b.col + 1), b.text)
    return '{}:{}:{}'.format(path, str(b.row + 1), str(b.col + 1))


class CopyFilePathAndLineNumberCommand(sublime_plugin.TextCommand):

    def run(self, edit, strip: bool = True, max_len: int = 50, include_text: bool = False) -> None:
        path = self.view.file_name()  # type: Optional[str]
        if not path:
            return
        project_path = self.project_path()
        if project_path:
            path = os.path.relpath(path, project_path)

        bookmarks = []  # type: List[BookmarkType]
        for r in self.view.sel():
            bookmarks.append(self.get_line_number_and_text(r.begin(), strip, max_len))
        text = '\n'.join(format_bookmark(path, b, include_text) for b in bookmarks)
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
        # type: (Any, int, bool, int) -> BookmarkType
        row, col = self.view.rowcol(point)
        line = self.view.substr(self.view.line(point))  # type: str
        if strip:
            line = line.strip()
        return cast(BookmarkType, Bookmark(row, col, truncate(line, max_len)))
