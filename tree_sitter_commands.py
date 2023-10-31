from __future__ import annotations

import os
from typing import TypeVar

import sublime
import sublime_plugin
from sublime_tree_sitter import (
    byte_offset,
    get_ancestor,
    get_node_spanning_region,
    get_region_from_node,
    get_size,
    get_tree_dict,
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


def scroll_to_region(region: sublime.Region, view: sublime.View):
    if region.b not in view.visible_region():
        view.show(region.b)


class TreeSitterPrintTreeCommand(sublime_plugin.TextCommand):
    """
    For debugging. If nothing selected, print syntax tree for buffer. Else, print segment(s) of tree for selection(s).
    """
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

        root_nodes: list[Node] = []
        for region in self.view.sel():
            if len(region) > 0:
                root_node = get_node_spanning_region(region, self.view.buffer_id())
                if root_node:
                    root_nodes.append(root_node)

        if not root_nodes:
            root_nodes = [tree_dict["tree"].root_node]

        parts: list[str] = []
        for root_node in root_nodes:
            parts.extend([f"{indent * depth}{self.format_node(node)}" for node, depth in walk_tree(root_node)])
            parts.append("")

        name = get_view_name(self.view)
        view = window.new_file()
        view.set_name(f"Syntax Tree - {name}" if name else "Syntax Tree")
        view.set_scratch(True)
        view.insert(edit, 0, "\n".join(parts))


def get_descendant(region: sublime.Region, view: sublime.View) -> Node | None:
    """
    Find node that spans region, then find first descendant that's smaller than this node. This descendant is basically
    guaranteed to have at least one sibling.
    """
    if not (tree_dict := get_tree_dict(view.buffer_id())):
        return

    node = get_node_spanning_region(region, view.buffer_id()) or tree_dict["tree"].root_node
    for desc, _ in walk_tree(node):
        if get_size(desc) < get_size(node):
            return desc


def get_sibling(region: sublime.Region, view: sublime.View, forward: bool = True) -> Node | None:
    """
    - Find that node spans region
    - Find "first" ancestor of this node, including node itself, that has siblings
        - If node spanning region is root node, find "first" descendant that has siblings
    - Return the next or previous sibling
    """
    node = get_node_spanning_region(region, view.buffer_id())
    if not node:
        return

    if not node.parent:
        # We're at root node, so we find the first descendant that has siblings, and return sibling adjacent to region
        tree_dict = get_tree_dict(view.buffer_id())
        first_sibling = get_descendant(region, view)

        if first_sibling and first_sibling.parent and tree_dict:
            begin = byte_offset(region.begin(), tree_dict["s"])
            if forward:
                for sibling in first_sibling.parent.children:
                    if begin <= sibling.start_byte:
                        return sibling
            else:
                for sibling in reversed(first_sibling.parent.children):
                    if begin >= sibling.start_byte:
                        return sibling

        return first_sibling

    while node.parent and node.parent.parent:
        if len(node.parent.children) == 1:
            node = node.parent
        else:
            break

    siblings = not_none(node.parent).children
    idx = siblings.index(node)
    idx = idx + 1 if forward else idx - 1
    return siblings[idx % len(siblings)]


class TreeSitterSelectAncestorCommand(sublime_plugin.TextCommand):
    """
    Expand selection to smallest ancestor that's bigger than node spanning currently selected region.

    Does not select region corresponding to root node, i.e. region that spans entire buffer, because there are easier
    ways to do this…
    """

    def run(self, edit, reverse_sel: bool = True):
        sel = self.view.sel()
        new_region: sublime.Region | None = None

        for region in sel:
            new_node = get_ancestor(region, self.view)
            if new_node and new_node.parent:
                new_region = get_region_from_node(new_node, self.view, reverse=reverse_sel)
                self.view.sel().add(new_region)

        if new_region and len(sel) == 1:
            scroll_to_region(new_region, self.view)


class TreeSitterSelectSiblingCommand(sublime_plugin.TextCommand):
    """
    Find node spanning selected region, then find its next or previous sibling (depending on value of `forward`), and
    select this region or extend current selection (depending on value of `extend`).
    """
    def run(self, edit, forward: bool = True, extend: bool = False, reverse_sel: bool = True):
        sel = self.view.sel()
        new_regions: list[sublime.Region] = []

        for region in sel:
            if sibling := get_sibling(region, self.view, forward):
                new_region = get_region_from_node(sibling, self.view, reverse=reverse_sel)
                new_regions.append(new_region)
                if not extend:
                    sel.subtract(region)
                sel.add(new_region)

        if new_regions:
            scroll_to_region(new_regions[-1] if forward else new_regions[0], self.view)


class TreeSitterSelectDescendantCommand(sublime_plugin.TextCommand):
    """
    Find node that spans region, then find first descendant that's smaller than this node, and select region
    corresponding to thsi node.
    """
    def run(self, edit, reverse_sel: bool = True):
        sel = self.view.sel()
        new_region: sublime.Region | None = None

        for region in sel:
            if desc := get_descendant(region, self.view):
                new_region = get_region_from_node(desc, self.view, reverse=reverse_sel)
                sel.subtract(region)
                sel.add(new_region)

        if new_region and len(sel) == 1:
            scroll_to_region(new_region, self.view)


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


class TreeSitterChooseDescendantsCommand(sublime_plugin.TextCommand):
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
