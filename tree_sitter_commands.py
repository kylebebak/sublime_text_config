from __future__ import annotations

from pathlib import Path
from typing import List, Literal, Set, Tuple
from TreeSitter.src.api import get_ancestors

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

CaptureType = Tuple[Node, str, List[Node]]


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

    captured_nodes: Set[Node] = set()
    captures: list[CaptureType] = []

    for search_node in nodes:
        for captured_node, capture_name in query_node(tree_dict["scope"], search_node, query_file, queries_path) or []:
            captured_nodes.add(captured_node)
            captured_ancestors = [a for a in get_ancestors(captured_node)[1:] if a in captured_nodes]
            captures.append((captured_node, capture_name, captured_ancestors))

    return captures


def goto_captures(captures: list[CaptureType], view: sublime.View):
    options: list[sublime.QuickPanelItem] = []
    for node, capture_name, ancestors in captures:
        options.append(
            sublime.QuickPanelItem(
                trigger=node.text.decode(),
                kind=get_capture_kind(capture_name),
                annotation=ancestors[0].text.decode() if ancestors else "",
            )
        )

    def on_highlight(idx: int):
        """
        Scroll to symbol and select it.
        """
        node, _, _ = captures[idx]
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


class UserTreeSitterGotoQueryCommand(sublime_plugin.TextCommand):
    """
    Render goto options in current buffer from tree sitter query.
    """

    def run(self, edit):
        if not (tree_dict := get_tree_dict(self.view.buffer_id())):
            return

        nodes = get_selected_nodes(self.view) or [tree_dict["tree"].root_node]
        queries_path = "" if len(nodes) == 1 and nodes[0].parent is None else QUERIES_PATH

        def get_captures(nodes: list[Node]) -> list[CaptureType]:
            try:
                return get_captures_from_nodes(nodes, self.view, queries_path=queries_path)
            except FileNotFoundError:
                return []

        # If query returns no captures:
        #   - Against non-root node, move to root
        #   - Against root node, move to built-in goto text command

        if captures := get_captures(nodes):
            return goto_captures(captures, self.view)

        if len(nodes) > 1 or nodes[0].parent is not None:
            nodes = [tree_dict["tree"].root_node]
            if captures := get_captures(nodes):
                return goto_captures(captures, self.view)

        not_none(self.view.window()).run_command("show_overlay", {"overlay": "goto", "text": "@"})
