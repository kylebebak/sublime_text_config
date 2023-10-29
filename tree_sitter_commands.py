from __future__ import annotations

import os
from typing import TypeVar

import sublime
import sublime_plugin
from sublime_tree_sitter import (
    get_larger_region,
    get_node_spanning_region,
    get_region_from_node,
    get_size,
    get_tree_dict,
    has_tree,
    query_tree,
    walk_tree,
)
from tree_sitter import Node

T = TypeVar("T")


def not_none(var: T | None) -> T:
    assert var is not None
    return var


def get_view_name(view: sublime.View):
    if name := view.file_name():
        return os.path.basename(name)

    return view.name() or ""


def scroll_to_point(point: int, view: sublime.View):
    visible_region = view.visible_region()
    if point not in visible_region:
        view.show(point)


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

        root_node = tree_dict["tree"].root_node
        if len(sel := self.view.sel()) > 0 and len(region := sel[0]) > 0:
            root_node = get_node_spanning_region(region, self.view.buffer_id()) or root_node

        nodes = [f"{indent * depth}{self.format_node(node)}" for node, depth in walk_tree(root_node)]

        name = get_view_name(self.view)
        view = window.new_file()
        view.set_name(f"Syntax Tree - {name}" if name else "Syntax Tree")
        view.set_scratch(True)
        view.insert(edit, 0, "\n".join(nodes))


class TreeSitterSelectAncestorCommand(sublime_plugin.TextCommand):
    """
    Note: we scroll to start of ancestor if it's not visible.
    """

    def run(self, edit):
        for region in self.view.sel():
            new_region = get_larger_region(region, self.view)
            if new_region:
                self.view.sel().add(new_region)
                scroll_to_point(new_region.begin(), self.view)


class TreeSitterSelectSiblingCommand(sublime_plugin.TextCommand):
    def run(self, edit, to_next: bool = True):
        sel = self.view.sel()
        for region in sel:
            node = get_node_spanning_region(region, self.view.buffer_id())
            if not node or not node.parent:
                self.view.run_command("tree_sitter_select_descendant")
                return

            while node.parent and node.parent.parent:
                if len(node.parent.children) == 1:
                    node = node.parent
                else:
                    break

            siblings = not_none(node.parent).children
            idx = siblings.index(node)
            idx = idx + 1 if to_next else idx - 1
            sibling = siblings[idx % len(siblings)]

            new_region = get_region_from_node(sibling, self.view)
            sel.subtract(region)
            sel.add(new_region)

            scroll_to_point(new_region.begin(), self.view)


class TreeSitterSelectDescendantCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        tree_dict = get_tree_dict(self.view.buffer_id())
        if not tree_dict:
            return

        sel = self.view.sel()
        for region in sel:
            node = get_node_spanning_region(region, self.view.buffer_id()) or tree_dict["tree"].root_node

            for desc, _ in walk_tree(node):
                if get_size(desc) < get_size(node):
                    new_region = get_region_from_node(desc, self.view)
                    sel.subtract(region)
                    sel.add(new_region)

                    scroll_to_point(new_region.begin(), self.view)
                    return


class UserExpandSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if has_tree(self.view.buffer_id()):
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


class TreeSitterChooseDescendantsCommand(sublime_plugin.TextCommand):
    """
    TODO

    - Selecting all text should let us get root node
    - Specify query_name to look up query and use it
    - Create query for variable declarations, classes and functions
    - Include variable declarations (when selecting root node, only those that are children of root node?)
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
