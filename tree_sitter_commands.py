from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Literal, Tuple

import sublime
import sublime_plugin
from sublime_tree_sitter import get_ancestors, get_selected_nodes, get_tree_dict, query_node, scroll_to_region
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


CaptureNameType = Literal["definition.type", "definition.var", "definition.function"]

CAPTURE_NAME_TO_KIND: dict[CaptureNameType, sublime.Kind] = {
    "definition.type": (sublime.KindId.TYPE, "c", "c"),
    "definition.var": (sublime.KindId.VARIABLE, "v", "v"),
    "definition.function": (sublime.KindId.FUNCTION, "f", "f"),
}

CaptureType = Tuple[Node, str, List[Node]]


def parse_capture_name(capture_name: str) -> Tuple[str, int | None]:
    """
    Parse capture name and optionally captured node depth, compared with "container" depth, for rendering breadcrumbs.
    """
    parts = capture_name.split(".depth.", 1)
    return (parts[0], int(parts[1])) if len(parts) == 2 else (parts[0], None)


def get_captures_from_nodes(
    nodes: list[Node],
    view: sublime.View,
    query_file: str = "symbols.scm",
    queries_path: str | Path = "",
) -> List[CaptureType]:
    """
    Get capture tuples from search nodes. Capture tuples include captured ancestors for rendering breadcrumbs.

    Raises:
        `FileNotFoundError` if query file doesn't exist
    """
    if not (tree_dict := get_tree_dict(view.buffer_id())):
        return []

    container_id_to_captured_node: Dict[int, Node] = {}
    captures: list[CaptureType] = []

    for search_node in nodes:
        for captured_node, capture_name in query_node(tree_dict["scope"], search_node, query_file, queries_path) or []:
            _, depth = parse_capture_name(capture_name)

            container = captured_node
            if depth is not None:
                for _ in range(depth):
                    container = not_none(container.parent)
                container_id_to_captured_node[container.id] = captured_node

            # Exclude search_node from ancestors, user already knows they're searching this node
            captured_ancestors = [
                container_id_to_captured_node[a.id]
                for a in get_ancestors(container)[1:]
                if a.id in container_id_to_captured_node and a.id != search_node.id
            ]
            captures.append((captured_node, capture_name, captured_ancestors))

    return captures


def get_capture_kind(name: str) -> sublime.Kind:
    """
    For rendering `QuickPanelItem`s.
    """
    name, _ = parse_capture_name(name)
    if name not in CAPTURE_NAME_TO_KIND:
        return (sublime.KindId.AMBIGUOUS, "?", "?")

    return CAPTURE_NAME_TO_KIND[name]


def on_highlight_repaint_view(view: sublime.View):
    """
    Works around ST quick panel rendering bug. Modifying selection in `on_highlight` callback has no effect unless
    viewport moves.

    TODO: implementation doesn't work if entire buffer fits in viewport, because we can't scroll to force repaint.
    """
    DY = 2

    x, y = view.viewport_position()
    if y == 0:
        view.set_viewport_position((x, DY))
        view.set_viewport_position((x, 0))
    else:
        view.set_viewport_position((x, y - DY))
        view.set_viewport_position((x, y))


def goto_captures(captures: list[CaptureType], view: sublime.View):
    """
    Render goto options in quick panel in `view`, from list of `captures`. See also `get_captures_from_nodes`.
    """

    def format_node_text(text: str):
        if " " not in text:
            return text
        return " ".join(text.split())

    def format_breadcrumbs(ancestors: list[Node]):
        return " ➔ ".join(format_node_text(a.text.decode()) for a in reversed(ancestors))

    indent = " " * 4
    options: list[sublime.QuickPanelItem] = []
    for node, capture_name, ancestors in captures:
        options.append(
            sublime.QuickPanelItem(
                trigger=f"{indent * len(ancestors)}{format_node_text(node.text.decode())}",
                kind=get_capture_kind(capture_name),
                annotation=format_breadcrumbs(ancestors),
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

    # Find capture nearest to first selected region, and open quick panel at this index
    selected_index = -1
    if regions:
        row, _ = view.rowcol(regions[0].begin())
        for idx, (node, _, _) in enumerate(captures):
            if row >= node.start_point[0]:
                selected_index = idx

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
    window.show_quick_panel(options, on_select=on_select, on_highlight=on_highlight, selected_index=selected_index)


class UserTreeSitterGotoQueryCommand(sublime_plugin.TextCommand):
    """
    Render goto options in current buffer from tree sitter query.

    If query returns no captures:

    - Against non-root node, move to root
    - Against root node, move to built-in goto text command
    """

    def run(self, edit):
        if not (tree_dict := get_tree_dict(self.view.buffer_id())):
            return

        nodes = get_selected_nodes(self.view) or [tree_dict["tree"].root_node]
        is_root_node = len(nodes) == 1 and nodes[0].parent is None

        def get_captures(nodes: list[Node], queries_path: str) -> list[CaptureType]:
            try:
                return get_captures_from_nodes(nodes, self.view, queries_path=queries_path)
            except FileNotFoundError:
                return []

        if captures := get_captures(nodes, "" if is_root_node else QUERIES_PATH):
            return goto_captures(captures, self.view)

        if not is_root_node:
            nodes = [tree_dict["tree"].root_node]
            if captures := get_captures(nodes, ""):
                return goto_captures(captures, self.view)

        not_none(self.view.window()).run_command("show_overlay", {"overlay": "goto", "text": "@"})
