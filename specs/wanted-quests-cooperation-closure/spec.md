# Feature Specification: Wanted Quests Cooperation Closure

**Workspace**: `wanted-quests-cooperation-closure`
**Created**: 2026-06-05
**Status**: Draft
**Input**: 用户描述: "小号邀请大号协作悬赏后，大号能接受协作任务，但是大号没有去执行这个任务，只是接受之后就扔那了。"

---

## Feature Traits

| Trait | 是否命中 | 依据 |
|---|---|---|
| `multi-stage-workflow` | ✅ | 小号发出协作邀请，大号接受，随后大号执行 `WantedQuests`，存在跨任务阶段。 |
| `external-side-effects` | ✅ | 会操作游戏账号、接受邀请、改变任务追踪和战斗状态。 |
| `artifact-handoff` | ✅ | 协作邀请被接受后产生“大号悬赏列表中的协作任务”，必须被 `WantedQuests` 消费。 |
| `user-visible-output` | ✅ | 日志、OASX 调度状态、游戏内协作任务完成情况都可见。 |
| `prior-closure-failure` | ✅ | 已观察到大号接受协作但未执行，属于已有闭环断点。 |

**结论**: 下游 plan 必须写清楚 producer-consumer 关系：邀请弹窗接受是 producer，`WantedQuests` 是 consumer，并定义可验证的消费证据。

---

## User Scenarios & Testing

### User Story 1 - 大号接受协作后自动进入悬赏执行闭环 (Priority: P1)

作为使用两个模拟器运行 OAS 的用户，我希望大号接受小号发来的悬赏协作后，系统能把大号侧 `WantedQuests` 尽快调度起来，以便协作任务不会只是被接受后停留在悬赏列表。

**Why this priority**: 这是小号 FindJade/悬赏邀请大号的核心收益。如果接受后不执行，小号流程看似成功但实际收益缺失。

**Acceptance Scenarios**:

1. **[US1-1] 接受勾协后调度悬赏**
   **Given** `oas_main` 正在运行，`global_game.emergency.friend_invitation` 允许接受勾协/粮协，且小号发来勾协邀请
   **When** 大号侧 `_burst()` 检测并点击接受
   **Then** `oas_main` 配置中的 `wanted_quests.scheduler.next_run` 被设置为当前时间，且调度器后续能将 `WantedQuests` 放入 pending 或立即执行。

2. **[US1-2] 悬赏调度配置可被检查和修正**
   **Given** 用户开启了协作邀请处理，但大号实例的 `WantedQuests.scheduler.enable` 可能未开启
   **When** 大号接受小号协作邀请
   **Then** 系统不绕过用户禁用语义；配置检查脚本必须指出 `WantedQuests` 不可达，并可在显式修正参数下启用或提示用户手动启用。

**Edge Cases**:

- **[US1-3] 非协作邀请** 普通组队邀请或不符合 `friend_invitation` 策略的邀请不应错误触发 `WantedQuests`。
- **[US1-4] 当前任务未结束** 如果大号正在战斗或执行长任务，系统不应强行中断当前任务；应保证当前任务结束后的调度能看到 `WantedQuests`。
- **[US1-5] 调度规则过滤** 如果 `script.optimization.schedule_rule` 使用 Filter，必须确认 `WantedQuests` 没被过滤，或由配置脚本修正。

---

## Requirements

### Functional Requirements

- **FR-001**: 系统必须在接受符合策略的悬赏协作邀请后，以最小侵入方式写入大号配置中的 `WantedQuests.scheduler.next_run`。
- **FR-002**: 系统必须保留现有 `friend_invitation` 策略，不改变用户对接受、拒绝、仅勾协、勾协粮协等选项的含义。
- **FR-003**: 系统必须在日志中输出协作接受和 `WantedQuests` 调用的可追踪信息。
- **FR-004**: 系统必须避免把普通组队邀请误判为需要执行 `WantedQuests` 的悬赏协作。
- **FR-005**: 配置脚本或文档必须说明 `oas_main` 需要启用 `WantedQuests`，且不能被调度规则过滤。

### Non-Functional Requirements

- **NFR-001**: 变更应局限在突发邀请处理和配置脚本/文档，不重写 `WantedQuests` 主流程。
- **NFR-002**: 失败时应可从日志判断是“未接受邀请”、“接受后未调度”还是“调度后悬赏执行失败”。

### Quality Attributes

| 属性 | 目标 | 为什么重要 | 验收 / 证据 | 是否阻塞 plan |
|------|------|------------|-------------|----------------|
| 一致性 | 接受协作后必有调度动作 | 避免 producer 产生协作任务但 consumer 不消费 | 日志出现接受邀请和 `WantedQuests.next_run` 更新或等价信息 | 是 |
| 可用性 | 不中断当前战斗或正在执行任务 | 大号可能在刷御魂/结界/斗技 | 当前任务结束后 pending 可见 | 是 |
| 可演进性 | 后续小号编排可依赖该闭环 | `FindJade`、小号日常编排都需要大号消费协作 | Feature 2 可直接复用 | 否 |

### Key Entities

- **协作邀请**: 游戏内好友发来的悬赏协作弹窗。当前全局突发素材可识别勾玉、猫粮、狗粮；体力、金币需要后续补充突发弹窗素材后再纳入自动识别。
- **Accepted Cooperation Artifact**: 大号接受后进入悬赏列表的协作任务。
- **WantedQuests Consumer**: 大号侧负责追踪和执行协作任务的任务模块。

---

## Out of Scope

- 不实现小号多任务编排。
- 不改御魂、探索等组队任务的邀请机制。
- 不解决 `WantedQuests` 内部 OCR 或战斗路径识别问题，除非验证时暴露为阻塞。

---

## Unclear Questions

- 是否需要在接受协作后立即暂停当前大号任务并抢占执行 `WantedQuests`？当前规格选择“不抢占，只保证尽快调度”。

---

## Stage Readiness

- 下一步建议：`plan`
- 阻塞项：无。当前需求足以进入技术方案。
