from __future__ import annotations

import os

import sublime
import sublime_plugin
from sublime_tree_sitter import (
    get_larger_region,
    get_node_spanning_region,
    get_region_from_node,
    get_tree_dict,
    has_tree,
    query_tree,
    walk_tree,
)
from tree_sitter import Node


def get_view_name(view: sublime.View):
    if name := view.file_name():
        return os.path.basename(name)

    return view.name() or ""


class TreeSitterPrintTreeCommand(sublime_plugin.TextCommand):
    def format_node(self, node: Node):
        return f"{node.type}  {node.start_point} → {node.end_point}"

    def run(self, edit):
        indent = " " * 2
        tree_dict = get_tree_dict(self.view.buffer_id())
        if not tree_dict:
            return

        window = self.view.window()
        if not window:
            return

        nodes: list[str] = []
        for node, depth in walk_tree(tree_dict["tree"].root_node):
            nodes.append(f"{indent * depth}{self.format_node(node)}")

        name = get_view_name(self.view)
        view = window.new_file()
        view.set_name(f"Syntax Tree - {name}" if name else "Syntax Tree")
        view.set_scratch(True)
        view.insert(edit, 0, "\n".join(nodes))


class UserExpandSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if has_tree(self.view.buffer_id()):
            self.view.run_command("tree_sitter_expand_selection")
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


class TreeSitterExpandSelectionCommand(sublime_plugin.TextCommand):
    """
    Note: we scroll to start of larger node if it's not visible.
    """

    def run(self, edit):
        for region in self.view.sel():
            new_region = get_larger_region(region, self.view)
            if new_region:
                self.view.sel().add(new_region)

                new_begin = new_region.begin()
                visible_region = self.view.visible_region()
                if new_region.begin() not in visible_region:
                    self.view.show(new_begin)


class TreeSitterSelectSiblingCommand(sublime_plugin.TextCommand):
    def run(self, edit, to_next: bool = True):
        sel = self.view.sel()
        for region in sel:
            node = get_node_spanning_region(region, self.view.buffer_id())
            print(node)
            if not node or not node.parent:
                return

            siblings = node.parent.children
            while node.parent:
                siblings = node.parent.children
                if len(siblings) == 1:
                    node = node.parent
                else:
                    break

            idx = siblings.index(node)
            idx = idx + 1 if to_next else idx - 1
            sibling = siblings[idx % len(siblings)]

            new_region = get_region_from_node(sibling, self.view)
            self.view.sel().subtract(region)
            self.view.sel().add(new_region)

            new_begin = new_region.begin()
            visible_region = self.view.visible_region()
            if new_region.begin() not in visible_region:
                self.view.show(new_begin)


class TreeSitterSelectAdjacentCommand(sublime_plugin.TextCommand):
    def run(self, edit, to_next: bool = True):
        pass


class TreeSitterSelectChooseDescendantsCommand(sublime_plugin.TextCommand):
    """
    TODO

    - Selecting all text should let us get root node, might require change to `get_node_spanning_region`
    - Specify query_name to look up query and use it
    - Create query for variable declarations, classes and functions
    """

    def run(self, edit, query_name: str):
        buffer_id = self.view.buffer_id()
        tree_dict = get_tree_dict(buffer_id)
        if not tree_dict:
            return

        node = get_node_spanning_region(self.view.sel()[0], buffer_id)
        if not node:
            return
        nodes = query_tree(tree_dict["scope"], "", node) or []
        for node in nodes:
            print(node[0])
