#!/usr/bin/env python3

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


INVALID_DATA_URL_RE = re.compile(r"^data:image/[^;]+;base64,\s*$")


@dataclass
class TurnSpan:
    turn_id: str
    start_index: int
    end_index: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Repair broken Codex Desktop session threads with invalid image payloads."
    )
    parser.add_argument(
        "thread_guid",
        nargs="?",
        help="Thread GUID to locate under the Codex sessions directory.",
    )
    parser.add_argument(
        "--codex-home",
        default=str(Path.home() / ".codex"),
        help="Codex state directory. Defaults to ~/.codex.",
    )
    parser.add_argument(
        "--file",
        help="Repair a specific session JSONL file directly instead of locating by GUID.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be removed without rewriting any files.",
    )
    args = parser.parse_args()

    if not args.file and not args.thread_guid:
        parser.error("provide a thread GUID or --file")

    return args


def load_jsonl(path: Path) -> tuple[list[str], list[dict]]:
    raw_lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    parsed = []
    for lineno, line in enumerate(raw_lines, start=1):
        try:
            parsed.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return raw_lines, parsed


def invalid_image_url(value: object) -> bool:
    return isinstance(value, str) and bool(INVALID_DATA_URL_RE.match(value))


def content_has_invalid_image(content: object) -> bool:
    if not isinstance(content, list):
        return False
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "input_image" and invalid_image_url(item.get("image_url")):
            return True
    return False


def event_has_invalid_image(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    images = payload.get("images")
    if not isinstance(images, list):
        return False
    return any(invalid_image_url(image) for image in images)


def find_turn_spans(entries: list[dict]) -> list[TurnSpan]:
    spans: list[TurnSpan] = []
    current_start = None
    current_turn_id = None

    for index, entry in enumerate(entries):
        if entry.get("type") != "event_msg":
            continue
        payload = entry.get("payload")
        if not isinstance(payload, dict) or payload.get("type") != "task_started":
            continue

        turn_id = payload.get("turn_id")
        if not isinstance(turn_id, str):
            continue

        if current_start is not None and current_turn_id is not None:
            spans.append(TurnSpan(current_turn_id, current_start, index - 1))

        current_start = index
        current_turn_id = turn_id

    if current_start is not None and current_turn_id is not None:
        spans.append(TurnSpan(current_turn_id, current_start, len(entries) - 1))

    return spans


def span_is_corrupt(entries: list[dict], span: TurnSpan) -> bool:
    for entry in entries[span.start_index : span.end_index + 1]:
        if entry.get("type") == "response_item":
            payload = entry.get("payload")
            if (
                isinstance(payload, dict)
                and payload.get("type") == "message"
                and payload.get("role") == "user"
                and content_has_invalid_image(payload.get("content"))
            ):
                return True

        if entry.get("type") == "event_msg" and event_has_invalid_image(entry.get("payload")):
            return True

    return False


def backup_path_for(path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return path.with_name(f"{path.name}.bak-{timestamp}")


def locate_thread_files(codex_home: Path, thread_guid: str) -> list[Path]:
    candidates: list[Path] = []
    search_roots = [codex_home / "sessions", codex_home / "archived_sessions"]

    for root in search_roots:
        if not root.exists():
            continue
        for path in root.rglob(f"*{thread_guid}*.jsonl"):
            if ".bak-" in path.name:
                continue
            candidates.append(path)

    return sorted(set(candidates))


def repair_file(path: Path, dry_run: bool) -> tuple[bool, list[TurnSpan], Path | None]:
    raw_lines, entries = load_jsonl(path)
    spans = find_turn_spans(entries)
    corrupt_spans = [span for span in spans if span_is_corrupt(entries, span)]

    if not corrupt_spans:
        return False, [], None

    keep = [True] * len(raw_lines)
    for span in corrupt_spans:
        for index in range(span.start_index, span.end_index + 1):
            keep[index] = False

    if dry_run:
        return True, corrupt_spans, None

    backup_path = backup_path_for(path)
    shutil.copy2(path, backup_path)

    kept_lines = [line for line, keep_line in zip(raw_lines, keep) if keep_line]
    path.write_text("".join(kept_lines), encoding="utf-8")

    return True, corrupt_spans, backup_path


def main() -> int:
    args = parse_args()

    if args.file:
        targets = [Path(args.file).expanduser()]
    else:
        codex_home = Path(args.codex_home).expanduser()
        targets = locate_thread_files(codex_home, args.thread_guid)

    if not targets:
        print("No matching session files found.", file=sys.stderr)
        return 1

    changed_any = False

    for target in targets:
        if not target.exists():
            print(f"Missing file: {target}", file=sys.stderr)
            continue

        changed, corrupt_spans, backup_path = repair_file(target, dry_run=args.dry_run)

        print(f"File: {target}")
        if not changed:
            print("  Status: no invalid image payload turns found")
            continue

        changed_any = True
        print(
            "  Removed turns: "
            + ", ".join(
                f"{span.turn_id} (lines {span.start_index + 1}-{span.end_index + 1})"
                for span in corrupt_spans
            )
        )

        if args.dry_run:
            print("  Status: dry run only")
        else:
            print(f"  Backup: {backup_path}")
            print("  Status: repaired")

    return 0 if changed_any else 1


if __name__ == "__main__":
    raise SystemExit(main())
