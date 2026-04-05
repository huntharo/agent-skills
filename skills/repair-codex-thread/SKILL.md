---
name: repair-codex-thread
description: Repair broken Codex Desktop thread session files when a thread GUID points to a session JSONL containing a malformed image payload, especially empty base64 data URLs like `data:image/png;base64,` that make the thread unloadable. Use when a user says a thread is broken, shows an `invalid_request_error` about `image_url`, or asks to rewrite a thread to remove a bad entry and restart Codex.
---

# Repair Codex Thread

Repair a broken Codex Desktop thread by GUID using the bundled script instead of manual JSONL surgery.

## Quick Start

1. Ask for the thread GUID if the user did not provide it.
2. Run a dry run first:

```bash
python3 scripts/repair_thread.py <thread-guid> --dry-run
```

3. If the reported corrupt turn matches the failure, run the repair:

```bash
python3 scripts/repair_thread.py <thread-guid>
```

4. Tell the user which file was repaired, where the backup was written, and that they should restart Codex.

## Workflow

### Default behavior

- Use `${CODEX_HOME:-$HOME/.codex}` as the Codex state root unless the environment clearly points elsewhere.
- Prefer GUID-based repair. The script searches `sessions/` and `archived_sessions/` and ignores backup files.
- Let the script make the backup and rewrite. Do not hand-edit the JSONL unless the script cannot classify the corruption.

### What the script removes

- Remove only turn blocks that contain an invalid user image payload.
- Treat an image payload as invalid when it is a `data:image/...;base64,` URL with no bytes after the comma.
- Remove the entire turn block starting at that turn's `task_started` event and ending immediately before the next `task_started` event or end of file.

### Verification

- Confirm the script reports a backup path for each modified file.
- Confirm the repaired file no longer contains the empty base64 data URL.
- If the user hit this from the UI, tell them to fully quit and restart Codex after the repair.

## When to Stop and Inspect Manually

- Stop if the script reports no matching thread files.
- Stop if the script finds the thread file but no invalid image payloads.
- Stop if the corruption is not an empty base64 image URL. Use `rg` on the session file to inspect the specific failure before changing anything by hand.

## Script

- Main entry point: `scripts/repair_thread.py`
- Optional direct-file mode for testing:

```bash
python3 scripts/repair_thread.py --file /path/to/session.jsonl --dry-run
```

## Expected Output

- Thread file path
- Removed turn IDs and line ranges
- Backup path
- Repaired file path
- A no-op message when nothing matched
