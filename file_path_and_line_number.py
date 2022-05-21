from __future__ import annotations

from typing import NamedTuple, cast

import sublime  # type: ignore
import sublime_plugin  # type: ignore

from collections import namedtuple
import os


BookmarkType = NamedTuple("Point", [("row", int), ("col", int), ("text", str)])
Bookmark = namedtuple("Bookmark", ["row", "col", "text"])


def truncate(s: str, n: int) -> str:
    if len(s) > n:
        return "{}…".format(s[:n])
    return s


def format_bookmark(path: str, b: BookmarkType, include_text: bool) -> str:
    if include_text:
        return "{}:{}:{}    {}".format(path, str(b.row + 1), str(b.col + 1), b.text)
    return "{}:{}:{}".format(path, str(b.row + 1), str(b.col + 1))


class CopyFilePathAndLineNumberCommand(sublime_plugin.TextCommand):
    def run(
        self, edit, strip: bool = True, max_len: int = 50, include_text: bool = False
    ) -> None:
        path: str | None = self.view.file_name()
        if not path:
            return
        project_path = self.project_path()
        if project_path:
            path = os.path.relpath(path, project_path)

        bookmarks: list[BookmarkType] = []
        for r in self.view.sel():
            bookmarks.append(self.get_line_number_and_text(r.begin(), strip, max_len))
        text = "\n".join(format_bookmark(path, b, include_text) for b in bookmarks)
        sublime.set_clipboard(text)
        self.view.window().status_message("copied - {}".format(truncate(text, 80)))

    def project_path(self) -> str | None:
        project = self.view.window().project_data()
        if project is None:
            return None
        try:
            return os.path.expanduser(project["folders"][0]["path"])
        except Exception:
            return None

    def get_line_number_and_text(
        self, point: int, strip: bool, max_len: int
    ) -> BookmarkType:
        row, col = self.view.rowcol(point)
        line: str = self.view.substr(self.view.line(point))
        if strip:
            line = line.strip()
        return cast(BookmarkType, Bookmark(row, col, truncate(line, max_len)))
