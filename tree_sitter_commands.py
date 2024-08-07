from __future__ import annotations

import sublime
import sublime_plugin
from sublime_tree_sitter import (
    TreeDict,
    contains,
    format_breadcrumbs,
    get_ancestors,
    get_captures_from_nodes,
    get_node_spanning_region,
    get_query_s_from_file,
    get_region_from_node,
    get_scope_to_language_name,
    get_selected_nodes,
    get_size,
    get_tree_dict,
    goto_captures,
)
from tree_sitter import Node

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


class UserMergeSelectionsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if len(sel := self.view.sel()) == 0:
            return
        region = sublime.Region(a=sel[0].begin(), b=sel[-1].end())
        sel.clear()
        sel.add(region)


class UserReverseSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        sel = self.view.sel()
        for region in sel:
            sel.subtract(region)
            sel.add(sublime.Region(a=region.b, b=region.a))


class UserTreeSitterGotoSymbolCommand(sublime_plugin.TextCommand):
    """
    Render goto options for symbols in current buffer captured by tree sitter query.

    If query returns no captures:

    - Against non-root node, move to root
    - Against root node, move to built-in goto text command

    If `force_user_queries=True` passed, use queries from `QUERIES_PATH`, on root node, regardless of current selection.
    """

    def get_query_s(self, tree_dict: TreeDict):
        language = get_scope_to_language_name()[tree_dict["scope"]]
        return get_query_s_from_file(language, QUERIES_PATH)

    def run(self, edit, force_user_queries: bool = False):
        if tree_dict := get_tree_dict(self.view.buffer_id()):
            if tree_dict["scope"] == "text.html.markdown" and (window := self.view.window()):
                return window.run_command("show_overlay", {"overlay": "goto", "text": "@"})

        if force_user_queries:
            if not tree_dict:
                return
            nodes = [tree_dict["tree"].root_node]
            if captures := get_captures_from_nodes(nodes, self.view, self.get_query_s(tree_dict)):
                return goto_captures(captures, self.view)

        nodes = get_selected_nodes(self.view)
        if not nodes or (len(nodes) == 1 and nodes[0].parent is None):
            return self.view.run_command("tree_sitter_goto_symbol")

        if tree_dict:
            if captures := get_captures_from_nodes(nodes, self.view, self.get_query_s(tree_dict)):
                return goto_captures(captures, self.view)

        return self.view.run_command("tree_sitter_goto_symbol")


class UserTreeSitterSelectAncestorCommand(sublime_plugin.TextCommand):
    """
    Expand selection to nearest ancestor of a given type.

    TODO: this can be part of `TreeSitterShowBreadcrumbsCommand`.
    """

    ECMA_TYPES = ["function_declaration", "arrow_function", "method_definition", "class_declaration"]
    LANGUAGE_TO_ANCESTOR_TYPES: dict[str, list[str]] = {
        "python": ["class_definition", "function_definition"],
        "javascript": ECMA_TYPES,
        "typescript": ECMA_TYPES,
        "tsx": ECMA_TYPES,
    }

    def run(self, edit):
        if not (tree_dict := get_tree_dict(self.view.buffer_id())):
            return

        language = get_scope_to_language_name()[tree_dict["scope"]]
        if not (ancestor_types := self.LANGUAGE_TO_ANCESTOR_TYPES.get(language)):
            return

        nodes = get_selected_nodes(self.view, include_emtpy_regions=True) or [tree_dict["tree"].root_node]

        sel = self.view.sel()
        for node in nodes:
            for ancestor in get_ancestors(node)[1:]:
                if ancestor.type in ancestor_types:
                    new_region = get_region_from_node(ancestor, self.view, reverse=True)
                    sel.add(new_region)
                    self.view.show(new_region)
                    break


class TreeSitterShowBreadcrumbsCommand(sublime_plugin.TextCommand):
    """
    Render popup with ancestor breadcrumbs "above" selection in parse tree.
    """

    def run(self, edit):
        if not (sel := self.view.sel()):
            return
        if not (tree_dict := get_tree_dict(self.view.buffer_id())):
            return
        if not (node := get_node_spanning_region(sel[0], self.view.buffer_id())) or not node.parent:
            return

        ancestors = get_ancestors(node)
        if len(ancestors) < 2:
            return
        search_node = get_ancestors(node)[-2]

        try:
            query_s = get_query_s_from_file(get_scope_to_language_name()[tree_dict["scope"]])
        except FileNotFoundError:
            return
        captures = get_captures_from_nodes([search_node], self.view, query_s)

        bc_capture = None
        for capture in captures:
            if (bc := capture["breadcrumb"]) and contains(bc["container"], node):
                if bc_capture is None:
                    bc_capture = capture
                    continue
                if bc_capture["breadcrumb"] is None:
                    continue
                if get_size(bc["container"]) <= get_size(bc_capture["breadcrumb"]["container"]):
                    bc_capture = capture

        if bc_capture is None or bc_capture["breadcrumb"] is None:
            return

        bc_nodes: list[Node] = [bc_capture["breadcrumb"]["node"], *(c["node"] for c in bc_capture["breadcrumbs"])]
        self.view.show_popup(format_breadcrumbs(bc_nodes), max_width=1024)
