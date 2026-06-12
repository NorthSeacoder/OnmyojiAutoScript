# Acceptance: Wanted Quests Cooperation Closure

**Workspace**: `wanted-quests-cooperation-closure`
**Date**: 2026-06-05
**Status**: Passed for scheduling closure

---

## Scope

This acceptance records the closure evidence for the producer-consumer gap:

- producer: small-account cooperation invitation popup
- consumer trigger: main-account `BaseTask._burst()`
- downstream task: main-account `WantedQuests`

This does not certify every `WantedQuests` internal OCR, navigation, or battle path. Those remain owned by the existing `WantedQuests` task.

---

## Verification Environment

- Windows repo: `C:\Users\64638\OnmyojiAutoScript`
- Main config: `oas_main`
- Main emulator adb serial: `127.0.0.1:5555`
- Verification time: 2026-06-05 18:29 local Windows time

Preconditions applied for the test:

- Synced `tasks/base_task.py`, `scripts/check_wanted_quests_main.py`, and `AGENTS.md` to Windows.
- Ran `venv\Scripts\python.exe scripts/check_wanted_quests_main.py --config config/oas_main.json --fix`.
- Temporarily delayed `activity_shikigami` and `kekkai_utilize` in `config/oas_main.json` to keep `WantedQuests` first in pending queue.
- Backed up the pre-test main config on Windows as `config/oas_main.before_wq_closure.json`.

---

## Evidence

Windows syntax check passed:

```text
venv\Scripts\python.exe -m py_compile tasks/base_task.py scripts/check_wanted_quests_main.py
```

Main-account config check passed:

```text
OK wanted_quests.scheduler.enable=true
OK wanted_quests.scheduler.next_run=2026-06-05 18:26:54
OK schedule rule will not exclude WantedQuests
```

Scheduler selected `WantedQuests` first:

```text
Pending tasks: ['WantedQuests', 'TalismanPass', 'Duel']
Scheduler: Start task `WantedQuests`
```

Main entered `WANTEDQUESTS`:

```text
--------------------------------- WANTEDQUESTS ---------------------------------
module_path: C:\Users\64638\OnmyojiAutoScript\tasks\WantedQuests\script_task.py
```

Main accepted a cooperation invitation and scheduled `WantedQuests` immediately:

```text
Invitation appearing
Accept friend invitation
Deal with invitation done
Accepted wanted quests cooperation, schedule WantedQuests
Delay task `wanted_quests` to 2026-06-05 18:29:42 (server_update=False, target=datetime.datetime(2026, 6, 5, 18, 29, 42))
[wanted_quests.scheduler.next_run] 2026-06-05 18:29:42
```

---

## Result

Passed:

- `WantedQuests` can be selected by `oas_main` scheduler when enabled.
- Accepted recognized cooperation popup now triggers the local patch path.
- The patch writes `WantedQuests.next_run` with `server_update=False`, so the call is immediate instead of delayed to a server update window.
- The patch did not require changes to `script.py`, `module/config/config.py`, or global scheduler behavior.

Remaining operational note:

- Current recognized popup types are jade, cat food, and dog food only. Sushi and gold require additional global popup assets before claiming support.
- Full downstream battle completion still depends on existing `WantedQuests` navigation/OCR behavior.
