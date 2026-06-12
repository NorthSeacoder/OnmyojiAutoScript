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
   **Given** `oas_findjade` 中启用了 `Orochi`、`FindJade`、`DailyTriflesStoreSign`、`Hunt`、`TalismanPass`、`Exploration` 或 `AreaBoss`
   **When** 全局 scheduler 选择到一个小号任务
   **Then** 系统在任务执行前切换到当前应执行的小号，然后运行原任务。

2. **[US1-2] 编排任务覆盖所有到期小号**
   **Given** `SubAccountRotation` 启用了某个小号子任务，且两个小号都到期
   **When** scheduler 启动 `SubAccountRotation`
   **Then** `SubAccountRotation` 在同一次运行中依次切到到期小号并执行该子任务，直到本轮到期账号处理完。

3. **[US1-3] 庭院事务保留**
   **Given** 小号登录后触发 `Restart` 登录处理
   **When** `restart.harvest_config.enable_courtyard_affairs` 为 true
   **Then** 编排流程保留庭院事务收取，不禁用或绕开现有 `HARVEST` 行为。

**Edge Cases**:

- **[US1-3] 单个小号登录失败** 跳过该账号或按失败间隔重试，不影响其他小号执行。
- **[US1-4] 任务失败** 记录当前账号和当前 scheduler task，失败处理仍尽量复用原任务的 `next_run`/failure interval。
- **[US1-5] Cookie/扫码失效** 日志应能指出当前账号登录失败，需要人工接管。

### User Story 2 - 复用现有组队任务邀请大号 (Priority: P1)

作为已有 OAS 组队功能的用户，我希望御魂/探索等任务仍由全局 scheduler 正常启动，只是在这些任务运行前已经处于正确小号登录态，而不是新增一套组队执行器。

**Why this priority**: 御魂是当前最高优先级；仓库已有 `GeneralInvite`、`Orochi`、`Exploration` 的邀请能力，复用可以减少风险。

**Acceptance Scenarios**:

1. **[US2-1] 小号御魂邀请大号**
   **Given** `orochi.orochi_config.user_status` 配置为 `leader`，`orochi.invite_config.friend_1` 为大号昵称
   **When** scheduler 启动 `SubAccountRotation`，且 `Orochi` 子任务被显式启用
   **Then** 小号作为队长进入御魂并通过现有 `GeneralInvite` 邀请大号。

2. **[US2-2] 小号探索邀请大号**
   **Given** `exploration.exploration_config.user_status` 配置为 `leader`，`exploration.invite_config.friend_1` 为大号昵称
   **When** scheduler 启动 `SubAccountRotation`，且 `Exploration` 子任务被显式启用
   **Then** 小号执行困难28探索，并通过现有探索邀请逻辑邀请大号；执行次数/时长沿用现有 `Exploration` 配置手动控制，不在轮换层硬编码。

**Edge Cases**:

- **[US2-3] 大号不空闲** 小号等待现有邀请超时后退出房间并继续后续流程。
- **[US2-4] 大号未接受组队** 不应卡住整个小号循环。
- **[US2-5] 组队次数限制** 御魂/探索的次数或时长沿用现有 `Orochi` / `Exploration` 配置手动控制，避免轮换层长期占用大号。

### User Story 3 - 小号执行商店日常礼包和麒麟/阴界 (Priority: P1/P2)

作为用户，我希望每个小号领取商店日常礼包，推进 50 天黑蛋进度，并在合适时间摸一下麒麟/阴界，以便小号资源收益最大化。

**Why this priority**: 商店日常礼包是当前前三优先级；麒麟/阴界是后续收益项，但依赖日期/时间窗口。

**Acceptance Scenarios**:

1. **[US3-1] 摸麒麟**
   **Given** 当前时间在 `Hunt` 允许执行窗口内
   **When** scheduler 启动 `SubAccountRotation`，且 `Hunt` 子任务被显式启用
   **Then** 复用现有 `Hunt` 任务进入麒麟/阴界流程并执行一次。

2. **[US3-2] 领取商店日常礼包**
   **Given** `daily_trifles.trifles_config.store_sign` 为 true
   **When** scheduler 启动 `SubAccountRotation`，且商店日常礼包子任务被显式启用
   **Then** 复用现有 `DailyTrifles.run_store_sign()` 进入礼包屋并领取免费一抽/50 天黑蛋进度奖励。

3. **[US3-3] 可选寄售屋兑换碎片**
   **Given** 用户显式配置目标式神碎片，且寄售屋可兑换
   **When** scheduler 启动对应可选子任务
   **Then** 小号每周最多兑换一个指定式神碎片；若现有 `RichMan.consignment` 只能购买寄售券，不得把它误认为已满足该碎片兑换需求。

**Edge Cases**:

- **[US3-4] 非执行时间** `Hunt` 应跳过并安排下次运行，不阻塞其他小号。
- **[US3-5] 资源不足** 兑换或领取失败只记录日志，不影响后续账号。

### User Story 4 - 小号轻量日常和地域鬼王 (Priority: P2)

作为用户，我希望小号只做必要的轻量日常：花合战/收菜、困难28探索、地域鬼王；不把宠物、委派、每周杂项、活动等长流程塞进轮换。

**Acceptance Scenarios**:

1. **[US4-1] 花合战/收菜**
   **Given** `TalismanPass` 子任务被显式启用
   **When** scheduler 启动 `SubAccountRotation`
   **Then** 小号领取花合战/可收取奖励，不扩展到未确认的日常杂项。

2. **[US4-2] 地域鬼王**
   **Given** `AreaBoss` 子任务被显式启用
   **When** scheduler 启动 `SubAccountRotation`
   **Then** 小号执行地域鬼王，失败只记录当前账号，不影响后续账号。

3. **[US4-3] 逢魔不作为子任务**
   **Given** 切号登录后庭院事务会顺手处理部分入口
   **When** 用户没有显式要求独立 `DemonEncounter` 轮换
   **Then** 系统不得新增独立逢魔子任务。

---

## Requirements

### Functional Requirements

- **FR-001**: 系统必须提供一个普通 scheduler 任务 `SubAccountRotation`，在该任务内部为到期小号切换账号并执行启用的子任务。
- **FR-002**: 若某个子任务仍有其他到期小号未执行，`SubAccountRotation` 必须在同一次运行中继续处理，直到本轮到期账号处理完。
- **FR-003**: 编排任务必须保留现有登录收取和庭院事务逻辑。
- **FR-004**: 账号轮换层必须能配置哪些子任务需要在小号账号池上执行，当前范围为 `Orochi`、`FindJade`、商店日常礼包、`Hunt`、`TalismanPass`、`Exploration`、`AreaBoss`，以及可选的寄售屋指定式神碎片兑换。
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
| 可配置性 | 可按子任务逐步启用 | 用户要先稳定庭院/悬赏，再启用组队 | 配置模型和脚本支持子任务开关 | 是 |
| 可演进性 | 后续能加入更多小号任务 | 用户未来还有 9 个小号和更多日常 | 账号轮换 hook 对普通任务通用 | 是 |
| 一致性 | 每个账号完成时间准确更新 | 防止同一时段重复登录执行 | 配置中账号 history 更新 | 是 |

### Key Entities

- **SubAccount**: 小号账号信息，包含角色名、服务器、账号标识、平台、最近完成时间。
- **SubTask**: `SubAccountRotation` 内部可启用的小号子任务，例如 `Orochi`、`FindJade`、商店日常礼包、`Hunt`、`TalismanPass`、`Exploration`、`AreaBoss`。
- **Account Rotation State**: 记录每个账号对各子任务的最近完成时间。
- **Main Account Friend**: 被小号邀请的大号，当前昵称为 `不知庭院`。

---

## Out of Scope

- 不重写组队邀请、房间等待、战斗逻辑。
- 不实现跨模拟器通信协议；大号仍依赖现有 OAS 实例接受邀请。
- 不保证大号在任何时刻都空闲；组队邀请失败时由现有超时机制处理。
- 不在第一版处理所有 9 个小号的个性化阵容差异，先支持统一配置。
- 不接入 `Pets`、`DemonEncounter`、`Delegation`、`WeeklyTrifles`、结界卡、阴阳寮突破、道馆、斗技、整理御魂或活动类任务，除非用户后续明确改变范围。

---

## Unclear Questions

- 御魂每个小号每日目标次数需要后续配置；当前只确定优先级最高。
- 探索已收敛为困难28，但次数/时长沿用现有 `Exploration` 日常配置手动控制。

---

## Stage Readiness

- 下一步建议：`plan`
- 阻塞项：无。子任务默认开关可在 plan 中采用保守默认；御魂/探索次数沿用现有任务配置。
