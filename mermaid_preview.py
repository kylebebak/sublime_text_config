"""Render mermaid code blocks in the current buffer as PNG phantoms.

Commands:
  mermaid_render   Find mermaid fences, render via mmdc, show PNGs below each block
  mermaid_remove   Remove all mermaid phantoms from the view

PNGs are cached in CACHE_DIR as <md5 of block text>.png. db.json tracks last
use per hash so the cache can be pruned to MAX_FILES (least recently used first).
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import re
import struct
import subprocess
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import sublime
import sublime_plugin

# Stable fnm "default" alias; the per-shell multishell path changes every session.
MMDC_PATH = os.path.expanduser("~/.local/share/fnm/aliases/default/bin/mmdc")
CACHE_DIR = os.path.join(tempfile.gettempdir(), "sublime_mermaid")
DB_PATH = os.path.join(CACHE_DIR, "db.json")
MAX_FILES = 32
RENDER_SCALE = 2  # mmdc pixel scale; images are displayed at 1/RENDER_SCALE
MMDC_TIMEOUT = 60
MAX_WORKERS = 4  # concurrent mmdc processes (each launches its own Chrome)
PHANTOM_KEY = "mermaid_preview"
DEBOUNCE_MS = 400

FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})\s*mermaid\b.*$")
db_lock = threading.Lock()


def find_blocks(view: sublime.View) -> list[tuple[str, int]]:
    """Return [(code, end_point)] for each closed mermaid fence.

    end_point is the end of the closing fence line (where the phantom goes).
    """
    blocks: list[tuple[str, int]] = []
    lines = view.lines(sublime.Region(0, view.size()))
    i = 0
    while i < len(lines):
        m = FENCE_OPEN.match(view.substr(lines[i]))
        if not m:
            i += 1
            continue
        fence = m.group(1)
        closer = re.compile(r"^\s*" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*$")
        j = i + 1
        while j < len(lines) and not closer.match(view.substr(lines[j])):
            j += 1
        if j >= len(lines):
            break  # unclosed fence
        code = "\n".join(view.substr(lines[k]) for k in range(i + 1, j))
        if code.strip():
            blocks.append((code, lines[j].end()))
        i = j + 1
    return blocks


def load_db() -> dict[str, float]:
    """Map of md5 hash -> last used unix timestamp."""
    try:
        with open(DB_PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_db(db: dict[str, float]) -> None:
    tmp = DB_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(db, f)
    os.replace(tmp, DB_PATH)


def touch_and_prune(hashes: set[str]) -> None:
    """Mark hashes as used now, then evict least recently used beyond MAX_FILES."""
    with db_lock:
        db = load_db()
        now = time.time()
        for h in hashes:
            db[h] = now
        # Drop entries whose file vanished.
        db = {h: t for h, t in db.items() if os.path.exists(png_path(h))}
        for h, _ in sorted(db.items(), key=lambda kv: kv[1])[: max(0, len(db) - MAX_FILES)]:
            try:
                os.remove(png_path(h))
            except OSError:
                pass
            del db[h]
        save_db(db)


def png_path(h: str) -> str:
    return os.path.join(CACHE_DIR, h + ".png")


def png_size(path: str) -> tuple[int, int]:
    """Read (width, height) from the PNG IHDR chunk."""
    with open(path, "rb") as f:
        head = f.read(24)
    width, height = struct.unpack(">II", head[16:24])
    return width, height


def render(code: str, h: str) -> str | None:
    """Render code to the cached PNG if needed. Returns an error string or None."""
    out = png_path(h)
    if os.path.exists(out):
        return None
    # Unique temp names: overlapping refreshes may render the same block at once.
    token = uuid.uuid4().hex
    src = os.path.join(CACHE_DIR, f"{h}.{token}.mmd")
    tmp_out = os.path.join(CACHE_DIR, f"{h}.{token}.part.png")
    with open(src, "w") as f:
        f.write(code)
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(MMDC_PATH) + os.pathsep + env.get("PATH", "")
    try:
        proc = subprocess.run(
            [MMDC_PATH, "-i", src, "-o", tmp_out, "-b", "white", "-s", str(RENDER_SCALE), "-q"],
            capture_output=True,
            text=True,
            timeout=MMDC_TIMEOUT,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return str(e)
    finally:
        try:
            os.remove(src)
        except OSError:
            pass
    if proc.returncode != 0 or not os.path.exists(tmp_out):
        return (proc.stderr or proc.stdout or "mmdc failed").strip()
    os.replace(tmp_out, out)  # atomic: Sublime never sees a half-written PNG
    return None


@lru_cache(maxsize=MAX_FILES)
def img_tag(h: str) -> str:
    """<img> with the PNG inlined as a data URI (file contents are immutable per hash)."""
    path = png_path(h)
    w, ht = png_size(path)
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return f'<img src="data:image/png;base64,{data}" width="{w // RENDER_SCALE}" height="{ht // RENDER_SCALE}">'


def phantom_html(h: str, error: str | None) -> str:
    if error:
        return '<body id="mermaid-preview"><div style="color:red">mermaid error: {}</div></body>'.format(
            html.escape(error[:500]).replace("\n", "<br>")
        )
    return f'<body id="mermaid-preview">{img_tag(h)}</body>'


def worker(view: sublime.View, blocks: list[tuple[str, int]]) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    hashed = [(hashlib.md5(code.encode("utf-8")).hexdigest(), code, point) for code, point in blocks]
    # Identical blocks share a hash; render each unique one once, in parallel.
    unique = {h: code for h, code, _ in hashed}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        errors = dict(zip(unique, pool.map(render, unique.values(), unique.keys())))
    results: list[tuple[str, int, str | None]] = [(h, point, errors[h]) for h, _, point in hashed]
    touch_and_prune({h for h, _, err in results if not err})

    def apply() -> None:
        if not view.is_valid():
            return
        view.erase_phantoms(PHANTOM_KEY)
        for h, point, err in results:
            view.add_phantom(
                PHANTOM_KEY,
                sublime.Region(point, point),
                phantom_html(h, err),
                sublime.LAYOUT_BLOCK,
            )

    sublime.set_timeout(apply, 0)


class MermaidRenderCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit) -> None:
        blocks = find_blocks(self.view)
        if not blocks:
            self.view.window().status_message("Mermaid: no mermaid code blocks found")
            return
        self.view.window().status_message(f"Mermaid: rendering {len(blocks)} diagram(s)...")
        threading.Thread(target=worker, args=(self.view, blocks), daemon=True).start()


class MermaidRemoveCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit) -> None:
        disable_auto(self.view.id())
        self.view.erase_phantoms(PHANTOM_KEY)


# --- Auto render -------------------------------------------------------------
# Re-renders (debounced) on every edit. Stateless: each refresh just runs mmdc for
# blocks that aren't cached yet.

auto_views: set[int] = set()  # view ids with auto render on
generations: dict[int, int] = {}  # bumped per refresh; stale results are dropped
debounce_tokens: dict[int, int] = {}
last_good: dict[int, list[str | None]] = {}  # per block index, last hash that rendered
last_applied: dict[int, list[tuple[str | None, str | None]]] = {}  # (hash, error) signature


def block_hash(code: str) -> str:
    return hashlib.md5(code.encode("utf-8")).hexdigest()


def disable_auto(view_id: int) -> None:
    auto_views.discard(view_id)
    generations[view_id] = generations.get(view_id, 0) + 1  # drop in-flight results
    debounce_tokens.pop(view_id, None)
    last_good.pop(view_id, None)
    last_applied.pop(view_id, None)


def auto_phantom_html(h: str | None, error: str | None) -> str:
    """Image (if any) plus error text (if any), so a bad edit keeps the last good image."""
    parts = []
    if h:
        parts.append(img_tag(h))
    if error:
        parts.append(
            '<div style="color:red">mermaid error: {}</div>'.format(html.escape(error[:500]).replace("\n", "<br>"))
        )
    return '<body id="mermaid-preview">' + "".join(parts) + "</body>"


def apply_auto(
    view: sublime.View,
    gen: int,
    results: list[tuple[str | None, str | None, str]],
    good: list[str | None],
) -> None:
    """Main thread. results: (hash to display, error, hash of the block text) per block."""
    vid = view.id()
    if not view.is_valid() or vid not in auto_views or generations.get(vid) != gen:
        return
    # Results were computed from an earlier snapshot of the buffer. If it has changed since,
    # the points are stale; drop them (the debounced refresh for that edit follows).
    current = find_blocks(view)
    if [block_hash(code) for code, _ in current] != [bh for _, _, bh in results]:
        return
    last_good[vid] = good
    signature = [(h, err) for h, err, _ in results]
    if last_applied.get(vid) == signature:
        return  # nothing visible changed; existing phantoms track their text
    last_applied[vid] = signature
    view.erase_phantoms(PHANTOM_KEY)  # shared with the one-off render, so no duplicates
    for (h, err, _), (_, point) in zip(results, current):
        view.add_phantom(
            PHANTOM_KEY,
            sublime.Region(point, point),
            auto_phantom_html(h, err),
            sublime.LAYOUT_BLOCK,
        )


def render_and_apply(
    view: sublime.View,
    gen: int,
    blocks: list[tuple[str, int]],
    previous: list[str | None],
) -> None:
    """Background thread: render uncached blocks in parallel, then apply (latest wins)."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    hashed = [(block_hash(code), code) for code, _ in blocks]
    unique = {h: code for h, code in hashed}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        errors = dict(zip(unique, pool.map(render, unique.values(), unique.keys())))

    results: list[tuple[str | None, str | None, str]] = []
    good: list[str | None] = []
    for i, (h, _) in enumerate(hashed):
        err = errors[h]
        old = previous[i] if i < len(previous) else None
        if err is None:
            shown = h
        else:  # keep the last good image for this block while showing the error
            shown = old if old and os.path.exists(png_path(old)) else None
        results.append((shown, err, h))
        good.append(h if err is None else old)
    touch_and_prune({h for h, err in errors.items() if not err})
    sublime.set_timeout(lambda: apply_auto(view, gen, results, good), 0)


def refresh(view: sublime.View) -> None:
    vid = view.id()
    gen = generations.get(vid, 0) + 1
    generations[vid] = gen
    blocks = find_blocks(view)
    previous = last_good.get(vid, [])
    threading.Thread(target=render_and_apply, args=(view, gen, blocks, previous), daemon=True).start()


class MermaidAutoRenderCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit) -> None:
        auto_views.add(self.view.id())
        refresh(self.view)


class MermaidAutoRenderListener(sublime_plugin.EventListener):
    def on_modified_async(self, view: sublime.View) -> None:
        vid = view.id()
        if vid not in auto_views:
            return
        token = debounce_tokens.get(vid, 0) + 1
        debounce_tokens[vid] = token

        def fire() -> None:
            if debounce_tokens.get(vid) == token and vid in auto_views and view.is_valid():
                refresh(view)

        sublime.set_timeout_async(fire, DEBOUNCE_MS)

    def on_pre_close(self, view: sublime.View) -> None:
        disable_auto(view.id())
