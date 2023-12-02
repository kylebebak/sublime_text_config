from __future__ import annotations

from pathlib import Path
from typing import Literal

import sublime
import sublime_plugin
from sublime_tree_sitter import get_selected_nodes, get_tree_dict, query_node, scroll_to_region
from tree_sitter import Node

from .utils import not_none

QUERIES_PATH = "~/Repos/sublime_text_config/queries"


class UserExpandSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if get_tree_dict(self.view.buffer_id()):
            self.view.run_command("tree_sitter_select_ancestor")
        else:
            # Fall back to using BracketHighlighter
            self.view.run_command(
                "bh_async_key",
                {
                    "no_outside_adj": None,
                    "lines": True,
                    "plugin": {"type": ["__all__"], "command": "bh_modules.bracketselect"},
                },
            )


class UserReverseSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        sel = self.view.sel()
        for region in sel:
            sel.subtract(region)
            sel.add(sublime.Region(a=region.b, b=region.a))


def on_highlight_repaint_view(view: sublime.View):
    """
    Works around ST quick panel rendering bug. Modifying selection in `on_highlight` callback has no effect unless
    viewport moves.
    """
    DY = 2

    x, y = view.viewport_position()
    if y == 0:
        view.set_viewport_position((x, DY))
        view.set_viewport_position((x, 0))
    else:
        view.set_viewport_position((x, y - DY))
        view.set_viewport_position((x, y))


CaptureNameType = Literal["definition.class", "definition.var", "definition.function"]

CAPTURE_NAME_TO_KIND: dict[CaptureNameType, sublime.Kind] = {
    "definition.class": (sublime.KindId.TYPE, "c", "c"),
    "definition.var": (sublime.KindId.VARIABLE, "v", "v"),
    "definition.function": (sublime.KindId.FUNCTION, "f", "f"),
}


def get_capture_kind(capture_name: str) -> sublime.Kind:
    if capture_name not in CAPTURE_NAME_TO_KIND:
        return (sublime.KindId.AMBIGUOUS, "?", "?")

    return CAPTURE_NAME_TO_KIND[capture_name]


def get_captures_from_nodes(
    nodes: list[Node],
    view: sublime.View,
    query_file: str = "symbols.scm",
    queries_path: str | Path = "",
):
    if not (tree_dict := get_tree_dict(view.buffer_id())):
        return []

    captures: list[tuple[Node, str]] = []
    for node in nodes:
        for n, c in query_node(tree_dict["scope"], node, query_file, queries_path) or []:
            captures.append((n, c))

    return captures


def goto_goto_captures(captures: list[tuple[Node, str]], view: sublime.View):
    options: list[sublime.QuickPanelItem] = []
    for node, capture_name in captures:
        options.append(
            sublime.QuickPanelItem(
                trigger=node.text.decode(),
                kind=get_capture_kind(capture_name),
                annotation="text",
            )
        )

    def on_highlight(idx: int):
        """
        Scroll to symbol and select it.
        """
        node, _ = captures[idx]
        a = view.text_point_utf8(*node.start_point)
        b = view.text_point_utf8(*node.end_point)
        region = sublime.Region(a, b)

        sel = view.sel()
        sel.clear()
        scroll_to_region(region, view)
        on_highlight_repaint_view(view)  # Works around ST quick panel `on_highlight` rendering bug
        sel.add(region)

    regions = [r for r in view.sel()]
    xy = view.viewport_position()

    def on_select(idx: int):
        """
        If user "cancels" selection, revert selection and viewport position to initial values.
        """
        if idx == -1:
            view.set_viewport_position(xy)
            sel = view.sel()
            sel.clear()
            sel.add_all(regions)

    window = not_none(view.window())
    window.show_quick_panel(options, on_select=on_select, on_highlight=on_highlight)


class CustomTreeSitterGotoQueryCommand(sublime_plugin.TextCommand):
    """
    Render goto options in current buffer from tree sitter query.
    """

    def run(self, edit):
        if not (tree_dict := get_tree_dict(self.view.buffer_id())):
            return

        nodes = get_selected_nodes(self.view) or [tree_dict["tree"].root_node]
        queries_path = "" if len(nodes) == 1 and nodes[0].parent is None else QUERIES_PATH

        captures = get_captures_from_nodes(nodes, self.view, queries_path=queries_path)
        goto_goto_captures(captures, self.view)
