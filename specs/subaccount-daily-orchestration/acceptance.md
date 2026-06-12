# Acceptance: Subaccount Daily Orchestration

**Workspace**: `subaccount-daily-orchestration`
**Last updated**: 2026-06-07

---

## 2026-06-07 Windows Orochi Adapter Verification

**Scope**: `SubAccountRotation` -> `Orochi`

**Environment**

- Windows repo: `C:\Users\64638\OnmyojiAutoScript`
- Main config: `oas_main`, main account `不知庭院`, adb serial `127.0.0.1:5555`
- Small config: `oas_findjade`, small account `最后的黄泉 / bmkfh1992@126.com`, adb serial `127.0.0.1:5557`
- Log file: `C:\Users\64638\OnmyojiAutoScript\log\2026-06-07_oas.txt`

**Temporary validation configuration**

- Main `Orochi` member `limit_count = 1`
- Small `SubAccountRotation` enabled with only `Orochi`, `max_accounts_per_run = 1`
- Small `Orochi` configured as `leader`, `friend_1 = 不知庭院`, `limit_count = 1`
- Small `restart.harvest_config.enable_courtyard_affairs = False` only during this isolated御魂 check, because 庭院事务 could consume the one-shot validation window before the adapter ran.

**Observed result**

- `23:08:26` `SubAccountRotation run Orochi for 最后的黄泉-月蚀长夜`
- `23:08:33` existing `Orochi` leader flow started.
- `23:09:34` invite flow started and OCR found `不知庭院`.
- `23:09:43` invite confirmation clicked.
- `23:09:46` main account accepted invite.
- `23:09:49` challenge started.
- `23:09:51` battle started.
- `23:10:17` battle won.
- `23:10:19` / `23:10:25` `Orochi count limit out`.
- `23:10:42` `SubAccountRotation captured Orochi next_run ...`.
- `23:10:42` `Scheduler: End task SubAccountRotation`.

**Acceptance decision**

- Pass. The adapter reused the existing `tasks/Orochi/script_task.py` leader/invite/battle flow.
- Pass. The small account invited the main account and completed one御魂 run.
- Pass. `SubAccountRotation` intercepted `set_next_run("Orochi", ...)`, so ordinary `orochi.scheduler.next_run` was not changed by the rotation sub-task.
- Pass. Real configs were restored after validation: `SubAccountRotation`, `FindJade`, and `Orochi` schedulers disabled for both configs as appropriate; `orochi limit_count = 30`; `restart.harvest_config.enable_courtyard_affairs = True`.

## Remaining Acceptance Items

- T010: `FindJade` current-account cooperation adapter. Static validation and Windows temporary helper configuration passed. 2026-06-07 23:45 real-device attempt reached `SubAccountRotation` with sub-task `FindJade`, then stalled during account switching before entering WantedQuests; config was restored. After the account-switch readiness patch, 2026-06-08 00:04 real-device retry reached `FindJade` and completed the no-cooperation skip path (`there is no cooperation quest`). Real-device cooperation invite is still pending. Must not call the full existing account loop.
- T011: shop daily gift package adapter. 2026-06-08 user clarified this is not `MysteryShop`; the intended flow is the normal shop gift package that advances the 50-day black daruma progress. Implemented `DailyTriflesStoreSign` as a current-account `SubAccountRotation` adapter around `DailyTrifles.run_store()`: it temporarily enables `store_sign`, temporarily sets `buy_sushi_count = -1`, and restores both values afterward so it does not run other `DailyTrifles` miscellany or buy sushi. Local and Windows `py_compile` passed. Windows helper temporary config with `--sub-task DailyTriflesStoreSign --disable-find-jade` passed and real `oas_findjade.json` remained safe. Real-device shop gift-room path is still pending. Historical `MysteryShop` adapter static validation and non-MysteryShop-day skip path passed, but that does not satisfy T011.
- T012: `Hunt` adapter. Static validation and Windows helper/import validation passed. 2026-06-08 00:27 real-device non-combat time-window skip path passed: account switching succeeded, `Today is the Kirin day`, and `Hunt.next_run` was captured by `SubAccountRotation`. Real-device Kirin/Netherworld combat path is still pending during a valid time window.
- T012A: `TalismanPass` adapter. Pass for isolated adapter path. Local and Windows `py_compile` passed. 2026-06-08 00:48-00:49 Windows real-device isolated validation passed with temporary `--disable-harvest`: account switching/login reached `SubAccountRotation run TalismanPass`, entered `page_daily`, claimed TalismanPass rewards, selected the configured `金币/勾玉` level reward, captured `TalismanPass.next_run` inside `SubAccountRotation`, and ended `SubAccountRotation`. Ordinary `talisman_pass.scheduler` remained disabled with `next_run = 2023-01-01 00:00:00`. Note: a previous validation attempt with normal harvest enabled was blocked before TalismanPass by `Harvest mail` wait timeout and app restart; real config was restored to harvest enabled and rotation disabled afterward.
- T012B: `Exploration` adapter. Local implementation and Windows `py_compile` passed. The adapter calls existing `tasks/Exploration/script_task.py`, captures `Exploration.next_run` inside `SubAccountRotation`, and ignores Exploration side-effect scheduling for `RealmRaid` and `MemoryScrolls` so the rotation does not enable out-of-scope guild/scroll tasks. 2026-06-08 first Windows real-device attempt reached `SubAccountRotation run Exploration` for the small account while main was temporarily narrowed to `Exploration` member, then failed in the existing Exploration leader branch with `AttributeError: 'int' object has no attribute 'reset'` from `wait_until_stable(..., timeout=5)`. This was fixed locally and synced to Windows as `timeout=Timer(5)` in `tasks/Exploration/solo.py`. Rerun reached `SubAccountRotation run Exploration`, logged `<<< LEADER >>>`, and crossed the previous failure point; however current small accounts are below level 54 and cannot enter hard chapter 28, so the true hard-28 invite/battle path is blocked by account level. Configs were restored to safe state afterward. Run count/limit time must remain controlled by existing `exploration` config.
- T012C: `AreaBoss` adapter. Code-level implementation added on 2026-06-08. `SubAccountRotation` calls the existing `tasks/AreaBoss/script_task.py` flow, captures `set_next_run("AreaBoss", ...)` inside the rotation adapter, and restores the original in-memory `area_boss.general_battle.lock_team_enable` value after the existing AreaBoss task forces it to `False`. Local `py_compile` passed. Real-device AreaBoss validation is intentionally deferred for the unified validation pass.
- Optional shop extension: consignment house weekly exchange for one configured shikigami shard. Existing `RichMan.consignment` currently only buys sale tickets, so this needs separate UI/assets/config assessment before being counted as implemented.
