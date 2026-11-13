# Foresight extraction as built

Input: coordinator's standalone extraction brief; existing app-design Director
contract r1 at ~/.hermes/profiles/app-design/workspace/design-documents/motion-studio/engineering/director-contract-r1.md,
including MA-r1 applicability. This is a bounded extraction, not a new product
design. No wait for design/approval was introduced. No excluded profile content
was opened. No native app UI was made: NSH/GPUI Kit do not apply to this Python
CLI/library extraction. The static documentation site follows Crystal Ball's
existing palette and layout; no design document was authored.

Implemented: foresight/cards contains passive inventory, finite Mapping, executable
fingerprinting and bounded execute/validation ports; review contains core-only
Crystal Ball 1.2.0 checks, decoded-media applicability, coverage and retained report
assets. api.py exports check/inventory; Cards(home) supplies local SQLite intent
and receipt persistence, exact originals and reports. cli.py supplies JSON
inventory, card list/templates/prepare/read/test, and check. hermes.py registers
one foresight tool, no hooks, automatic tests, provider calls or installs.
Host consent/scoping, historical revisions, RPC, SQLite table adapters, take
removal and Desktop UI remain in Motion Studio. Compatibility import aliases
forward old imports and fixture patches to the one Foresight implementation.
Motion Studio injects its existing stronger original-media validator into execute.

Technical defaults: standalone cards use a separate local home (default
~/.foresight), not Studio's scoped database. A test command is persisted before
execution, uncertain outcomes remain Testing across reopen, and replay observes
the original receipt. Unknown price is denied; only confirmed failures count.
Fingerprint drift invalidates a Tested card. Summary-only checks do not retain
assets unless report_dir is explicit; new report directories refuse overwrite.
Temporary checker environments point HOME/USERPROFILE/AppData to a private root,
never inherit PYTHONPATH or provider config, and redact both JSON-escaped and
native paths. Report asset names always use forward slashes. SQLite connections
are explicitly closed: Windows verification exposed the otherwise hidden file lock.
No load-time installation, host registry inspection or replacement checker added.

Packaging: foresight-media 0.1.0 / Python >=3.11 / MIT. Crystal Ball release wheel
URL+SHA256 is the supplied 1.2.0 pin; its local wheel hash was verified. Pydantic 2
is the only additional direct dependency. Privacy/build scripts follow Crystal
Ball, including anonymous source-archive ownership. One exact public dependency
URL is exempted from the personal-name matcher; paths, emails and keys still scan.
No publication, tags, pushes or remote repository creation are authorized/performed.

Verification so far: 25 unittest tests pass on /usr/bin/python3 (3.14.4) and the
specified Python 3.11.15 venv; compileall passes. System Python's real-check tests
explicitly inject sibling Crystal Ball source because that interpreter lacks the
distribution. The 3.11 venv tests use the actual installed pinned wheel. Tests
cover real still/audio/disguised bytes, shape failure, one actual tiny MP4 and
receipt reuse; unsafe mappings, unknown cost, uncertain delivery, confirmed
failures, drift, report traversal/no overwrite, plugin registration/dispatch and
privacy scanner failure sensitivity. Earlier 21-test candidate also passed both.
Windows native verification via ssh windows-pc: 25 tests passed on Python 3.11
with the actual pinned Crystal Ball wheel and installed FFmpeg. Initial remote
runs found missing test dependencies, then unclosed SQLite handles and missing
isolated Windows home variables; the root causes were fixed rather than skipped.
A final forward-slash report asset-name correction made the same media assertions
pass on both platforms. Privacy scan passed (34 files, zero findings); release
builder produced a privacy-scanned wheel (25 members) and sdist (42 members).
The archive scan also checks anonymous tar owner metadata. The final archives
were copied to Windows, installed/extracted anew, and passed all 25 tests plus
compileall; running the installed package outside the source tree returned 0.1.0.
A Python AST check measured 67 functions, maximum span 73, with no Studio imports.
An installed-wheel test run outside the Linux source checkout also passed all 25
checks; the console entry point returned 0.1.0 and untested starter cards.

Motion Studio: python3 -m unittest discover -s tests passed 432 tests after local
wheel installation in the test interpreter; compileall passed; check_structure
with the requested NODE_PATH passed (maximum function span 167). First full run
failed isolated Music children because Foresight was not yet installed; installing
the local wheel fixed the actual import path, with no assertion changes. Existing
unclosed-connection ResourceWarnings elsewhere in Studio remain non-failing.
The site was opened in a browser and its header/hero screenshot inspected: no
visible overlap/clipping; ordinary scrolling continues below the viewport.

Limits: actual Hermes native installation is unverified (adapter fixtures only).
The plugin intentionally exposes starter cards, not card mutations; use the
CLI/API for preparation/confirmed local tests. Motion Studio's local wheel
reference is an interim development dependency; coordinator replaces it after
publishing. Complete-video planning/making/polish are README roadmap only.
