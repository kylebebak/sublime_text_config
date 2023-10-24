import os

import sublime_plugin
from sublime_tree_sitter import (
    get_larger_region,
    get_node_spanning_region,
    get_region_from_node,
    get_tree_dict,
    query_tree,
    walk_tree,
)


class TreeSitterPrintTreeCommand(sublime_plugin.TextCommand):
    def run(self, edit, out_path: str = ""):
        tree_dict = get_tree_dict(self.view.buffer_id())
        if not tree_dict:
            return

        if not out_path:
            for node in walk_tree(tree_dict["tree"].root_node):
                print(f"{node.start_byte}, {node}")

        else:
            with open(os.path.expanduser(out_path), "w+") as f:
                for node in walk_tree(tree_dict["tree"].root_node):
                    f.write(f"{node.start_byte}, {node}\n")


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


class TreeSitterSelectChooseDescendantsCommand(sublime_plugin.TextCommand):
    """
    TODO:

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
