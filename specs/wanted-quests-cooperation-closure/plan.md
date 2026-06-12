# Implementation Plan: Wanted Quests Cooperation Closure

**Workspace**: `wanted-quests-cooperation-closure` | **Date**: 2026-06-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/wanted-quests-cooperation-closure/spec.md`

---

## Summary

让大号在接受小号悬赏协作后，明确触发 `WantedQuests` 的调度闭环。因为本仓库是基于开源脚本维护的本地 patch，方案优先控制改动面：不改全局 scheduler，不新增强制任务队列，只在突发邀请处理处做小范围协作识别，并用配置脚本保证大号实例的 `WantedQuests` 可被正常调度。

---

## Architecture Overview

```text
小号 FindJade/WantedQuestsEx
  -> 发出悬赏协作邀请
  -> 大号 BaseTask._burst() 检测弹窗并按 emergency 策略接受
  -> 若弹窗被识别为悬赏协作，写入 WantedQuests.next_run = now
  -> Scheduler 在 WantedQuests.scheduler.enable=true 时将其作为待执行任务
  -> WantedQuests 消费已接受的协作任务并执行
```

---

## Producer-Consumer Matrix

| Producer | Artifact | Consumer | Consumption Proof |
|---|---|---|---|
| 小号 `WantedQuests.all_cooperation_invite()` | 游戏内协作邀请弹窗 | 大号 `BaseTask._burst()` | 大号日志出现 `Invitation appearing` 和接受动作 |
| 大号 `BaseTask._burst()` | 已接受的协作任务 + 调度请求 | 大号 scheduler | 配置中 `wanted_quests.scheduler.next_run` 为当前时间，日志出现协作调度记录 |
| 大号 scheduler | `WantedQuests` pending task | `tasks/WantedQuests/script_task.py` | 日志进入 `WANTEDQUESTS`，并出现追踪/执行悬赏流程 |

**孤儿 artifact 处理**: 当前断点是“已接受的协作任务”缺少稳定 consumer。本 feature 的目标就是补齐该 consumer 调度证据。

---

## Key Design Decisions

### Decision 1: 使用最小侵入的 `next_run` 触发，不改 scheduler 语义

- **背景**: 现有 `_burst()` 在接受邀请后调用 `set_next_run(task='WantedQuests', target=now)`，但用户观察到大号接受后未执行。
- **选项**:
  - A: 保持现状，任何 accept 都写 `WantedQuests.next_run`。改动最少，但会让普通组队邀请误触发悬赏。
  - B: 在 `_burst()` 中先识别协作悬赏类型，只有勾协/粮协等协作邀请被接受后才写 `WantedQuests.next_run=now`。不改变 scheduler、`task_call` 或任务启用语义。
  - C: 新增强制任务机制，即使 `WantedQuests.scheduler.enable=false` 也执行。闭环更强，但需要改核心调度语义，后续同步上游时冲突风险高。
  - D: 立即中断当前任务并执行 `WantedQuests`。响应最快，但破坏大号当前任务稳定性。
- **结论**: 选择 B。它符合“尽快调度但不强行抢占”的需求，也最适合本地 patch 长期维护。
- **影响**: `WantedQuests.scheduler.enable` 必须作为大号配置前提；实现不承诺绕过用户禁用的任务。
- **来源**: 当前代码：`module/config/config.py::update_scheduler` 只收集 enabled 任务，`module/config/config.py::task_call` 只写 `next_run`，`tasks/base_task.py::_burst` 当前对所有 accept 都触发悬赏。

### Decision 2: 配置脚本负责检查大号调度可达性

- **背景**: 小号 `FindJade` 已遇到过 Filter 调度规则不包含任务导致 `No task pending` 的问题。
- **选项**:
  - A: 手工在 UI 配置。
  - B: 增加一个脚本检查 `oas_main` 的 `WantedQuests` 调度可达性，包括 `scheduler.enable`、`next_run` 可写、调度规则是否包含 `WantedQuests`。
- **结论**: 选择 B，作为后续实现任务的一部分。脚本可以只检查并提示，也可以选择修正。
- **影响**: 降低未来 agent 和用户手工配置成本。
- **来源**: `scripts/configure_findjade_accounts.py` 已采用类似策略。

---

## Module Design

### Module: `tasks/base_task.py`

**职责**: 处理游戏内突发邀请弹窗。

**改动概述**: 在 `_burst()` 点击接受前记录本次弹窗是否为悬赏协作类型；点击接受后，如果是悬赏协作类型，则写入 `WantedQuests.next_run=now`。保留 `detect_record` 恢复逻辑。

**关键行为**:

```text
if accepted invitation and invitation is recognized jade/food cooperation:
    set WantedQuests.next_run = now
else:
    do not call WantedQuests
```

**注意事项**:

- 不能让普通组队邀请触发 `WantedQuests`。
- 当前实现只使用 `GlobalGameAssets` 已有的勾玉、猫粮、狗粮弹窗素材；体力、金币不在 MVP 自动识别范围内。
- 如果当前截图中无法识别协作类型，保守回退到现有行为或只在 `friend_invitation` 为协作策略时触发。
- 不修改 `module/config/config.py` 或全局 scheduler；禁用的 `WantedQuests` 由配置检查处理。

### Module: configuration helper

**职责**: 检查 `oas_main` 是否允许协作悬赏被调度。

**改动概述**: 可新增或扩展脚本，验证 `wanted_quests.scheduler.enable`、`wanted_quests.scheduler.next_run`、`script.optimization.schedule_rule`、priority/filter 列表是否允许 `WantedQuests` 进入 pending。脚本优先输出检查结果；是否自动修正应由显式参数控制。

---

## Risks and Tradeoffs

- 仍不抢占当前任务，所以如果大号在长时间任务中，`WantedQuests` 会等当前任务结束后执行。
- 游戏邀请弹窗的图像类型识别可能不完整，需要从日志和截图验证是否能区分普通邀请和协作邀请。
- 如果 `WantedQuests.scheduler.enable=false`，本 feature 不会绕过用户禁用；必须通过配置脚本或 UI 启用。
- 如果 `WantedQuests` 自身 OCR/路径失败，本 feature 只负责把它调度起来，不保证所有悬赏都能完成。

---

## Verification Strategy

- 单元级：检查 `_burst()` 只在协作悬赏被接受时写入 `WantedQuests.next_run=now`。
- 配置级：运行检查脚本确认 `oas_main` 中 `WantedQuests.scheduler.enable=true`，且不会被调度规则排除。
- 实机级：小号发勾协，大号接受后观察日志中出现协作调度记录和后续 `WANTEDQUESTS`。

---

## Stage Readiness

- 是否需要 `data-model.md`：不需要。没有新增持久实体，只调整调度闭环。
- 下一步建议：`tasks`
- 阻塞项：无。

---

## Design Artifacts

| 产物 | 是否需要 | 说明 |
|------|---------|------|
| plan.md | 必须 | 当前文件 |
| data-model.md | 不需要 | 没有新增实体模型 |
| tasks.md | 后续阶段生成 | 拆具体实现步骤 |
| acceptance.md | 后续阶段生成 | 记录实机验证结论 |
