# Phase 1 Real-Device Verification Guide

**Feature**: PassiveCooperationResponse - Orochi Member Mode  
**Date**: 2026-06-14  
**Tester**: [Your Name]

---

## Pre-requisites

### Environment Setup
- [ ] Two OAS instances ready (main + small account)
- [ ] Both accounts in same game server
- [ ] Small account friends with main account
- [ ] Both accounts have Orochi unlocked

### Configuration Files

**Main Account** (`config/oas_main.json` or similar):
```json
{
  "passive_cooperation_response": {
    "scheduler": {
      "enable": true,
      "priority": 999,
      "next_run": "2023-01-01 00:00:00"
    },
    "passive_config": {
      "orochi": {
        "enable": true,
        "max_accept_count": -1,
        "allowed_inviters": [],
        "buff_enable": true
      },
      "exploration": {
        "enable": false
      },
      "wanted_quests": {
        "enable": false
      }
    }
  }
}
```

**Small Account** (`config/oas_findjade.json` or similar):
```json
{
  "sub_account_rotation": {
    "scheduler": {
      "enable": true,
      "priority": 10,
      "next_run": "2023-01-01 00:00:00"
    },
    "rotation_config": {
      "enabled_sub_tasks": ["Orochi"]
    }
  },
  "orochi": {
    "scheduler": {
      "enable": false
    },
    "orochi_config": {
      "user_status": "leader",
      "limit_count": 3,
      "soul_buff_enable": false,
      "friend_1": "不知庭院"  // Main account name
    }
  }
}
```

---

## Test Scenarios

### Scenario 1: Single Invite Flow (Basic)

**Objective**: Verify main account can detect, accept, and complete one Orochi invite

**Steps**:
1. Start main account OAS
2. Verify log shows: `"PassiveCooperationResponse: Start listening for invites"`
3. Verify log shows: `"Listening for: orochi"`
4. Start small account OAS
5. Wait for small account to send Orochi invite

**Expected Behavior**:
- [ ] Main account log: `"Detected orochi invite from [inviter_name]"`
- [ ] Main account log: `"Accepting orochi invite from [inviter_name]"`
- [ ] Main account log: `"Clicked accept button"` (or similar)
- [ ] Main account log: `"Successfully entered room"`
- [ ] Main account log: `"Orochi member mode: user_status=MEMBER, buff_enable=true"`
- [ ] Main account log: `"PassiveCooperationResponse captured Orochi set_next_run (ignored)"`
- [ ] Main account enters battle and completes it
- [ ] Main account log: `"Orochi member execution completed successfully"`
- [ ] Main account log: `"Completed orochi invite (total: 1)"`
- [ ] Main account returns to main page
- [ ] Main account continues listening (loop doesn't break)

**Failure Cases**:
- Invite not detected → Check asset recognition
- Accept failed → Check button click timing
- Battle not started → Check room entry logic
- Config not restored → Check `finally` block execution

---

### Scenario 2: Buff Management Verification

**Objective**: Verify buff auto-enabled when `buff_enable=true`

**Prerequisites**:
- Main account has sufficient soul buff items
- `passive_config.orochi.buff_enable = true`

**Steps**:
1. Before test: Note current soul buff count in game
2. Run Scenario 1
3. During battle: Check game UI for soul buff icon

**Expected Behavior**:
- [ ] Main account log: `"Orochi member mode: ... buff_enable=True"`
- [ ] Game UI shows soul buff active during battle
- [ ] Soul buff count decreased by 1 after battle
- [ ] Main account log: `"Orochi config restored: ... buff_enable=[original_value]"`

**Variation**:
- Set `buff_enable=false`, verify no buff operations

---

### Scenario 3: Multiple Invite Flow

**Objective**: Verify main account can handle multiple sequential invites

**Configuration**:
- Small account: `orochi.limit_count = 3`
- Main account: `max_accept_count = -1` (unlimited)

**Steps**:
1. Run Scenario 1
2. After first battle completes, small account sends 2nd invite
3. After second battle completes, small account sends 3rd invite

**Expected Behavior**:
- [ ] Main accepts all 3 invites sequentially
- [ ] Main account log shows `"total: 1"`, `"total: 2"`, `"total: 3"`
- [ ] Config restoration works correctly after each invite
- [ ] No memory leaks or state corruption

---

### Scenario 4: Accept Count Limit

**Objective**: Verify `max_accept_count` limit enforcement

**Configuration**:
- Small account: `orochi.limit_count = 3`
- Main account: `max_accept_count = 2`

**Steps**:
1. Run Scenario 3 setup
2. Observe behavior on 3rd invite

**Expected Behavior**:
- [ ] Main accepts invites #1 and #2
- [ ] On invite #3:
  - Main log: `"Detected orochi invite"`
  - Main log: `"Rejected invite: orochi accept count reached limit (2/2)"`
  - Main does NOT accept invite
  - Main continues listening (loop doesn't break)

---

### Scenario 5: Whitelist Filter

**Objective**: Verify `allowed_inviters` whitelist enforcement

**Configuration**:
- Main account: `allowed_inviters = ["某个不存在的昵称"]`
- Small account: Normal setup

**Steps**:
1. Run Scenario 1 setup

**Expected Behavior**:
- [ ] Main log: `"Detected orochi invite from [inviter_name]"`
- [ ] Main log: `"Rejected invite: Inviter '[inviter_name]' not in whitelist"`
- [ ] Main does NOT accept invite
- [ ] Main continues listening

**Variation**:
- Set `allowed_inviters = ["[small_account_name]"]`, verify invite accepted

---

### Scenario 6: Scheduler Non-Pollution

**Objective**: Verify `orochi.scheduler.next_run` not modified by passive response

**Prerequisites**:
- Main account: `orochi.scheduler.enable = true`, `next_run` set to future date

**Steps**:
1. Before test: Note `orochi.scheduler.next_run` value in config file
2. Run Scenario 1
3. After test: Check `orochi.scheduler.next_run` value

**Expected Behavior**:
- [ ] Main account log: `"PassiveCooperationResponse captured Orochi set_next_run (ignored)"`
- [ ] Config file `orochi.scheduler.next_run` UNCHANGED
- [ ] Main account does NOT trigger normal Orochi task

---

### Scenario 7: Config Restoration on Exception

**Objective**: Verify config restored even when exception occurs

**Steps**:
1. Modify code to inject artificial exception in `_execute_orochi_member()`
2. Run Scenario 1

**Expected Behavior**:
- [ ] Exception logged
- [ ] Main account log: `"Orochi config restored: user_status=[original], buff_enable=[original]"`
- [ ] Config values verified by checking `config.orochi.orochi_config.user_status`
- [ ] Main continues listening (doesn't crash)

---

## Logging Checklist

Key log patterns to verify:

**Startup**:
```
PassiveCooperationResponse: Start listening for invites
Listening for: orochi
```

**Invite Detection**:
```
Detected invite popup
Current page for invite inference: [page_name]
Invite detected: type=orochi, inviter=[name]
Detected orochi invite from [name]
```

**Validation**:
```
Accepting orochi invite from [name]
Attempting to accept invite
Clicked accept button
Successfully entered room
```

**Execution**:
```
Executing orochi member mode
Orochi member mode: user_status=MEMBER, buff_enable=True
PassiveCooperationResponse captured Orochi set_next_run (ignored)
Orochi member execution completed successfully
Completed orochi invite (total: 1)
```

**Return to Standby**:
```
Returning to standby state
Orochi config restored: user_status=[original], buff_enable=[original]
```

---

## Issue Tracking Template

**Issue #**: [Number]  
**Scenario**: [Which scenario]  
**Severity**: Critical / High / Medium / Low  
**Description**: [What went wrong]  
**Expected**: [What should happen]  
**Actual**: [What actually happened]  
**Logs**: [Relevant log snippets]  
**Root Cause**: [Analysis]  
**Resolution**: [How to fix]  
**Status**: Open / Fixed / Verified

---

## Success Criteria

Phase 1 passes if:
- [ ] All 7 scenarios pass
- [ ] No Critical or High severity issues
- [ ] Config restoration verified in all cases
- [ ] Scheduler non-pollution verified
- [ ] Buff management works as configured
- [ ] Main account can handle multiple sequential invites
- [ ] Validation logic (count limit, whitelist) works correctly

---

## Post-Verification Actions

1. Update `acceptance.md` with:
   - Test execution date/time
   - Pass/Fail status for each scenario
   - Discovered issues and resolutions
   - Screenshots or video recordings (if applicable)

2. If issues found:
   - Document in acceptance.md
   - Create fix commits
   - Re-run affected scenarios

3. If all scenarios pass:
   - Mark Phase 1 as ✅ VERIFIED
   - Proceed to Phase 2 planning

---

## Notes Section

[Add any observations, edge cases discovered, or recommendations for future improvements]
