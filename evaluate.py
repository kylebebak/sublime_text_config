from __future__ import annotations, division

import datetime
import json
import math
import subprocess
import threading

import sublime
import sublime_plugin


class EvaluateCommand(sublime_plugin.TextCommand):
    view: sublime.View

    def run(self, edit):
        sels = self.view.sel()

        threads: list[EvaluateCall] = []
        for sel in sels:
            to_eval = self.view.substr(sel)
            thread = EvaluateCall(sel, to_eval, 5)
            threads.append(thread)
            thread.start()

        self.view.sel().clear()

        self.handle_threads(edit, threads)

    def handle_threads(self, edit: sublime.Edit, threads: list[EvaluateCall], offset: int = 0):
        for t in threads:
            t.join(5)
            offset = self.replace(edit, t, offset)

        selections = len(self.view.sel())
        sublime.status_message(f"Evaluated {selections} selection(s)")

    def replace(self, edit: sublime.Edit, thread: EvaluateCall, offset: int):
        sel = thread.sel
        original = thread.original
        result = thread.result

        if offset:
            sel = sublime.Region(sel.begin() + offset, sel.end() + offset)

        prefix = original
        main = str(result)
        self.view.replace(edit, sel, main)

        end_point = (sel.begin() + len(prefix) + len(main)) - len(original)
        self.view.sel().add(sublime.Region(end_point, end_point))

        return offset + len(main) - len(original)


class EvaluateCall(threading.Thread):
    def __init__(self, sel: sublime.Region, to_eval: str, timeout: float):
        self.sel = sel
        self.original = to_eval
        self.timeout = timeout
        self.result = self.original  # Default result
        threading.Thread.__init__(self)

    def run(self):
        """
        Evaluate `self.original`, save to `self.result`. If `self.timeout` reached, the run fails and nothing changes.

        If `self.original` starts with '!', after trimming leading spaces, it is evaluated as Shell code. (The same
        convention as ipython).

        Otherwise, it is evaluated as Python code.
        """
        if self.original.lstrip().startswith("!"):
            # Remove the first bang
            shell_code = self.original.lstrip()[1:]
            try:
                p = subprocess.Popen(
                    shell_code,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                # stderr goes to stdout
                out, _ = p.communicate(timeout=self.timeout)
                out = out.decode()

                # Remove the last newline
                if out.endswith("\n"):
                    out = out[:-1]

                self.result = out
            except Exception:
                pass
        else:
            try:
                tmp_global = {"math": math, "datetime": datetime, "json": json}
                code = compile(self.original, "<string>", "eval")
                self.result = eval(code, tmp_global)
            except (ValueError, SyntaxError):
                pass
