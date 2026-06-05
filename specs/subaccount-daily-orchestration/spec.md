# Feature Specification: Subaccount Daily Orchestration

**Workspace**: `subaccount-daily-orchestration`
**Created**: 2026-06-05
**Status**: Draft
**Input**: 用户描述: "切号后除了执行庭院事务以外，还要能够邀请大号去进行御魂或者探索任务，同时小号摸一下麒麟、购买商店黑蛋等。已有组队功能，不要重写组队；日程本身支持任务执行，只是额外加一层账号切换。"

---

## Feature Traits

| Trait | 是否命中 | 依据 |
|---|---|---|
| `multi-stage-workflow` | ✅ | 全局 scheduler 先选出任务，再由账号轮换层决定是否需要切换到下一个小号后执行。 |
| `external-side-effects` | ✅ | 会登录多个游戏账号，消耗体力/门票/金币/商店货币，并邀请大号组队。 |
| `artifact-handoff` | ✅ | scheduler 产出的 pending task 交给账号轮换层，账号轮换层产出的登录态交给现有任务消费。 |
| `user-visible-output` | ✅ | OASX 调度、日志、游戏内任务完成状态都可见。 |
| `prior-closure-failure` | ✅ | 之前已出现切号、服务器选择、协作接受后不执行等闭环问题。 |

**结论**: 下游 plan 必须定义每个阶段的 producer-consumer 关系，尤其是“切号成功后谁消费登录态”和“组队功能只被调用不被重写”。

---

## User Scenarios & Testing

### User Story 1 - 每个小号切号后执行一组日常动作 (Priority: P1)

作为维护 9 个小号的用户，我希望脚本在全局 scheduler 选出待执行任务后，能在执行小号任务前切换到合适的小号，以便继续复用现有日程、优先级、任务 enable/next_run 机制。

**Why this priority**: 这是小号自动化的主目标，也是减少配置复杂度的核心。

**Acceptance Scenarios**:

1. **[US1-1] scheduler 驱动小号任务**
   **Given** `oas_findjade` 中启用了 `FindJade`、`Hunt`、`MysteryShop` 或组队任务
   **When** 全局 scheduler 选择到一个小号任务
   **Then** 系统在任务执行前切换到当前应执行的小号，然后运行原任务。

2. **[US1-2] 同一任务覆盖所有到期小号**
   **Given** `FindJade` 被标记为 rotated task，且两个小号都到期
   **When** scheduler 第一次启动 `FindJade` 并完成第一个小号
   **Then** 系统将 `FindJade` 重新置为可运行，下一轮继续切到第二个小号，直到该 task 的到期账号全部处理完。

3. **[US1-3] 庭院事务保留**
   **Given** 小号登录后触发 `Restart` 登录处理
   **When** `restart.harvest_config.enable_courtyard_affairs` 为 true
   **Then** 编排流程保留庭院事务收取，不禁用或绕开现有 `HARVEST` 行为。

**Edge Cases**:

- **[US1-3] 单个小号登录失败** 跳过该账号或按失败间隔重试，不影响其他小号执行。
- **[US1-4] 任务失败** 记录当前账号和当前 scheduler task，失败处理仍尽量复用原任务的 `next_run`/failure interval。
- **[US1-5] Cookie/扫码失效** 日志应能指出当前账号登录失败，需要人工接管。

### User Story 2 - 复用现有组队任务邀请大号 (Priority: P2)

作为已有 OAS 组队功能的用户，我希望御魂/探索等任务仍由全局 scheduler 正常启动，只是在这些任务运行前已经处于正确小号登录态，而不是新增一套组队执行器。

**Why this priority**: 仓库已有 `GeneralInvite`、`Orochi`、`Exploration` 的邀请能力，复用可以减少风险。

**Acceptance Scenarios**:

1. **[US2-1] 小号御魂邀请大号**
   **Given** `orochi.orochi_config.user_status` 配置为 `leader`，`orochi.invite_config.friend_1` 为大号昵称
   **When** scheduler 启动 `Orochi`，且该任务被标记为小号轮换任务
   **Then** 小号作为队长进入御魂并通过现有 `GeneralInvite` 邀请大号。

2. **[US2-2] 小号探索邀请大号**
   **Given** `exploration.exploration_config.user_status` 配置为 `leader`，`exploration.invite_config.friend_1` 为大号昵称
   **When** scheduler 启动 `Exploration`，且该任务被标记为小号轮换任务
   **Then** 小号通过现有探索邀请逻辑邀请大号，不新增独立邀请实现。

**Edge Cases**:

- **[US2-3] 大号不空闲** 小号等待现有邀请超时后退出房间并继续后续流程。
- **[US2-4] 大号未接受组队** 不应卡住整个小号循环。
- **[US2-5] 组队次数限制** 编排器应能限制每个小号执行御魂/探索的次数或时长，避免长期占用。

### User Story 3 - 小号执行麒麟和神秘商店黑蛋 (Priority: P2)

作为用户，我希望每个小号在合适时间摸一下麒麟，并在神秘商店日购买黑蛋碎片，以便小号资源收益最大化。

**Why this priority**: 这是小号日常收益项，但依赖日期/时间/商店刷新。

**Acceptance Scenarios**:

1. **[US3-1] 摸麒麟**
   **Given** 当前时间在 `Hunt` 允许执行窗口内
   **When** scheduler 启动 `Hunt`，且该任务被标记为小号轮换任务
   **Then** 复用现有 `Hunt` 任务进入麒麟/阴界流程并执行一次。

2. **[US3-2] 购买神秘商店黑蛋**
   **Given** 当天是神秘商店日，且 `mystery_shop.shop_config.black_daruma_scrap` 为 true
   **When** scheduler 启动 `MysteryShop`，且该任务被标记为小号轮换任务
   **Then** 复用现有 `MysteryShop` 购买黑蛋碎片逻辑。

**Edge Cases**:

- **[US3-3] 非执行时间** `Hunt` 或 `MysteryShop` 应跳过并安排下次运行，不阻塞其他小号。
- **[US3-4] 资源不足** 购买失败只记录日志，不影响后续账号。

---

## Requirements

### Functional Requirements

- **FR-001**: 系统必须提供一个账号轮换层，在全局 scheduler 启动指定小号任务前切换账号。
- **FR-002**: 若某个 rotated task 仍有其他到期小号未执行，系统必须在当前账号完成后重新触发同一 task，直到本轮到期账号处理完。
- **FR-003**: 编排任务必须保留现有登录收取和庭院事务逻辑。
- **FR-004**: 账号轮换层必须能配置哪些任务需要在小号账号池上执行，例如 `FindJade`、`Hunt`、`MysteryShop`、`Orochi`、`Exploration`。
- **FR-005**: 御魂和探索必须复用现有 `Orochi`、`Exploration` 和 `GeneralInvite` 能力，不新增重复的组队底层实现。
- **FR-006**: 账号轮换层必须支持记录每个小号在每类轮换任务上的完成时间，避免短时间重复登录执行同一类任务。
- **FR-007**: 任务失败时必须记录账号和任务名，并尽量复用原 scheduler 的失败间隔语义。
- **FR-008**: 配置脚本必须能继续简化新增小号，不要求用户手动编辑复杂 JSON。

### Non-Functional Requirements

- **NFR-001**: 变更应以账号轮换层为主，减少侵入现有任务模块和 scheduler 语义。
- **NFR-002**: 日志必须能定位当前账号、当前 scheduler task、成功/失败状态。
- **NFR-003**: 默认配置应保守，避免首次启用就消耗大量资源或长时间占用大号。

### Quality Attributes

| 属性 | 目标 | 为什么重要 | 验收 / 证据 | 是否阻塞 plan |
|------|------|------------|-------------|----------------|
| 可用性 | 单账号失败不拖垮全流程 | 10 个号中可能有 cookie 失效或账号异常 | 日志显示跳过失败账号并继续 | 是 |
| 可配置性 | 可按 rotated task 逐步启用 | 用户要先稳定庭院/悬赏，再启用组队 | 配置模型和脚本支持任务轮换开关 | 是 |
| 可演进性 | 后续能加入更多小号任务 | 用户未来还有 9 个小号和更多日常 | 账号轮换 hook 对普通任务通用 | 是 |
| 一致性 | 每个账号完成时间准确更新 | 防止同一时段重复登录执行 | 配置中账号 history 更新 | 是 |

### Key Entities

- **SubAccount**: 小号账号信息，包含角色名、服务器、账号标识、平台、最近完成时间。
- **RotatedTask**: 被标记为需要在小号池上运行的普通 OAS 任务，例如 `FindJade`、`Hunt`、`MysteryShop`、`Orochi`、`Exploration`。
- **Account Rotation State**: 记录某个任务下一次应使用哪个小号，以及每个账号对该任务的最近完成时间。
- **Main Account Friend**: 被小号邀请的大号，当前昵称为 `不知庭院`。

---

## Out of Scope

- 不重写组队邀请、房间等待、战斗逻辑。
- 不实现跨模拟器通信协议；大号仍依赖现有 OAS 实例接受邀请。
- 不保证大号在任何时刻都空闲；组队邀请失败时由现有超时机制处理。
- 不在第一版处理所有 9 个小号的个性化阵容差异，先支持统一配置。

---

## Unclear Questions

- 第一版是否将御魂/探索默认关闭，只在确认大号协作闭环稳定后再启用？当前规格建议默认关闭，但仍通过 scheduler enable 控制。
- 御魂和探索每天每个小号的目标次数是多少？当前计划只提供配置，不硬编码。

---

## Stage Readiness

- 下一步建议：`plan`
- 阻塞项：无。次数和默认开关可在 plan 中采用保守默认。
