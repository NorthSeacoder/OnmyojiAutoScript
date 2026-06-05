# Implementation Plan: Wanted Quests Cooperation Closure

**Workspace**: `wanted-quests-cooperation-closure` | **Date**: 2026-06-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/wanted-quests-cooperation-closure/spec.md`

---

## Summary

让大号在接受小号悬赏协作后，明确触发 `WantedQuests` 的调度闭环。推荐方案是在现有 `_burst()` 接受逻辑中使用更明确的任务调用语义，并配套配置检查，避免只设置 `next_run` 后被调度规则或启用状态吞掉。

---

## Architecture Overview

```text
小号 FindJade/WantedQuestsEx
  -> 发出悬赏协作邀请
  -> 大号 BaseTask._burst() 检测弹窗并按 emergency 策略接受
  -> 大号 Config.task_call("WantedQuests", force_call=True)
  -> Scheduler 将 WantedQuests 作为待执行任务
  -> WantedQuests 消费已接受的协作任务并执行
```

---

## Producer-Consumer Matrix

| Producer | Artifact | Consumer | Consumption Proof |
|---|---|---|---|
| 小号 `WantedQuests.all_cooperation_invite()` | 游戏内协作邀请弹窗 | 大号 `BaseTask._burst()` | 大号日志出现 `Invitation appearing` 和接受动作 |
| 大号 `BaseTask._burst()` | 已接受的协作任务 + 调度请求 | 大号 scheduler | 配置中 `wanted_quests.scheduler.next_run` 为当前时间，日志出现 `Task call: wanted_quests` |
| 大号 scheduler | `WantedQuests` pending task | `tasks/WantedQuests/script_task.py` | 日志进入 `WANTEDQUESTS`，并出现追踪/执行悬赏流程 |

**孤儿 artifact 处理**: 当前断点是“已接受的协作任务”缺少稳定 consumer。本 feature 的目标就是补齐该 consumer 调度证据。

---

## Key Design Decisions

### Decision 1: 使用 `task_call` 而不是只写 `set_next_run`

- **背景**: 现有 `_burst()` 在接受邀请后调用 `set_next_run(task='WantedQuests', target=now)`，但用户观察到大号接受后未执行。
- **选项**:
  - A: 保持现状，只让用户调整配置。改动最少，但无法防止 enable/filter 等配置吞掉调度。
  - B: 在接受后调用 `self.config.task_call('WantedQuests', force_call=True)`。语义更明确，会保存配置，并可绕过任务未启用问题。
  - C: 立即中断当前任务并执行 `WantedQuests`。响应最快，但破坏大号当前任务稳定性。
- **结论**: 选择 B。它符合“尽快调度但不强行抢占”的需求。
- **影响**: `_burst()` 需要区分接受的是协作类邀请，避免普通组队邀请触发悬赏。
- **来源**: 当前代码：`module/config/config.py::task_call`，`tasks/base_task.py::_burst`。

### Decision 2: 配置脚本负责检查大号调度规则

- **背景**: 小号 `FindJade` 已遇到过 Filter 调度规则不包含任务导致 `No task pending` 的问题。
- **选项**:
  - A: 手工在 UI 配置。
  - B: 增加一个脚本检查 `oas_main` 的 `WantedQuests` 调度可达性。
- **结论**: 选择 B，作为后续实现任务的一部分。脚本可以只检查并提示，也可以选择修正。
- **影响**: 降低未来 agent 和用户手工配置成本。
- **来源**: `scripts/configure_findjade_accounts.py` 已采用类似策略。

---

## Module Design

### Module: `tasks/base_task.py`

**职责**: 处理游戏内突发邀请弹窗。

**改动概述**: 在 `_burst()` 点击接受后，如果邀请类型是悬赏协作类型，则调用 `self.config.task_call('WantedQuests', force_call=True)`。保留 `detect_record` 恢复逻辑。

**关键行为**:

```text
if accepted invitation and invitation is jade/food/sushi/gold cooperation:
    config.task_call("WantedQuests", force_call=True)
else:
    do not call WantedQuests
```

**注意事项**:

- 不能让普通组队邀请触发 `WantedQuests`。
- 如果当前截图中无法识别协作类型，保守回退到现有行为或只在 `friend_invitation` 为协作策略时触发。

### Module: configuration helper

**职责**: 检查 `oas_main` 是否允许协作悬赏被调度。

**改动概述**: 可新增或扩展脚本，验证 `wanted_quests.scheduler`、`script.optimization.schedule_rule`、priority/filter 列表是否会吞掉 `WantedQuests`。

---

## Risks and Tradeoffs

- 仍不抢占当前任务，所以如果大号在长时间任务中，`WantedQuests` 会等当前任务结束后执行。
- 游戏邀请弹窗的图像类型识别可能不完整，需要从日志和截图验证是否能区分普通邀请和协作邀请。
- 如果 `WantedQuests` 自身 OCR/路径失败，本 feature 只负责把它调度起来，不保证所有悬赏都能完成。

---

## Verification Strategy

- 单元级：检查 `_burst()` 接受协作时调用 `task_call('WantedQuests', force_call=True)`。
- 配置级：运行检查脚本确认 `oas_main` 中 `WantedQuests` 不会被 Filter 排除。
- 实机级：小号发勾协，大号接受后观察日志中出现 `Task call` 和后续 `WANTEDQUESTS`。

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
