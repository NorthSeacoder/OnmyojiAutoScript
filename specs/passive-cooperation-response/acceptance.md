# Acceptance: Passive Cooperation Response

**Workspace**: `passive-cooperation-response`
**Created**: 2026-06-13
**Status**: Phase 1 Implementation Complete, Awaiting Real-Device Verification

---

## Implementation Summary

### Phase 1: 基础架构和御魂邀请 (MVP)

**Status**: ✅ Implementation Complete (9/12 tasks, 75%)  
**Completed**: 2026-06-13  
**Total Effort**: 42 hours

---

## Completed Tasks

### T1.1 - 配置模型实现 ✅
**Completed**: 2026-06-13  
**Files**:
- `tasks/PassiveCooperationResponse/config.py`
- `module/config/config_model.py` (added passive_cooperation_response field)
- `tasks/PassiveCooperationResponse/config/passive_cooperation_response.yaml`

**Verification**:
- ✅ Config loads without errors
- ✅ Nested access (`config.passive_cooperation_response.passive_config.orochi.enable`) works
- ✅ Python syntax validation passed

---

### T1.2 - 邀请检测模块框架 ✅
**Completed**: 2026-06-13  
**Files**:
- `tasks/PassiveCooperationResponse/invite_detector.py`

**Implementation**:
- ✅ `InviteInfo` dataclass defined
- ✅ `InviteDetector` class skeleton created
- ✅ Methods: `detect_invite()`, `_infer_invite_type()`, `accept_invite()`

---

### T1.3 - 邀请弹窗资产准备 ✅
**Completed**: 2026-06-13  
**Files**:
- `tasks/PassiveCooperationResponse/assets/__init__.py`

**Implementation**:
- ✅ Asset class `PassiveCooperationResponseAssets` defined
- ✅ Reuses `GeneralInvite` component assets (zero duplication)
- ✅ Asset mappings:
  - `INVITE_POPUP` → `I_I_ACCEPT`
  - `INVITE_ACCEPT_BUTTON` → `I_I_ACCEPT`
  - `INVITE_SURE_BUTTON` → `I_GI_SURE`
  - `INVITER_NAME_REGION_1/2` → `O_FRIEND_NAME_1/2`

---

### T1.4 - 邀请检测逻辑实现 ✅
**Completed**: 2026-06-13  
**Files**:
- `tasks/PassiveCooperationResponse/invite_detector.py`

**Implementation**:
- ✅ `detect_invite()`: Detect popup → infer type → parse inviter → return InviteInfo
- ✅ `_infer_invite_type()`: Context-based inference using `ui_get_current_page()`
  - Main page → "orochi"
  - Explore page → "exploration"
  - Wanted page → "wanted_quests"
  - Unknown → "unknown"
- ✅ `accept_invite()`: Click accept buttons with retry logic (max 10 attempts)
- ✅ `_parse_inviter_name()`: Placeholder returns "Unknown" (OCR in Phase 2)

**Known Limitations**:
- Inviter name OCR not implemented (always returns "Unknown")
- Invite type inference based on page heuristic (no content OCR)

---

### T1.5 - 主任务框架搭建 ✅
**Completed**: 2026-06-13  
**Files**:
- `tasks/PassiveCooperationResponse/script_task.py`

**Implementation**:
- ✅ `ScriptTask` class created
- ✅ `__init__`: Initialize InviteDetector and accept_counts tracker
- ✅ `run()`: Main loop skeleton
- ✅ `_get_enabled_tasks()`: List enabled passive configs
- ✅ `_execute_task()`: Dispatcher to task-specific executors

---

### T1.6 - 邀请验证逻辑实现 ✅
**Completed**: 2026-06-13  
**Files**:
- `tasks/PassiveCooperationResponse/script_task.py`
- `tasks/PassiveCooperationResponse/test_invite_validation.py`

**Implementation**:
- ✅ `_should_accept_invite()`: 4-stage validation
  1. Task type enabled check
  2. Accept count limit check (`max_accept_count`: -1=unlimited, 0=disabled, n=limit)
  3. Inviter whitelist check (empty list = accept all)
  4. Cooperation type filter (wanted_quests only)
- ✅ `_get_rejection_reason()`: Human-readable rejection messages

**Unit Test Results**: ✅ 11/11 scenarios passed
- Task disabled
- Accept count limits (0, -1, n, at limit, under limit)
- Whitelist (empty, match, no match)
- Cooperation type filter (allowed, disallowed)
- Combined conditions

---

### T1.7 - 御魂 Member 模式接口调研 ✅
**Completed**: 2026-06-13  
**Documentation**:
- `specs/passive-cooperation-response/T1.7-orochi-member-research.md`

**Research Conclusions**:
- ✅ Confirmed: Orochi `run()` auto-dispatches to `run_member()` based on `user_status`
- ✅ Decision: Use `user_status=MEMBER` + `run()` (not direct `run_member()`)
- ✅ Rationale: Reuses complete flow including buff management, exception handling, timeout
- ✅ Buff management: Automatically handled in `run()` entry/exit

---

### T1.8 - 御魂 Member 执行逻辑 ✅
**Completed**: 2026-06-13  
**Files**:
- `tasks/PassiveCooperationResponse/script_task.py`

**Implementation**:
- ✅ `_execute_orochi_member()`: Complete implementation
  1. Save original config (`user_status`, `soul_buff_enable`)
  2. Set `user_status=MEMBER` + apply passive buff config
  3. Instantiate OrochiTask and intercept `set_next_run`
  4. Call `runner.run()` → auto-dispatches to `run_member()`
  5. Restore config in `finally` block
- ✅ Exception handling:
  - `TaskEnd` → return True (normal completion)
  - `RequestHumanTakeover` → propagate (critical errors)
  - Other exceptions → log and return False
- ✅ Detailed logging at each step

**Architecture Compliance**:
- ✅ Patch-first: Zero modification to existing Orochi code
- ✅ Adapter pattern: Independent task wrapper
- ✅ Interception: `set_next_run` captured and ignored
- ✅ Config isolation: Temporary mutation + guaranteed restoration

---

### T1.9 - 主循环实现 ✅
**Completed**: 2026-06-13  
**Files**:
- `tasks/PassiveCooperationResponse/script_task.py`

**Implementation**:
- ✅ `run()`: Complete listening loop
  1. Check enabled tasks → exit if none
  2. Loop: Screenshot → detect_invite() → validate → accept → execute
  3. Update accept_counts on success
  4. Return to main page after each invite
- ✅ Integration: All modules connected (detector, validator, executor)
- ✅ Polling interval: 1 second

**Flow**:
```
Start → Check enabled tasks
  ↓
Loop:
  Screenshot
  → detect_invite()
  → No invite? sleep(1), continue
  → Validate (_should_accept_invite)
  → Rejected? log reason, continue
  → Accept (detector.accept_invite)
  → Failed? log warning, continue
  → Execute (_execute_task)
  → Update accept_counts
  → ui_goto_main()
  → Continue loop
```

---

## Pending Tasks (Awaiting Real-Device Verification)

### T1.10 - 端到端测试（御魂） ⏳
**Scheduled**: 2026-06-14 上午  
**Dependencies**: T1.9 ✅

**Test Plan**:
1. Configuration:
   - Main account: `passive_cooperation_response.passive_config.orochi.enable=true`
   - Small account: `SubAccountRotation` with Orochi sub-task enabled
2. Test Flow:
   - Start main account OAS (PassiveCooperationResponse enabled)
   - Start small account OAS (SubAccountRotation triggers Orochi invite)
   - Observe logs and game UI
3. Verification Checkpoints:
   - [ ] Main detects invite and logs it
   - [ ] Main accepts invite
   - [ ] Main enters Orochi battle
   - [ ] Battle completes
   - [ ] Main returns to standby (main page)
   - [ ] Main continues listening for next invite
   - [ ] `orochi.scheduler.next_run` NOT modified
   - [ ] Config restoration verified

**Risk**: Potential asset recognition issues, timing issues, edge cases

---

### T1.11 - 加成管理验证 ⏳
**Scheduled**: 2026-06-14 上午  
**Dependencies**: T1.8 ✅

**Status**: Implementation already complete in T1.8  
**Implementation Details**:
- Buff management reuses Orochi's `run()` built-in logic
- `passive_config.orochi.buff_enable` → `orochi_config.soul_buff_enable`
- Orochi `run()` automatically calls `open_buff()` + `soul(is_open=True)` before member mode
- Orochi `run()` automatically calls `open_buff()` + `soul(is_open=False)` after member mode

**Verification Plan**:
- [ ] `buff_enable=true`: Verify buff auto-enabled (check game UI + logs)
- [ ] `buff_enable=false`: Verify no buff operations
- [ ] Buff already enabled: Verify no duplicate clicks

---

### T1.12 - Phase 1 文档更新 ⏳
**Scheduled**: After T1.10/T1.11 verification  
**Dependencies**: T1.10, T1.11

**Tasks**:
1. Update this `acceptance.md` with real-device verification results
2. Document discovered issues and resolutions
3. Update `CLAUDE.md` or `AGENTS.md` with:
   - Feature description
   - Configuration guide
   - Usage examples
   - Known limitations

---

## Architecture Review

### Design Principles (Patch-first Strategy)

✅ **Adapter pattern over injection**  
- PassiveCooperationResponse is independent task
- Zero modification to Orochi/Exploration/WantedQuests code

✅ **Interception over rewrite**  
- `set_next_run` intercepted and ignored
- Scheduler not polluted

✅ **Temporary config mutation with restoration**  
- Config changes isolated to execution scope
- `finally` block guarantees restoration

✅ **Narrow entry points**  
- Calls existing `run()` via `user_status` switch
- Reuses complete member flow

✅ **Guard conditions at task boundaries**  
- Validation at PassiveCooperationResponse entry
- No deep modification in existing tasks

---

## Known Limitations (Phase 1 MVP)

1. **Inviter name OCR**: Not implemented, always returns "Unknown"
   - Impact: Whitelist filtering requires placeholder value
   - Mitigation: Use empty whitelist (accept all) for Phase 1
   - Resolution: Implement OCR in Phase 2

2. **Invite type inference**: Page-based heuristic only
   - Impact: May misidentify invite type in edge cases
   - Mitigation: Main page defaults to Orochi (most common)
   - Resolution: Add content OCR in Phase 2

3. **Exploration/WantedQuests**: Placeholder stubs
   - Impact: Only Orochi invites supported in Phase 1
   - Resolution: Implement in Phase 2/3

4. **Accept counts persistence**: Not saved across restarts
   - Impact: Counts reset when OAS restarts
   - Resolution: Add persistence in Phase 4 (enhancement)

---

## Next Steps

1. **2026-06-14 上午**: Real-device verification (T1.10)
2. **Post-verification**: Update this document with results
3. **Phase 2**: Exploration invite support (if Phase 1 passes)
4. **Phase 3**: WantedQuests cooperation support

---

## Reference

- Spec: `specs/passive-cooperation-response/spec.md`
- Plan: `specs/passive-cooperation-response/plan.md`
- Tasks: `specs/passive-cooperation-response/tasks.md`
- Research: `specs/passive-cooperation-response/T1.7-orochi-member-research.md`
