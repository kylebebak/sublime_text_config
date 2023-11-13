from __future__ import annotations

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
                },  # type: ignore
            )


class UserReverseSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        sel = self.view.sel()
        for region in sel:
            sel.subtract(region)
            sel.add(sublime.Region(a=region.b, b=region.a))


class TreeSitterGotoQueryCommand(sublime_plugin.TextCommand):
    """
    Render goto options in current buffer from tree sitter query.
    """

    def run(self, edit):
        if not (tree_dict := get_tree_dict(self.view.buffer_id())):
            return

        nodes = get_selected_nodes(self.view) or [tree_dict["tree"].root_node]
        queries_path = "" if len(nodes) == 1 and nodes[0].parent is None else QUERIES_PATH

        options: list[str] = []
        captures: list[Node] = []
        for node in nodes:
            for n, s in query_node(tree_dict["scope"], "symbols.scm", node, queries_path) or []:
                captures.append(n)
                options.append(f"{n} {s}")

        def on_highlight(idx: int):
            node = captures[idx]
            a = self.view.text_point_utf8(*node.start_point)
            b = self.view.text_point_utf8(*node.end_point)

            scroll_to_region(sublime.Region(a, b), self.view)

        window = not_none(self.view.window())
        window.show_quick_panel(options, on_select=lambda x: None, on_highlight=on_highlight)
