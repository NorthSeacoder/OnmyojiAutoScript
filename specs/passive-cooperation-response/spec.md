# Feature Specification: Passive Cooperation Response

**Workspace**: `passive-cooperation-response`
**Created**: 2026-06-13
**Status**: Draft
**Parent Context**: 从 `subaccount-daily-orchestration` 实机验证中发现的架构需求

---

## Feature Traits

| Trait | 是否命中 | 依据 |
|---|---|---|
| `multi-stage-workflow` | ✅ | 需要监听邀请、验证来源、启动对应任务、完成后恢复监听态 |
| `external-side-effects` | ✅ | 接受游戏内邀请、消耗体力/门票、修改大号游戏状态 |
| `state-machine` | ✅ | 待命态 → 邀请检测 → 任务执行 → 恢复待命态 |
| `config-isolation` | ✅ | 不能污染普通任务的 scheduler.next_run，需要隔离配置上下文 |
| `prior-closure-failure` | ✅ | 当前架构要求启用普通任务才能响应邀请，导致调度器污染 |

**结论**: 必须设计独立于普通任务调度器的被动响应机制，避免为了接受邀请而启用会自主触发的普通任务。

---

## Problem Statement

### 当前架构痛点

从 `SubAccountRotation` 实机验证（2026-06-13）中暴露的问题：

**问题 1: 调度器污染**
- 小号发起御魂邀请时，大号必须启用 `orochi.scheduler.enable=true` 才能通过 burst 机制响应
- 这导致大号的 `orochi.scheduler.next_run` 会被更新，影响大号自己的御魂计划
- 验证完成后必须手动关闭 scheduler，配置管理复杂

**问题 2: 任务干扰**
- 启用 `Orochi` scheduler 后，大号可能在不该打御魂的时候自己触发任务
- 临时配置（`limit_count=1`）只能减轻问题，无法根治

**问题 3: 配置耦合**
- 小号 `limit_count=2` 期望打两次，但大号 `limit_count=1` 只接受一次邀请
- 多轮邀请需要两边配置精确协调，容易失配
- 大号作为 member 的配置与作为 leader 的配置混在同一个 `orochi` 配置块中

**问题 4: 通用性不足**
- 类似问题也存在于 FindJade cooperation（已通过 `cooperation_only` 部分解决）
- 但 `cooperation_only` 只适用于 WantedQuests，不能推广到御魂、探索等其他任务
- 每个任务都需要单独添加 `*_only` 模式，维护成本高

### 理想目标

大号应该有一个**专门的被动响应任务**，它：

1. **不占用调度器**: 不参与普通 scheduler 轮询，不会自己触发
2. **只响应邀请**: 纯粹等待并响应小号发起的组队/协作邀请
3. **不污染 next_run**: 完成后不更新对应普通任务的 `scheduler.next_run`
4. **配置隔离**: 被动响应的配置（如 accept 次数）与普通任务配置分离
5. **通用性**: 一个任务支持多种邀请类型（御魂、探索、协作等）

---

## User Scenarios & Testing

### User Story 1 - 大号待命接受小号御魂邀请 (Priority: P0)

作为维护多个小号的用户，我希望大号能在不启用御魂 scheduler 的情况下，随时接受小号发起的御魂邀请，以便小号轮换流程顺畅运行，同时不影响大号自己的御魂计划。

**Why this priority**: 这是 `SubAccountRotation` 正常运行的前置需求，直接阻塞小号轮换的核心价值。

**Acceptance Scenarios**:

1. **[US1-1] 大号待命态接受御魂邀请**
   **Given** 大号启用了 `PassiveCooperationResponse` 任务，配置了 `orochi.passive_mode.enable=true`
   **And** 大号普通 `Orochi` 任务的 `scheduler.enable=false`（未启用）
   **When** 小号发起御魂邀请给大号
   **Then** `PassiveCooperationResponse` 检测到邀请弹窗，解析邀请类型为"御魂"，自动接受邀请，并以 member 模式加入战斗
   **And** 战斗完成后返回待命态，继续监听下一次邀请
   **And** 普通 `Orochi` 任务的 `scheduler.next_run` **不被修改**

2. **[US1-2] 多轮邀请响应**
   **Given** 小号配置 `limit_count=3`，期望打 3 次御魂
   **And** 大号 `orochi.passive_mode.max_accept_count=3` 或 `-1`（无限制）
   **When** 小号完成第一次战斗后发起第二次邀请
   **Then** 大号自动接受第二次邀请，继续以 member 模式参与
   **And** 重复至小号的 `limit_count` 耗尽或大号的 `max_accept_count` 达到上限

3. **[US1-3] 邀请次数限制**
   **Given** 大号 `orochi.passive_mode.max_accept_count=1`
   **When** 小号发起第二次邀请
   **Then** 大号不接受邀请（或接受后立即退出房间），日志记录"已达到御魂被动响应次数上限"

**Edge Cases**:

- **[US1-E1] 小号邀请超时** 大号在 2 分钟内未检测到邀请弹窗，返回待命态
- **[US1-E2] 战斗失败** 大号战斗失败后仍正常退出并返回待命态，不影响后续邀请
- **[US1-E3] 网络中断** 战斗过程中网络中断，大号尝试重连或返回待命态，不卡死
- **[US1-E4] 大号不在待命态** 大号正在执行其他普通任务时，不响应邀请（或由普通任务决定是否中断）

### User Story 2 - 大号待命接受小号探索邀请 (Priority: P1)

作为用户，我希望大号能接受小号发起的探索邀请，在不启用探索 scheduler 的情况下帮助小号完成困难 28 等高难度探索。

**Why this priority**: 探索是小号轮换的第二优先级，且探索邀请逻辑与御魂类似。

**Acceptance Scenarios**:

1. **[US2-1] 大号待命态接受探索邀请**
   **Given** 大号启用了 `PassiveCooperationResponse` 任务，配置了 `exploration.passive_mode.enable=true`
   **And** 大号普通 `Exploration` 任务的 `scheduler.enable=false`
   **When** 小号发起探索邀请
   **Then** 大号检测到探索邀请弹窗，自动接受并以 member 模式加入探索
   **And** 探索完成后返回待命态
   **And** 普通 `Exploration` 任务的 `scheduler.next_run` 不被修改

**Edge Cases**:

- **[US2-E1] 探索层级不匹配** 小号邀请困难 28，但大号未解锁，日志记录"探索层级未解锁"并拒绝
- **[US2-E2] 探索次数限制** 大号 `exploration.passive_mode.max_accept_count` 控制接受次数

### User Story 3 - 大号待命接受小号协作邀请 (Priority: P1)

作为用户，我希望大号能接受小号发起的寻物协作邀请，复用现有 `cooperation_only` 模式的思路，但统一到 `PassiveCooperationResponse` 任务中。

**Why this priority**: FindJade cooperation 已部分实现，但当前是分散在 WantedQuests 配置中，应统一到被动响应任务。

**Acceptance Scenarios**:

1. **[US3-1] 大号待命态接受协作邀请**
   **Given** 大号启用了 `PassiveCooperationResponse` 任务，配置了 `wanted_quests.passive_mode.enable=true`
   **And** 大号普通 `WantedQuests` 任务的 `scheduler.enable=false`
   **When** 小号发起寻物协作邀请
   **Then** 大号通过 `PassiveCooperationResponse` 检测到协作邀请，自动接受并加入战斗
   **And** 战斗完成后返回待命态
   **And** 普通 `WantedQuests` 任务的 `scheduler.next_run` 不被修改

**Edge Cases**:

- **[US3-E1] 协作类型过滤** 大号可配置只接受特定类型协作（玉藻、狗粮、猫粮），拒绝其他类型
- **[US3-E2] 协作次数限制** 大号 `wanted_quests.passive_mode.max_accept_count` 控制每日接受次数

### User Story 5 - 加成管理 (Priority: P0)

作为用户，我希望大号在接受御魂邀请时自动开启御魂加成，在接受探索邀请时自动开启经验加成，以便提升收益，避免手动管理加成状态。

**Why this priority**: 加成管理直接影响收益，是被动响应任务的核心价值之一，与邀请接受同等重要。

**Acceptance Scenarios**:

1. **[US5-1] 御魂加成自动开启**
   **Given** 大号 `passive_cooperation_response.passive_config.orochi.buff_enable=true`
   **When** 大号接受御魂邀请并进入组队界面
   **Then** 自动点击御魂加成按钮，确保加成开启
   **And** 日志记录"Orochi buff enabled"

2. **[US5-2] 探索经验加成自动开启**
   **Given** 大号 `passive_cooperation_response.passive_config.exploration.exp_buff_enable=true`
   **When** 大号接受探索邀请并进入探索准备界面
   **Then** 自动点击经验加成按钮，确保加成开启
   **And** 日志记录"Exploration exp buff enabled"

3. **[US5-3] 加成状态检测**
   **Given** 大号配置了自动开启加成
   **When** 进入组队/探索界面
   **Then** 首先检测加成当前状态（已开启/未开启）
   **And** 如果未开启，点击开启；如果已开启，跳过点击
   **And** 避免重复点击导致关闭加成

4. **[US5-4] 加成配置独立控制**
   **Given** 用户希望大号在普通御魂中不开加成，但在被动响应时开加成
   **Then** `orochi.orochi_config.soul_buff_enable` 控制普通任务
   **And** `passive_cooperation_response.passive_config.orochi.buff_enable` 控制被动响应
   **And** 两者独立配置，互不影响

**Edge Cases**:

- **[US5-E1] 加成不足** 大号御魂加成不足时，日志记录"Orochi buff insufficient"，但仍继续战斗
- **[US5-E2] 加成识别失败** OCR 识别加成状态失败时，尝试点击一次开启，避免卡住
- **[US5-E3] 协作任务无加成** WantedQuests 协作任务没有加成概念，配置中不包含 `buff_enable`

---

## User Story 4 - 统一配置和监控 (Priority: P2)

作为用户，我希望被动响应任务有统一的配置入口和监控界面，能清晰看到大号当前待命状态、已接受邀请次数、拒绝原因等信息。

**Why this priority**: 提升可维护性和可观测性，避免配置分散导致的混乱。

**Acceptance Scenarios**:

1. **[US4-1] 统一配置结构**
   **Given** 用户编辑配置文件
   **Then** 所有被动响应配置集中在 `passive_cooperation_response` 顶层配置块中：
   ```json
   {
     "passive_cooperation_response": {
       "scheduler": {
         "enable": true,
         "priority": 999
       },
       "passive_config": {
         "orochi": {
           "enable": true,
           "max_accept_count": -1,
           "allowed_inviters": ["最后的黄泉", "破晓的森林"],
           "buff_enable": true
         },
         "exploration": {
           "enable": true,
           "max_accept_count": 2,
           "exp_buff_enable": true
         },
         "wanted_quests": {
           "enable": true,
           "max_accept_count": 5,
           "allowed_cooperation_types": ["jade", "cat_food", "dog_food"]
         }
       }
     }
   }
   ```

2. **[US4-2] 监控日志**
   **Given** 被动响应任务正在运行
   **Then** 日志包含：
   - "PassiveCooperationResponse: Listening for invites (orochi, exploration, wanted_quests)"
   - "PassiveCooperationResponse: Detected orochi invite from 最后的黄泉"
   - "PassiveCooperationResponse: Accepted orochi invite (1/3)"
   - "PassiveCooperationResponse: Battle completed, returning to listening state"
   - "PassiveCooperationResponse: Rejected orochi invite (max_accept_count reached)"

**Edge Cases**:

- **[US4-E1] 配置热更新** 用户修改配置后，被动响应任务在下一个检测周期生效，无需重启
- **[US4-E2] 历史记录** 记录最近 N 次接受/拒绝邀请的历史（时间、类型、邀请者、结果）

---

## Scope & Non-Goals

### In Scope

✅ 大号待命态监听御魂、探索、协作邀请  
✅ 自动接受邀请并以 member 模式参与战斗  
✅ 配置隔离：不污染普通任务的 `scheduler.next_run`  
✅ 次数限制：每种邀请类型独立的 `max_accept_count`  
✅ 邀请者白名单：只接受指定小号的邀请  
✅ 统一配置和日志  

### Out of Scope

❌ 大号主动发起组队（仍由普通任务负责）  
❌ 小号之间互相邀请（当前只考虑小号 → 大号）  
❌ 实时 UI 界面（仅日志输出）  
❌ 跨服务器邀请（假设大号和小号在同一服务器）  
❌ 自动拒绝陌生人邀请（当前只关注配置的小号邀请）  

### Future Considerations

🔮 **邀请优先级**: 同时收到多个邀请时的处理策略（当前假设顺序处理）  
🔮 **大号繁忙态中断**: 大号正在执行普通任务时，是否允许中断以接受高优先级邀请  
🔮 **跨配置文件共享**: 多个配置文件共享同一个被动响应任务实例（当前假设每个配置独立）  
🔮 **GUI 集成**: 在 OASX GUI 中显示被动响应状态和历史  

---

## Core Interactions

### 1. 被动响应任务生命周期

```
[启动] → [待命态] ⟲ (循环检测邀请弹窗)
           ↓ (检测到邀请)
       [解析邀请] (类型、邀请者、层级等)
           ↓
       [验证配置] (enable、max_accept_count、白名单)
           ↓ (通过)
       [接受邀请] → [执行对应任务 member 模式] → [战斗完成]
           ↓
       [返回待命态] ⟲
```

### 2. 与普通任务的隔离

```
普通任务 (Orochi scheduler.enable=false)
   ↓
   不会自主触发
   ↓
   scheduler.next_run 保持不变

被动响应任务 (PassiveCooperationResponse scheduler.enable=true)
   ↓
   独立调度，高优先级
   ↓
   检测到邀请 → 临时调用普通任务的 member 流程
   ↓
   完成后不调用 set_next_run()
   ↓
   普通任务的 scheduler.next_run 不受影响
```

### 3. 配置映射关系

| 普通任务配置 | 被动响应配置 | 说明 |
|---|---|---|
| `orochi.scheduler.enable` | `passive_cooperation_response.passive_config.orochi.enable` | 分离开关 |
| `orochi.orochi_config.limit_count` | `passive_cooperation_response.passive_config.orochi.max_accept_count` | 普通任务限制自己主动打的次数，被动响应限制接受邀请的次数 |
| `orochi.orochi_config.user_status` | 固定 `member` | 被动响应永远是 member |
| `orochi.orochi_config.soul_buff_enable` | `passive_cooperation_response.passive_config.orochi.buff_enable` | 普通任务控制自己主动打时的加成，被动响应控制接受邀请时的加成 |
| `orochi.invite_config.friend_1` | `passive_cooperation_response.passive_config.orochi.allowed_inviters` | 普通任务是邀请谁，被动响应是接受谁的邀请 |
| `exploration.exploration_config.exp_enable` | `passive_cooperation_response.passive_config.exploration.exp_buff_enable` | 探索经验加成配置独立 |

---

## Data Model

### 配置结构

```python
class PassiveCooperationResponseConfig:
    scheduler: SchedulerConfig  # 独立调度器
    passive_config: PassiveModeConfig

class PassiveModeConfig:
    orochi: PassiveTaskConfig
    exploration: PassiveTaskConfig
    wanted_quests: PassiveCooperationConfig

class PassiveTaskConfig:
    enable: bool  # 是否接受该类型邀请
    max_accept_count: int  # -1 表示无限制
    allowed_inviters: List[str]  # 邀请者白名单，空列表表示接受所有
    buff_enable: bool  # 御魂加成/探索经验加成

class PassiveCooperationConfig(PassiveTaskConfig):
    allowed_cooperation_types: List[str]  # 玉藻/狗粮/猫粮
    # 协作任务没有 buff_enable，从父类继承但不使用
```

### 运行时状态

```python
class PassiveResponseState:
    current_state: Literal["listening", "validating", "executing"]
    active_invite: Optional[InviteInfo]  # 当前正在处理的邀请
    accept_counts: Dict[str, int]  # 每种任务类型当前已接受次数
    history: List[InviteHistoryRecord]  # 最近 50 条历史

class InviteInfo:
    task_type: Literal["orochi", "exploration", "wanted_quests"]
    inviter_name: str
    layer: Optional[str]  # 御魂层级/探索章节
    cooperation_type: Optional[str]  # 协作类型
    detected_at: datetime

class InviteHistoryRecord:
    task_type: str
    inviter_name: str
    detected_at: datetime
    accepted: bool
    rejection_reason: Optional[str]  # "max_count_reached" / "inviter_not_allowed" / "task_disabled"
    completed: bool
    completed_at: Optional[datetime]
```

---

## Constraints & Risks

### Technical Constraints

1. **检测延迟**: 邀请弹窗检测基于轮询截图，有 0.5-2 秒延迟
2. **OCR 依赖**: 邀请者昵称解析依赖 OCR，可能误识别
3. **单线程执行**: 被动响应任务与其他任务共享同一个 device，不能并发执行
4. **会话保持**: 大号需要保持登录态，否则检测不到邀请弹窗

### Integration Risks

1. **与现有 member 流程的兼容性**: 需要验证现有 `Orochi.run_member()`、`Exploration.run_member()` 能否被独立调用
2. **与 SubAccountRotation 的时序**: 小号发起邀请后，大号的被动响应任务可能正在执行其他检测，导致邀请超时
3. **配置迁移**: 现有用户可能已经在用 `cooperation_only`，需要提供迁移路径

### Upstream Compatibility

根据开发原则（**Patch-first strategy for upstream compatibility**）：

- ✅ 新增 `PassiveCooperationResponse` 任务不修改现有任务代码
- ✅ 配置结构新增，不影响现有配置
- ⚠️ 需要确保普通任务的 member 流程能被独立调用（可能需要小幅重构）
- ⚠️ 需要验证 `set_next_run` 拦截机制在被动响应场景下的有效性

---

## Implementation Research (2026-06-13)

### 调研结论

经过对现有代码的深入调研，确认了以下关键接口和机制：

#### 1. Orochi member 模式 ✅

**接口**: `tasks/Orochi/script_task.py`
- `run()` 方法根据 `user_status` 自动分发到 `run_member()`
- `run_member()` 不需要进入御魂界面，直接等待邀请
- **调用方式**: 设置 `user_status=member` + 拦截 `set_next_run` + 调用 `run()`

#### 2. Exploration member 模式 ✅

**接口**: `tasks/Exploration/solo.py`
- `run()` 方法根据 `user_status` 分发到 `run_member()`
- `run_member()` 等待队长发起探索邀请
- **调用方式**: 设置 `user_status=member` + 拦截 `set_next_run` + 调用 `run()`

#### 3. WantedQuests cooperation_only 模式 ✅

**接口**: `tasks/WantedQuests/script_task.py`
- `run()` 方法检查 `cooperation_only` 配置
- 如果为 `true`，调用 `pre_work_cooperation_only()` 只处理协作
- **调用方式**: 设置 `cooperation_only=True` + 拦截 `set_next_run` + 调用 `run()`

#### 4. 加成管理机制 ✅

**接口**: `tasks/Component/GeneralBuff/general_buff.py`
- **御魂加成**: `open_buff()` + `soul(is_open=True)` + `close_buff()`
- **探索经验加成**: `open_buff()` + `exp_50()/exp_100()` + `close_buff()`
- **状态检测**: 通过 `I_OPEN_YELLOW` / `I_CLOSE_RED` 检测当前开关状态
- **独立调用**: 可以在被动响应任务中独立控制，不依赖原任务的 `run()` 前置处理

### 架构风险评估

| 风险 | 级别 | 缓解方案 | 状态 |
|---|---|---|---|
| `run()` 前置处理开启加成 | 中 | 在被动响应任务中独立控制加成，完成后恢复 | ✅ 可控 |
| `run()` 后置处理调用 `set_next_run` | 高 | 拦截 `set_next_run` 方法 | ✅ 已验证（SubAccountRotation） |
| member 模式接口不完整 | 低 | 现有 member 流程已完善 | ✅ 无风险 |
| 配置恢复失败 | 中 | 使用 `try-finally` 确保恢复 | ✅ 可控 |

---

## Design Decisions

### 1. 邀请检测机制
**决策**: 依赖弹窗 OCR + 上下文页面判断组合方式
- 检测到组队邀请弹窗时，OCR 解析邀请者昵称
- 根据弹窗出现时的上下文页面判断类型：
  - `page_soul_zones` 上下文 → 御魂邀请
  - `page_exploration` 上下文 → 探索邀请
  - 协作邀请有独特弹窗样式，可直接识别
- **理由**: OCR 技术成熟，上下文判断可靠，避免复杂的弹窗类型模式匹配

### 2. 次数计数方式
**决策**: 累计计数，不自动重置
- `max_accept_count=-1` 表示无限制（日常使用推荐）
- 如需限制，用户在配置中设置具体数值
- **理由**: 用户反馈"不重要，日常使用时注意看小号的邀请"，简化设计，避免日期重置逻辑

### 3. 与现有 `cooperation_only` 的关系
**决策**: 保留 `cooperation_only`，逐步迁移
- 现有 `wanted_quests.wanted_quests_config.cooperation_only` 保持向后兼容
- 新增 `passive_cooperation_response.passive_config.wanted_quests` 作为推荐方式
- 文档中说明两种配置的区别和迁移路径
- **理由**: `cooperation_only` 是嵌入在 WantedQuests 内部的"仅协作模式"，适合大号也想主动找协作的场景；被动响应任务是纯待命态，适合大号完全不主动、只接受邀请的场景

### 4. 大号繁忙时的处理
**决策**: 第一版不支持中断，等待大号空闲
- 被动响应任务在 scheduler 中设置高优先级（999）
- 但不会中断正在执行的其他任务
- 如果大号正忙，小号邀请会超时，小号日志记录"invite timeout"
- **理由**: 避免复杂的任务中断和状态恢复逻辑，保持实现简洁

### 5. 多大号场景
**决策**: 不支持
- 当前只考虑单个大号配置
- 小号邀请时指定昵称，被动响应任务响应所有允许的邀请者
- **理由**: 用户反馈无多大号场景需求

---

## Acceptance Criteria Summary

### Must Have (P0)

- [ ] 大号待命态能检测并接受小号御魂邀请
- [ ] 普通 `Orochi` 任务的 `scheduler.next_run` 不受影响
- [ ] 支持多轮邀请（小号 `limit_count > 1`）
- [ ] 邀请次数限制 (`max_accept_count`)
- [ ] 邀请者白名单 (`allowed_inviters`)
- [ ] 配置隔离：`passive_cooperation_response` 独立配置块
- [ ] 日志记录：检测、接受、完成、拒绝
- [ ] **御魂加成自动管理** (`buff_enable`)
- [ ] **探索经验加成自动管理** (`exp_buff_enable`)

### Should Have (P1)

- [ ] 支持探索邀请
- [ ] 支持协作邀请
- [ ] 统一配置结构
- [ ] 历史记录（最近 50 条）
- [ ] 拒绝原因详细日志

### Could Have (P2)

- [ ] 配置热更新
- [ ] GUI 状态显示
- [ ] 跨配置文件共享

### Won't Have (当前版本)

- 邀请优先级调度
- 大号繁忙态中断
- 跨服务器邀请
- 实时 UI 界面

---

## Next Steps

1. **Review**: 用户确认需求范围和优先级
2. **Plan**: 设计实现方案（邀请检测、任务调用、配置结构）
3. **Prototype**: 实现御魂邀请的 MVP（最小可验证原型）
4. **Validate**: 实机验证御魂邀请流程
5. **Extend**: 扩展到探索和协作邀请
6. **Document**: 更新用户文档和配置示例

---

**Status**: Ready for review and planning phase
