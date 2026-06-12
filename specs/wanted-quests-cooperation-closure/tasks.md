# Tasks: Wanted Quests Cooperation Closure

**Workspace**: `wanted-quests-cooperation-closure` | **Date**: 2026-06-05
**Input**: `specs/wanted-quests-cooperation-closure/spec.md` + `plan.md`
**Prerequisites**: spec.md, plan.md

---

## 执行原则

- 先修大号接受协作后的调度闭环，再推进小号日常编排。
- 不抢占大号当前任务；只保证当前任务结束后 scheduler 能看到 `WantedQuests`。
- 不改变普通组队邀请的行为。
- 本仓库是上游开源脚本的本地 patch；实现优先控制改动面，不改全局 scheduler 或 `task_call` 语义。

---

## Phase 1: 协作邀请调度闭环

**目标**: 大号接受协作邀请后，稳定触发 `WantedQuests` 调度。

- [x] T001 [US1] 梳理 `_burst()` 当前邀请类型判断
  - scope: `tasks/base_task.py`, `tasks/GlobalGame/assets.py`, `tasks/GlobalGame/config_emergency.py`
  - maps_to: US1, FR-001, FR-004
  - verify: 能说明哪些邀请类型会点击 accept，哪些会 ignore/reject。

- [x] T002 [US1] 接受协作悬赏后以最小侵入方式触发 `WantedQuests`
  - scope: `tasks/base_task.py`
  - maps_to: US1, FR-001, FR-002, Decision 1
  - verify: 接受勾协/粮协等协作邀请后，`wanted_quests.scheduler.next_run` 被写为当前时间，并出现等价调度日志；不修改 `module/config/config.py` 或 scheduler。

- [x] T003 [US1] 避免普通组队邀请误触发 `WantedQuests`
  - scope: `tasks/base_task.py`
  - maps_to: US1-3, FR-004
  - verify: 普通组队邀请只执行原有 accept 行为，不写入 `WantedQuests.next_run`。

---

## Phase 2: 配置和验证

**目标**: 确保 `oas_main` 的配置允许大号 `WantedQuests` 被 scheduler 正常看见。

- [x] T004 [US1] 增加或扩展配置检查脚本
  - scope: `scripts/`, `AGENTS.md`
  - maps_to: US1-5, FR-005, Decision 2
  - verify: 脚本能检查 `wanted_quests.scheduler.enable`、`next_run` 可写性、调度规则是否包含 `WantedQuests`，并输出是否可达；自动修正必须通过显式参数触发。

- [x] T005 [US1] 本地静态验证
  - scope: changed files
  - maps_to: NFR-001
  - verify: 运行格式/导入级检查，确认没有语法错误。

- [x] T006 [US1] Windows 实机验证
  - scope: `oas_main`, `oas_findjade`
  - maps_to: US1-1, US1-2, Quality 一致性
  - verify: 在 `WantedQuests.scheduler.enable=true` 的大号实例中，小号发送勾协，大号接受后进入 `WANTEDQUESTS`，并执行或明确记录执行失败原因。

---

## 依赖与顺序

- T001 必须先于 T002/T003。
- T002 和 T003 是同一改动面的两个验收点，应一起实现。
- T004 可与 T002/T003 并行，但 T006 前必须完成。
- T006 是本 feature 的最终闭环验证。

---

## 覆盖检查

| 场景 / 需求 | 对应任务 |
|-------------|----------|
| US1-1 接受勾协后调度悬赏 | T001, T002, T006 |
| US1-2 悬赏调度配置可被检查和修正 | T004 |
| US1-3 非协作邀请不误触发 | T003 |
| US1-4 当前任务未结束 | T002, T006 |
| US1-5 调度规则过滤 | T004 |

| 架构决策 / 质量属性 | 对应任务 | 验证任务 |
|----------------------|----------|----------|
| Decision 1: 最小侵入写入 `next_run` | T002 | T006 |
| Decision 2: 配置脚本检查 | T004 | T004, T006 |
| 一致性 | T002 | T006 |
| 可用性 | T003 | T006 |

---

## Stage Readiness

- 推荐下一步：`implement`
- 阻塞项：无。
