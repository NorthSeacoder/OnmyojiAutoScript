# Repository Guidelines

## Project Structure & Module Organization

This is a Python 3.10 automation project for Onmyoji. Core reusable code lives in `module/`, including device control, OCR, config, server, GUI, and shared base utilities. Task implementations live in `tasks/<TaskName>/`, usually with `config.py`, `assets.py`, `script_task.py`, and task-specific image/OCR/click assets under nested folders. Entry points are `gui.py` for the desktop UI, `server.py` for the FastAPI service, and `script.py` for script orchestration. Runtime configuration and generated state belong in `config/` and `log/`; do not commit local logs or user secrets. Development helpers are in `dev_tools/`, deployment assets in `deploy/`, and bundled external binaries in `bin/`.

## Build, Test, and Development Commands

Run commands from the repository root.

- `python -m pip install -r requirements.txt`: install pinned runtime dependencies.
- `python gui.py`: start the local GUI and OCR server.
- `python server.py --host 0.0.0.0 --port 22270`: start the web service.
- `docker compose build`: build the Docker image from `deploy/docker/`.
- `docker compose up`: run the containerized service with the repo mounted at `/app/OnmyojiAutoScript`.
- `python dev_tools/generate_requirements.py`: regenerate `requirements.txt` from `requirements-in.txt` after dependency changes.

## Coding Style & Naming Conventions

Use 4-space indentation, UTF-8 source files, and explicit imports. Follow existing module patterns before adding new abstractions. Task folders use PascalCase (`RealmRaid`, `DemonEncounter`), while image and JSON asset names are lowercase, task-prefixed, and descriptive, such as `demon_de_find.png` or `image.json`. Keep user-facing text compatible with `assets/i18n/` when adding labels.

## Testing Guidelines

There is no dedicated test suite in this repository yet. Validate changes with the narrowest runnable path: import touched modules, run `python gui.py` or `python server.py`, and exercise the affected task against a configured emulator/device. For asset changes, verify screenshot matching and update related `image.json`, `ocr.json`, or `click.json` files together.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commit-style messages, for example `fix(RealmRaid): ...`, `docs(workflow): ...`, and `chore(workflow): ...`. Keep commits scoped to one behavioral change. Pull requests should describe the affected task/module, list manual verification steps, link related issues, and include screenshots or logs for UI, image-recognition, or task-flow changes.

## Agent-Specific Instructions

Respond in Simplified Chinese when interacting with users. Prefix shell commands with `rtk` where the local environment requires it. If adding project skills, keep the source in `.agents/skills/<skill-name>/SKILL.md` and expose it through relative symlinks instead of duplicating files.
Before working on Windows/OASX/MuMu integration, FindJade small-account flows, or real-device validation, use the project skill at `.agents/skills/oas-windows-dev/SKILL.md`.

## Local FindJade Account Setup

This workspace uses `config/oas_findjade.json` for the small-account emulator. To update the simplified FindJade small-account list, run `python scripts/configure_findjade_accounts.py` from the repo root. Defaults are server `月蚀长夜`, main invitee `不知庭院`, and two Android small accounts: `最后的黄泉 / bmkfh1992@126.com` and `破晓的森林 / CRfalling`. Add future small accounts with `--add "昵称:账号"`; use `--add "昵称:账号:OCR别名"` if account OCR needs aliases. The script rewrites the `find_jade` section and sets `script.optimization.schedule_rule` to `FIFO`, because the default `Filter` scheduler priority list does not include `FindJade` and would filter it out.
