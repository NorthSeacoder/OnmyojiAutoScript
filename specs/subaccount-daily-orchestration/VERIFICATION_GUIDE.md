# Real-Device Verification Guide

**Date**: 2026-06-12  
**Branch**: `oas-small-account-rotation`  
**Environment**: Windows PC (C:\Users\64638\OnmyojiAutoScript) via SSH

---

## Prerequisites

### 1. Sync Code to Windows
```bash
# On Mac
git push origin oas-small-account-rotation

# On Windows (via ssh win)
cd C:\Users\64638\OnmyojiAutoScript
git fetch origin
git checkout oas-small-account-rotation
git pull origin oas-small-account-rotation
```

### 2. Verify Critical Fixes
```bash
# On Windows
venv\Scripts\python.exe -m py_compile tasks/SubAccountRotation/script_task.py
```

Expected: No syntax errors

### 3. Environment Check
- Main emulator: 127.0.0.1:5555 (不知庭院)
- Small emulator: 127.0.0.1:5557 (最后的黄泉 / 破晓的森林)
- Both emulators running and ADB connected

---

## Verification Sequence

### ✅ Phase 1: DailyTriflesStoreSign (优先级1)

**Time required**: 5-10 minutes  
**Prerequisites**: Daily store gift not claimed today

```bash
# On Windows
bash scripts/verify_daily_trifles_store_sign.sh
venv\Scripts\python.exe server.py --config oas_findjade --host 0.0.0.0 --port 22271
```

**Validates**:
- Issue #3 fix: DailyTrifles set_next_run interception
- Config restoration: store_sign and buy_sushi_count

**Success criteria**:
- [ ] Log: "SubAccountRotation captured DailyTrifles next_run"
- [ ] Config: daily_trifles.scheduler.next_run unchanged
- [ ] Config: store_sign and buy_sushi_count restored
- [ ] History: new DailyTriflesStoreSign entry in sub_account_rotation.history_list

---

### ✅ Phase 2: AreaBoss (优先级1)

**Time required**: 10-15 minutes  
**Prerequisites**: Time window 06:00-24:00, AreaBoss tickets available

```bash
# On Windows (check time first)
bash scripts/verify_area_boss.sh
venv\Scripts\python.exe server.py --config oas_findjade --host 0.0.0.0 --port 22271
```

**Validates**:
- Issue #1 fix: lock_team_enable restoration even when TaskEnd raised
- Config restoration: area_boss.general_battle.lock_team_enable

**Success criteria**:
- [ ] Log: "SubAccountRotation captured AreaBoss next_run"
- [ ] Config: area_boss.scheduler.next_run unchanged
- [ ] Config: lock_team_enable restored to original value
- [ ] History: new AreaBoss entry in sub_account_rotation.history_list

---

### ✅ Phase 3: FindJade Cooperation Path (优先级2)

**Time required**: 15-20 minutes  
**Prerequisites**: Small account has cooperation quests (jade/cat food/dog food)

```bash
# On Windows
bash scripts/verify_find_jade_cooperation.sh

# Manual step: Edit config/oas_main.json
# Set: wanted_quests.wanted_quests_config.cooperation_only = true

# Run both instances
venv\Scripts\python.exe server.py --config oas_main --host 0.0.0.0 --port 22270
venv\Scripts\python.exe server.py --config oas_findjade --host 0.0.0.0 --port 22271
```

**Validates**:
- Issue #2 fix: WantedQuests set_next_run interception from FindJade
- Main cooperation_only mode: accepts cooperation without searching own quests
- End-to-end cooperation flow

**Success criteria**:
- [ ] Small log: "SubAccountRotation captured WantedQuests next_run from FindJade"
- [ ] Main config: wanted_quests.scheduler.next_run unchanged
- [ ] Small config: FindJade history updated
- [ ] Both accounts: cooperation battle completed

---

## After Verification

### Record Results

Update `specs/subaccount-daily-orchestration/acceptance.md`:

```markdown
## 2026-06-12 Real-Device Verification Results

### DailyTriflesStoreSign
- **Status**: [PASS/FAIL]
- **Timestamp**: [HH:MM:SS]
- **Notes**: [observations]

### AreaBoss
- **Status**: [PASS/FAIL]
- **Timestamp**: [HH:MM:SS]
- **Notes**: [observations]

### FindJade Cooperation
- **Status**: [PASS/FAIL]
- **Timestamp**: [HH:MM:SS]
- **Notes**: [observations]
```

### Restore Configs

```bash
# If needed
cp config/oas_findjade.before_*_verification.json config/oas_findjade.json
cp config/oas_main.before_cooperation_verification.json config/oas_main.json
```

---

## Remaining Verification Items

### Phase 4: Hunt Combat Path (需等时间窗口)
- **Blocker**: Need to wait for Hunt time window
- **麒麟**: Available all day
- **阴界之门**: Opens at 19:00

### Phase 5: Exploration Hard-28 (需小号升级)
- **Blocker**: Small accounts below level 54
- **Options**: Level up small accounts or use different accounts

---

## Troubleshooting

### Issue: Account switch fails
- Check adb connection: `adb devices`
- Verify emulator serial in config
- Check account credentials (email/password)

### Issue: Config not restored
- Check backup files exist
- Manually restore from backup
- Verify finally blocks executed (check logs)

### Issue: Scheduler pollution
- Check `*_scheduler.next_run` values in config
- Look for "SubAccountRotation captured * next_run" in logs
- If polluted, restore from backup and re-verify

---

## Next Steps After All Pass

1. Update `specs/subaccount-daily-orchestration/acceptance.md` with all results
2. Commit acceptance updates
3. Proceed to SDD Verify stage completion
4. Consider merge to master or continue with remaining features
