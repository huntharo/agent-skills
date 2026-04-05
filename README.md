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

## Layout

Each skill lives under `skills/<skill-name>/` and contains its own `SKILL.md` plus any bundled resources.
