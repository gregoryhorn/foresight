# Foresight

**One sentence in. A little magic out.**
*Crystal Ball sees. Foresight makes.*

Foresight learns the tools you already have, plans the video, gets it made, and
lets [Crystal Ball](https://gregoryhorn.github.io/crystal-ball/) check every take.
Crystal Ball 1.2 installs with it. Site: https://gregoryhorn.github.io/foresight/

**In 0.1.0:** tool inventory, tool cards with one confirmed tiny test, and
Crystal Ball checks that match the media (image, audio, video).
**Next:** plan (script + scene plan + critic), make + assemble one MP4 with
captions, polish. Goals, not promises or dates.

## Install and run

Python 3.11 or newer, FFmpeg and ffprobe on PATH. No model download or provider
setup is performed. Crystal Ball 1.2.0 is pinned by release wheel URL and SHA256
in pyproject.toml. MIT; external binaries retain their own licenses.

From ~/Projects/foresight:

    python -m venv .venv
    .venv/bin/python -m pip install .
    .venv/bin/foresight inventory
    .venv/bin/foresight card templates
    .venv/bin/foresight check ~/Media/example.mp4 --report-dir ~/Reports/example

Windows PowerShell:

    py -3.11 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install .
    .\.venv\Scripts\foresight.exe inventory
    .\.venv\Scripts\foresight.exe check ~\Media\example.mp4 --report-dir ~\Reports\example

All CLI output is JSON. Exit codes: 0 completed, 1 FAIL or Not checked,
2 invalid input/setup/error. PASS is technical evidence, not creative approval.
A core-only check discloses disabled optional senses. Actual decoded media kind,
not the extension, selects applicable checks. Still/audio do not inherit a video
destination; explicit shape remains a requested constraint.

## Tool cards and one confirmed test

    foresight card --home ~/.foresight prepare examples/tiny-mp4.json
    foresight card --home ~/.foresight list
    foresight card --home ~/.foresight read CARD_ID
    foresight card --home ~/.foresight test CARD_ID --command YOUR_STABLE_ID --confirmed

Inspect the card mapping before confirming. This example invokes installed FFmpeg
once to create a 0.6 second 160x90 blue silent H.264 MP4. Only the fixed FFmpeg
mapping or narrowly validated local argument primitives are accepted; no shell,
network route, arbitrary executable or automatic install. Unknown price is not
zero. The test saves intent before executing, retains original output and report,
and enables only the tested operation/version/shape/length when applicable checks
pass. Two confirmed failures require re-test. An uncertain outcome stays Testing;
reusing the command observes the original, and a new command cannot bypass it.
No blind retry. The standalone store is local SQLite plus outputs/reports under
--home. Use separate homes for separate trust scopes; it is not a multiuser API.
Motion Studio retains its own scoped store, historical revisions and consent UI.

## Python API and Hermes

    from foresight import check, inventory
    from foresight.cards.service import Cards
    result = check("example.mp4", report_dir="new-report-directory")

Report directories must be new. The summary records input SHA256, checker version,
effective options, coverage and omissions; full report assets are retained below
assets/. Without report_dir, check returns only the summary. The checker uses an
isolated temporary config, no inherited provider settings, and the same interpreter.

Install the distribution into the Hermes plugin's Python environment and install
hermes_plugin/foresight as the plugin folder through the host's supported plugin
installation flow. The wheel includes it under share/foresight/hermes_plugin.
It exposes one foresight tool with inventory, card (untested starters), and check
actions. It registers no hooks, does not replace crystal_ball, and never dispatches
a tiny test automatically. Card mutations are intentionally CLI/API-only in 0.1.0.
Native Hermes installation is not covered by the adapter fixture tests.

## Develop and verify

    python -m unittest discover -s tests -v
    python -m compileall -q foresight tests scripts
    python scripts/privacy_scan.py
    python scripts/build_release.py

The release builder creates a wheel and source archive, anonymizes archive owner
metadata and scans every text member. It never publishes. Tests use synthetic
media only. With the installed pinned checker they exercise the installed CLI;
otherwise an explicitly labelled sibling Crystal Ball source fixture is used.
Set TMPDIR/TEMP/TMP to a private scratch directory for transient test/build files.
See docs/as-built/extraction.md for observed results and integration boundaries.

## Roadmap

1. Plan: script + scene plan + critic.
2. Make + assemble MP4.
3. Polish.

No complete-video generation, planning critic, provider calls or assembly pipeline
is implemented in this release.
