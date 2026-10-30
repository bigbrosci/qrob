# QRob Project Memory

## Current Summary - 2026-10-30

- Latest change: moved the standalone get_potcars.py from actions_py/ to
  ~/bin/qrob_private/anvil/get_potcars.py at the user's request. The earlier
  location described below is historical; QRob no longer contains the script.
  HANDOFF.md, command usage, and the input-preparation skill reference its
  external location. Its contents and executable permissions are unchanged.
- Target project: QRob. APARE documentation supplied workflow ideas only; no
  APARE files were edited. Current task is documentation and handoff maintenance,
  not MKM modeling or cluster execution.
- Added a startup/finish protocol in AGENTS.md, HANDOFF.md, and restart_ai.md.
  Updated the two local skills and actions_py/USAGE.md to reflect current tools.
- At handoff setup, actions_py/get_potcars.py was a user-requested standalone utility and
  was already untracked at this task's start. Keep its existing implementation;
  do not mistake it for an unrelated file to delete. It uses only the standard
  library, with an editable Anvil POTCAR_DIR, explicit order or POSCAR/00/POSCAR
  input, and exact-name then _sv lookup for bare elements.
- Python 3.5-3.10 compatibility is a requirement for that standalone script.
  Earlier session checks reported 3.5 grammar and synthetic concatenation checks,
  not execution under every supported interpreter or an Anvil library check.
  The full repository environment recipe selects Python 3.11.
- Existing reformat.py trims output after the expected atom coordinates,
  preserving selective-dynamics flags; optional trailing velocity data is omitted.
  It currently warns if trimming fails, so inspect warnings before assuming a
  clean output. This behavior was inspected, not changed in this task.
- Next: follow the user's next QRob task. No calculation or resubmission is
  pending from this documentation work. Remote scheduler/library availability
  and filesystem permissions have not been checked.

## Task Log

### 2026-10-30 - Move Standalone POTCAR Utility

- Executor: Codex, user-requested move to ~/bin/qrob_private/anvil/get_potcars.py.
  Destination directory existed and no destination script was present.
- Moved the script without editing its contents; updated QRob navigation, usage,
  and skill references. No calculation inputs or scientific settings changed.
- Validation: destination exists with executable permissions, source no longer
  exists, and git diff --check passed.
- Next use: `python3 ~/bin/qrob_private/anvil/get_potcars.py Fe C H O` from
  the intended calculation directory. No POTCAR generation was run for this move.

### 2026-10-30 - Establish QRob Handoff and Memory

- Executor: Codex, at the user's request to improve QRob using APARE's Markdown
  organization as a reference. Read QRob rules, both local skills, usage,
  environment snippets, relevant command implementations, and test layout.
- Added HANDOFF.md (navigation and cross-device steps), this memory, and
  restart_ai.md (startup pointer). Extended AGENTS.md with startup, completion,
  reuse, provenance, and device-state rules. Updated both skills with concrete
  task checks and documented standalone POTCAR use in actions_py/USAGE.md.
- Borrowed APARE's separation of rules, shared state, handoff navigation, and
  reusable skills. Did not transfer its scientific settings or result status.
  The interrupted APARE review left temporary copies in
  /tmp/apare-handoff-review; they are not QRob state and need not be resumed.
- Validation: git diff --check passed; all 12 local Markdown links across the
  seven edited/new documents resolved, code fences were balanced, and both
  skills retained their name/description headers. These are documentation
  checks; no Python regression suite or physical calculation was run.
  No code, calculation inputs, generated results, shell profiles, or permissions
  changed.
- Next read-only command from the checkout: `git diff --check`.
  Live Anvil execution and multi-version Python testing remain outside this
  documentation task; no numerical acceptance claim is made.
