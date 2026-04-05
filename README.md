# Agent Skills

A small collection of reusable Codex and agent skills.

## Install

This repo is designed to work with the [`skills` CLI](https://skills.sh/docs/cli), which is run with `npx` rather than a global install.

Install the full repo:

```bash
npx skills add huntharo/agent-skills
```

Install just `repair-codex-thread`:

```bash
npx skills add huntharo/agent-skills --skill repair-codex-thread
```

List the skills available in this repo:

```bash
npx skills add huntharo/agent-skills --list
```

## Skills

- `repair-codex-thread`
  Repair a broken Codex Desktop thread session file when a malformed image payload makes the thread unloadable.

## Details

### `repair-codex-thread`

Repairs a broken Codex Desktop thread by removing the corrupt turn from the backing session JSONL and writing a timestamped backup before the rewrite.

Useful when Codex refuses to reopen a thread because an image attachment was recorded as an empty base64 data URL.

Screenshot:

`[placeholder: add screenshot here after upload]`

Searchable error snippet:

```text
Invalid 'input[0].content[2].image_url': Expected a base64-encoded data URL with an image MIME type (e.g. 'data:image/png;base64,aW1nIGJ5dGVzIGhlcmU='), but got empty base64-encoded bytes.
```

Repo install:

```bash
npx skills add huntharo/agent-skills --skill repair-codex-thread
```

## Layout

Each skill lives under `skills/<skill-name>/` and contains its own `SKILL.md` plus any bundled resources.
