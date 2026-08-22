# Sublime Text plugin host changes (4200 → 4205)

## Symptom

`Requester` (https://github.com/kylebebak/Requester) works on ST build 4200, fails to load on build 4205 with:

```
File ".../Requester/deps/urllib3/exceptions.py", line 2, in <module>
    from .packages.six.moves.http_client import (
        IncompleteRead as httplib_IncompleteRead
    )
ModuleNotFoundError: No module named 'urllib3.packages.six.moves'
```

Confirmed via `sys.version`:

- ST 4200 → Python 3.8.12
- ST 4205 → Python 3.14.6

Requester has a `.python-version` file at its repo root containing `3.8`. That value used to pin the interpreter; as of 4205 it no longer does (see below).

## What's actually going on

Confirmed by inspecting the app bundle directly:

```
$ ls "/Applications/Sublime Text.app/Contents/MacOS/" | grep plugin_host
plugin_host-3.14
plugin_host-3.3
```

`Lib/` in that same directory only has `python3.14.zip`/`python314` and `python3.3.zip`/`python33` — no functional 3.8 anywhere. The `Lib/python38` directory that exists under `~/Library/Application Support/Sublime Text/` is an empty leftover, not a real host.

**There is no 3.8 plugin host in 4205.** A `.python-version` file containing `3.8` no longer means "pin to Python 3.8" — it means "not legacy 3.3," and gets routed to whatever the current default host is, which is now 3.14.

## Why: two independent, overlapping migrations

Both explained in a single Sublime HQ blog post, *"Sublime Text Build 4200 and Future Plugin Changes"* (May 21, 2025 — https://www.sublimetext.com/blog/):

- **Python 3.3 phase-out** — gradual: the `disable_plugin_host_3.3` setting was added first (opt-in), full removal planned "some time after Q1 2026." As of today (Aug 2026) this is still mid-rollout, which is why `plugin_host-3.3` is still shipping in 4205.
- **Python 3.8 → 3.13 (shipped as 3.14) swap** — separate track, its own "next development cycle" timeline, rolled out via beta first. Already fully landed in 4205. Direct quote: *"We will be replacing Python 3.8 with 3.13 in the next development cycle. Plugins targeting 3.8 will instead run on 3.13."*

The wording confirms this is the intended design, not an incomplete rollout: plugins that declare `3.8` get **redirected** to the new interpreter rather than continuing to run on a preserved 3.8 host alongside an opt-in new one.

## Root cause of the specific crash

Not a general "3.8 code breaks on 3.14" problem — most plain Python 3.8 code runs fine on 3.14. The specific break is that Requester's vendored `urllib3` is old enough to still bundle `six` for Python 2/3 compatibility. `six.moves` implements lazy submodules via a `sys.meta_path` import hook using the legacy `find_module`/`load_module` loader protocol, which no longer works on modern CPython. Hence `urllib3.packages.six.moves` isn't found as a real module.

Fix: vendor a current `requests`/`urllib3` (urllib3 2.x dropped the six/py2 vendoring entirely), and audit other vendored deps for the same class of problem (legacy import hooks, removed stdlib modules like `imp`, `distutils`, etc.) before assuming everything else is fine on 3.14.

## Takeaway / opinion

No real grace period on this transition, unlike 3.3→3.8: that migration kept both hosts running concurrently, so plugin authors had a genuine window to port code while still targeting the old host. This transition repoints the meaning of the "current" `.python-version` value itself, so the moment a user upgrades ST, any plugin author who hadn't already ported breaks immediately, with no way to say "give me the old 3.8 binary" in the meantime.

Best guess at Sublime HQ's reasoning: since most plugins never declare `.python-version` and just ride the default, making 3.14 opt-in would mean near-zero adoption — the same reason 3.3 is being *forced* out via staged removal rather than being left opt-in forever. Understandable goal, but it does mean whoever's plugin depends on the "default" slot when a swap lands gets no warning and no fallback.
