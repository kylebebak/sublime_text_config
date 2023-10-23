import os

import sublime_plugin
from sublime_tree_sitter import get_larger_region, get_tree_dict, walk_tree


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


class TreeSitterSelectLargerNodeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for region in self.view.sel():
            new_region = get_larger_region(region, self.view)
            if new_region:
                self.view.sel().add(new_region)
