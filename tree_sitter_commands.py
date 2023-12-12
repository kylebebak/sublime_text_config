from __future__ import annotations

import sublime
import sublime_plugin
from sublime_tree_sitter import (
    get_ancestors,
    get_captures_from_nodes,
    get_region_from_node,
    get_scope_to_language_name,
    get_selected_nodes,
    get_tree_dict,
    goto_captures,
)
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


class UserTreeSitterGotoQueryCommand(sublime_plugin.TextCommand):
    """
    Render goto options in current buffer from tree sitter query.

    If query returns no captures:

    - Against non-root node, move to root
    - Against root node, move to built-in goto text command
    """

    def fallback(self):
        not_none(self.view.window()).run_command("show_overlay", {"overlay": "goto", "text": "@"})

    def run(self, edit):
        if not (tree_dict := get_tree_dict(self.view.buffer_id())):
            return self.fallback()

        nodes = get_selected_nodes(self.view) or [tree_dict["tree"].root_node]
        is_root_node = len(nodes) == 1 and nodes[0].parent is None

        def get_captures(nodes: list[Node], queries_path: str):
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

        self.fallback()


class UserTreeSitterSelectAncestorCommand(sublime_plugin.TextCommand):
    """
    Expand selection to nearest ancestor of a given type. If no types configured for this language, fall back to
    `UserExpandSelectionCommand`.
    """

    ECMA_TYPES = ["function_declaration", "arrow_function", "method_definition", "class_declaration"]
    LANGUAGE_TO_ANCESTOR_TYPES: dict[str, list[str]] = {
        "python": ["class_definition", "function_definition"],
        "javascript": ECMA_TYPES,
        "typescript": ECMA_TYPES,
        "tsx": ECMA_TYPES,
    }

    def fallback(self):
        not_none(self.view.window()).run_command("show_overlay", {"overlay": "goto", "text": "@"})

    def run(self, edit):
        if not (tree_dict := get_tree_dict(self.view.buffer_id())):
            return self.fallback()

        language = get_scope_to_language_name()[tree_dict["scope"]]
        if not (ancestor_types := self.LANGUAGE_TO_ANCESTOR_TYPES.get(language)):
            return self.view.run_command("user_expand_selection_command")

        nodes = get_selected_nodes(self.view, include_emtpy_regions=True) or [tree_dict["tree"].root_node]

        sel = self.view.sel()
        for node in nodes:
            for ancestor in get_ancestors(node)[1:]:
                if ancestor.type in ancestor_types:
                    new_region = get_region_from_node(ancestor, self.view, reverse=True)
                    sel.add(new_region)
                    self.view.show(new_region)
                    break
