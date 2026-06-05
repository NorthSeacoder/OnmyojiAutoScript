---
name: oas-windows-dev
description: Use when developing, debugging, syncing, or validating this OnmyojiAutoScript repo against the user's Windows MuMu/OASX setup, including SSH/SCP commands, config names, emulator serials, FindJade small accounts, scheduler issues, and known local patches.
---

# OAS Windows Development

Use this project skill before touching Windows-side OAS behavior, emulator integration, FindJade/small-account flows, OASX/server startup, or real-device validation.

## Environment

- Local repo: `/Users/yqg/personal/yys/OnmyojiAutoScript`
- Windows repo: `C:\Users\64638\OnmyojiAutoScript`
- Windows SSH over Tailscale: `rtk ssh 64638@100.106.54.99 "..."`
- Copy to Windows: `rtk scp <local> '64638@100.106.54.99:C:/Users/64638/OnmyojiAutoScript/<path>'`
- OASX/server URL on Windows: `http://127.0.0.1:22270`
- OASX is also on Windows; do not route it through Tailscale.

## Configs

- Main account config: `oas_main`
  - MuMu adb serial: `127.0.0.1:5555`
  - main nickname: `不知庭院`
- Small-account config: `oas_findjade`
  - MuMu adb serial: `127.0.0.1:5557`
  - server: `月蚀长夜`
  - small accounts currently configured:
    - `最后的黄泉 / bmkfh1992@126.com / Android`
    - `破晓的森林 / CRfalling / Android`
- Both configs should use:
  - `screenshot_method: ADB`
  - `control_method: adb`

## Existing Helper

Configure small accounts from repo root:

```bash
python scripts/configure_findjade_accounts.py
python scripts/configure_findjade_accounts.py --add "昵称:账号"
python scripts/configure_findjade_accounts.py --add "昵称:账号:OCR别名"
```

The helper rewrites only `config/oas_findjade.json` `find_jade` section and sets `script.optimization.schedule_rule = "FIFO"` because default `Filter` can exclude `FindJade`.

## Known Local Patches / Decisions

- Windows repo was updated to latest `master` earlier and kept local patches.
- `module/atom/image.py` has a guard for template larger than ROI to avoid OpenCV crash.
- `tasks/GameUi/assets.py` and `tasks/GameUi/page/page_img.json` exploration page threshold was adjusted to `0.65`.
- `tasks/Component/SwitchAccount/login_account.py` was patched:
  - submit account login through Android/Apple selector or direct return to game login page.
  - avoid false-positive login success while still on account-selection page.
  - skip server-switch popup when OCR current server already matches configured server.
- `HARVEST` / courtyard affairs comes from `tasks/Restart/login.py` via `restart.harvest_config.enable` and `enable_courtyard_affairs`. User wants to keep courtyard affairs.

## Current Feature Direction

- First fix `wanted-quests-cooperation-closure`: when main accepts small-account WantedQuests cooperation, main must actually schedule/execute `WantedQuests`.
- Then implement small-account multi-task support as account rotation around the existing global scheduler, not as a separate big task that reimplements scheduling.
- Do not rewrite existing team invite logic. Reuse `Orochi`, `Exploration`, and `GeneralInvite`.
- Default safe rollout: FindJade/cooperation first; Hunt/MysteryShop optional; Orochi/Exploration rotation disabled until stable.

## Validation Flow

1. Implement and run local syntax/import checks.
2. Sync touched files to Windows with `rtk scp`.
3. Restart Windows server/OASX as needed.
4. Validate with one config at a time:
   - `oas_main` for main account behavior.
   - `oas_findjade` for small-account switching.
5. For small accounts, test one low-risk feature first before enabling team tasks.
6. When logs mention `No emulator instance with {'serial': '127.0.0.1:5555'}`, it can be benign if ADB is connected; MuMu instance discovery uses different internal ports.

## Common Pitfalls

- Do not set enum values as uppercase strings in config. Example: `control_method` must be `adb`, not `ADB`.
- Do not assume `127.0.0.1:5555` maps to MuMu instance serials shown as `127.0.0.1:16384`; OAS can still use adb serials.
- If `FindJade` says `No task pending`, check scheduler rule. `FIFO` is safer than default `Filter` for custom tasks.
- If image template is larger than source, check synced PNG assets and ROI sizes before blaming emulator resolution.
- `CRfalling` may require mobile QQ scan if cookie expires.

## SDD Artifacts

- `specs/wanted-quests-cooperation-closure/`
- `specs/subaccount-daily-orchestration/`

Read those before implementing related features.
