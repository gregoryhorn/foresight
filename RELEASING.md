# Maintainer release procedure

This checklist does not announce a release or authorize live installation.
See [README.md](README.md), [AGENTS.md](AGENTS.md) and
[CHANGELOG.md](CHANGELOG.md). Version 0.1.0 currently labels the extracted source;
a version in pyproject.toml is not evidence of a published, qualified release.

## Candidate and ownership

Confirm gh api user --jq .login matches the authorized repository owner and
origin matches the intended public Foresight repository. Fetch main and inspect status,
the index and divergence. Work on main in the primary checkout only; no
branches/worktrees, force pushes, history rewriting or staging unrelated WIP.
Coordinate the implementation owner before committing its files.

app-design owns design/acceptance; app-developer owns application code, tests and
factual as-built records. Supply the applicable app-design revision before code
changes. Maintenance may publish routine docs and repository hygiene, not author
code fixes or silently revise specialist records. An in-progress as-built or
uncommitted correction is not a completion signoff.

## Build and verify the frozen candidate

1. Select a reviewed committed candidate and record its full SHA and input
   versions. Coordinate all WIP before building: scripts/build_release.py reads
   working files, not a Git commit snapshot. Check version consistency and update
   a dated Keep a Changelog entry without claiming unfinished features released.
2. Use a dedicated development environment with Python >=3.11, external
   ffmpeg/ffprobe and SoX for the quiet-tone fixture. Export TMPDIR, TMP and TEMP
   to approved scratch. Install the candidate and build prerequisites in this
   environment only, never in the live Hermes environment. The checker dependency
   must be the exact release URL plus SHA256 declared in pyproject.toml.
3. Run python -m unittest discover -s tests -v and
   python scripts/privacy_scan.py. Record interpreter/tool versions, installed
   checker version, passes, skips and failures. Require native Linux and Windows
   component CI for this candidate before release; inspect actual jobs, not just
   workflow YAML. Source fallback/fixture checks do not qualify the installed
   checker or a real host. A prepared, unpublished workflow is not test evidence.
4. With separately provisioned build requirements, run
   python scripts/build_release.py. Inspect dist/build.log and the actual wheel
   and source archive. The builder stages selected files in temporary storage,
   normalizes source ownership and scans archive contents; it does not tag/upload.
   Reject private evidence, credentials, binaries, bytecode and machine paths.
5. Install the built wheel into a separately authorized disposable environment,
   then run tests/imports/CLI outside the checkout on both native Linux and
   Windows. Report which imports resolve to the installed wheel. Do not infer
   native Windows execution from Linux wheel resolution or older candidate tests.
6. Obtain completion signoff for the exact candidate, including applicable
   subprocess descendant cleanup, retained checker/media reports and real
   Hermes host registration/UI/report flows on both platforms. These require
   separately authorized test hosts; never install/enable the production plugin
   during maintenance. Component CI does not close this gate.

## Publish and read back

Review git diff --check and the explicit staged diff; commit only intended files.
Push main only after applicable candidate tests pass. Read back origin/main and
GitHub's exact commit, then require successful exact-head CI. Delegate application
failures to app-developer; never weaken tests or take over code fixes.

Only after qualification, use a new annotated vVERSION tag at the verified SHA.
Do not replace tags/assets. Push the explicit tag and verify its peeled remote
SHA. Create a GitHub release with explicit tag, target SHA, reviewed limitations
and only inspected artifacts. Compute SHA256 of the exact wheel/source bytes;
read back release metadata/assets, download them to approved scratch and compare
their hashes before announcing a distributable pin. The local builder and a
successful upload response alone are not publication verification.

## Promotion and rollback

Do NOT pin Foresight in Motion Studio until complete, working and tested on BOTH
native Windows and Linux, including required host/UI qualification. Use only a
release asset URL plus SHA256; a relative local wheel path is not distributable.
The CF-FEA-r1 candidate has recorded passing native Linux and Windows source
and installed-wheel suites, plus disposable-host lifecycle/removal evidence.
The bounded CF-FEA-REVIEW-r1 conformance review is complete; see the local
`docs/as-built/review.md` and its linked exact-candidate evidence. These results
are not Studio UI/caller or real unfamiliar-tool qualification, hosted component
CI, a published release or downstream pin. Those promotion gates remain open.
Recheck exact candidate identities and owner completion before promotion rather
than repeating missing-baseline claims or treating standalone review as release
clearance.

For a bad release, stop promotion and document an explicit known-good version.
Have app-developer produce a new corrective version; do not overwrite assets,
move tags, rewrite history or self-update installed plugins. Preserve user data.
Every NousResearch PR, issue/comment or catalog SHA change needs the owner's exact
payload approval before posting; no delegate may bypass that boundary.
