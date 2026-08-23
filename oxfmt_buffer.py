"""
Formats the current buffer's content with `oxfmt`, without requiring the buffer to be saved first.

`oxfmt`'s LSP mode (configured in `LanguageServers.sublime-settings`) has known upstream bugs around unsaved/dirty
buffers, so `lsp_format_document` only reliably formats files that are saved to disk. This command sidesteps the
LSP entirely: it pipes the live buffer content to `oxfmt --stdin-filepath=...` over stdin/stdout and replaces the
buffer with the result. Nothing ever touches disk, so there's no temp file to clean up and no user-visible side
effect other than the buffer being formatted.
"""

from __future__ import annotations

import os
import subprocess

import sublime
import sublime_plugin

from .file_and_view_commands import get_project_path

# Mirrors the `oxfmt` selector in `LanguageServers.sublime-settings`.
SCOPE_EXTENSIONS: list[tuple[str, str]] = [
    ("source.json", "json"),
    ("source.yaml", "yaml"),
    ("source.toml", "toml"),
    ("source.scss", "scss"),
    ("source.less", "less"),
    ("source.css", "css"),
    ("source.tsx", "tsx"),
    ("source.ts", "ts"),
    ("source.jsx", "jsx"),
    ("source.js", "js"),
    ("text.html.markdown", "md"),
    ("text.html", "html"),
]


def extension_for_view(view: sublime.View) -> str | None:
    for scope, ext in SCOPE_EXTENSIONS:
        if view.match_selector(0, scope):
            return ext
    return None


def oxfmt_executable(start_dir: str) -> list[str]:
    """
    Walk up from `start_dir` looking for a local `node_modules/.bin/oxfmt`, same as the `npx` fallback described in
    `LanguageServers.sublime-settings`. Falls back to `npx oxfmt` if none is found.
    """
    directory = start_dir
    while True:
        candidate = os.path.join(directory, "node_modules", ".bin", "oxfmt")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return [candidate]
        parent = os.path.dirname(directory)
        if parent == directory:
            return ["npx", "oxfmt"]
        directory = parent


TIMEOUT_S = 2


class OxfmtBufferCommand(sublime_plugin.TextCommand):
    def is_enabled(self) -> bool:
        return extension_for_view(self.view) is not None

    def run(self, edit: sublime.Edit) -> None:
        view = self.view
        ext = extension_for_view(view)
        if ext is None:
            sublime.status_message("oxfmt: unsupported scope")
            return

        # A real path (even unsaved edits to it) lets oxfmt discover the right .oxfmtrc/.gitignore by walking up
        # from it, same as it would for a saved file. Only synthesize a fake one for brand new, never-saved buffers.
        stdin_filepath = view.file_name()
        if not stdin_filepath:
            base_dir = get_project_path(view) or os.getcwd()
            stdin_filepath = os.path.join(base_dir, f"__buffer__.{ext}")

        content = view.substr(sublime.Region(0, view.size()))
        cwd = os.path.dirname(stdin_filepath)
        argv = oxfmt_executable(cwd) + [f"--stdin-filepath={stdin_filepath}"]

        try:
            result = subprocess.run(  # noqa: PLW1510, UP022
                argv,
                input=content.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd if os.path.isdir(cwd) else None,
                timeout=TIMEOUT_S,
            )
        except FileNotFoundError:
            sublime.status_message("oxfmt: executable not found (is it installed?)")
            return
        except subprocess.TimeoutExpired:
            sublime.status_message("oxfmt: timed out")
            return

        if result.returncode != 0:
            error_lines = result.stderr.decode("utf-8", "replace").strip().splitlines()
            sublime.status_message(f"oxfmt: {error_lines[0] if error_lines else 'format failed'}")
            return

        formatted = result.stdout.decode("utf-8")
        if formatted == content:
            sublime.status_message("oxfmt: already formatted")
            return

        viewport_position = view.viewport_position()
        selections = [(r.a, r.b) for r in view.sel()]

        view.replace(edit, sublime.Region(0, view.size()), formatted)

        size = view.size()
        view.sel().clear()
        for a, b in selections:
            view.sel().add(sublime.Region(min(a, size), min(b, size)))
        view.set_viewport_position(viewport_position, False)

        sublime.status_message("oxfmt: formatted")
