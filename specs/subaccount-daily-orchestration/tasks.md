# Tasks: Subaccount Daily Orchestration

**Workspace**: `subaccount-daily-orchestration` | **Date**: 2026-06-05
**Input**: `specs/subaccount-daily-orchestration/spec.md` + `plan.md`
**Prerequisites**: spec.md, plan.md

---

## 执行原则

- 保留全局 scheduler，不重写任务调度。
- 账号轮换层只做“任务执行前切号”和“任务完成后更新账号历史”。
- 每个任务日志必须包含当前小号和当前 scheduler task。

---

## Phase 1: 配置模型和轮换入口

**目标**: 让 OAS 能识别哪些普通任务需要在小号池上轮换执行。

- [ ] T001 [US1] 新增 `SubAccountRotation` 配置模型
  - scope: `tasks/SubAccountRotation/config.py`
  - maps_to: FR-001, FR-003, Quality 可配置性
  - verify: `ConfigModel` 能加载默认配置。

- [ ] T002 [US1] 接入配置模型和菜单
  - scope: `module/config/config_model.py`, `module/config/config_menu.py`
  - maps_to: FR-001
  - verify: OASX 配置中能看到或至少配置文件能保存 `sub_account_rotation`。

- [ ] T003 [US1] 定义轮换任务列表和失败策略
  - scope: `tasks/SubAccountRotation/config.py`
  - maps_to: FR-003, FR-006
  - verify: 默认只轮换 `FindJade`，`Hunt`/`MysteryShop`/`Orochi`/`Exploration` 由配置显式加入。

---

## Phase 2: scheduler 前置账号轮换

**目标**: 在全局 scheduler 启动 rotated task 前切换到合适小号。

- [ ] T004 [US1] 实现账号列表加载和 per-task `need_run` 判断
  - scope: `tasks/SubAccountRotation/`, `tasks/FindJade/config.py`
  - maps_to: FR-001, FR-005
  - verify: 能复用 `find_jade.sup_account_list` 并跳过近期已完成账号。

- [ ] T005 [US1] 复用 `SwitchAccount` 完成逐账号登录
  - scope: `tasks/SubAccountRotation/`, `tasks/Component/SwitchAccount/`
  - maps_to: US1-1, US1-3
  - verify: 两个已配置小号能依次切换，登录失败账号被跳过。

- [ ] T006 [US1] 保留登录收取和庭院事务
  - scope: `tasks/SubAccountRotation/`, `tasks/Restart/login.py`
  - maps_to: US1-2, FR-002
  - verify: 小号登录后仍出现 HARVEST/庭院事务相关日志。

- [ ] T007 [US1] 在原 task 启动前注入账号轮换 hook
  - scope: `script.py`, `module/config/config.py`, `tasks/SubAccountRotation/`
  - maps_to: FR-003, FR-006, Quality 可演进性
  - verify: normal task 行为不变；rotated task 在日志中显示先切号再进入原 task。

- [ ] T007A [US1] 同一 rotated task 完成后继续调度下一个到期账号
  - scope: `script.py`, `module/config/config.py`, `tasks/SubAccountRotation/`
  - maps_to: US1-2, FR-002
  - verify: 两个小号都到期时，第一次 `FindJade` 完成后同一 task 立即重新 pending，并切到第二个小号。

---

## Phase 3: 复用现有子任务

**目标**: 把现有任务标记为需要账号轮换，而不是由新执行器调用。

- [ ] T008 [US1] 将 `FindJade` 作为默认 rotated task
  - scope: `tasks/SubAccountRotation/`, `tasks/FindJade/`
  - maps_to: FR-003, Feature 1 handoff
  - verify: 小号能发协作邀请；大号闭环由 Feature 1 验证。

- [ ] T009 [US3] 接入 `Hunt`
  - scope: `tasks/SubAccountRotation/`, `tasks/Hunt/`
  - maps_to: US3-1
  - verify: 非时间窗口能跳过，时间窗口能进入麒麟/阴界流程。

- [ ] T010 [US3] 接入 `MysteryShop`
  - scope: `tasks/SubAccountRotation/`, `tasks/MysteryShop/`
  - maps_to: US3-2
  - verify: 非神秘商店日跳过；商店日按配置尝试购买黑蛋。

- [ ] T011 [US2] 接入 `Orochi` 组队调用
  - scope: `tasks/SubAccountRotation/`, `tasks/Orochi/`
  - maps_to: US2-1, FR-004
  - verify: 小号作为 leader 调用现有邀请逻辑邀请 `不知庭院`。

- [ ] T012 [US2] 接入 `Exploration` 组队调用
  - scope: `tasks/SubAccountRotation/`, `tasks/Exploration/`
  - maps_to: US2-2, FR-004
  - verify: 小号作为 leader 调用现有探索邀请逻辑。

---

## Phase 4: 配置脚本和验证

**目标**: 降低后续新增小号和启用子任务的配置成本。

- [ ] T013 [US1] 新增或扩展小号轮换配置脚本
  - scope: `scripts/configure_subaccount_rotation.py` 或 `scripts/configure_findjade_accounts.py`
  - maps_to: FR-007
  - verify: 支持默认大号 `不知庭院`、服务器 `月蚀长夜`、两个现有小号、`--add` 新增小号，以及 `--rotate <TaskName>`。

- [ ] T014 [US1] 更新 `AGENTS.md`
  - scope: `AGENTS.md`
  - maps_to: FR-007
  - verify: 后续 agent 能按文档配置小号和启用子任务。

- [ ] T015 [US1] 本地静态验证
  - scope: changed files
  - maps_to: NFR-001
  - verify: 语法/导入级检查通过。

- [ ] T016 [US1] Windows 双小号实机验证
  - scope: `oas_findjade`
  - maps_to: US1-1, US1-2, Quality 可用性
  - verify: 两个小号依次切换，执行默认子任务，并更新完成时间。

- [ ] T017 [US2/US3] 可选实机验证
  - scope: `Hunt`, `MysteryShop`, `Orochi`, `Exploration`
  - maps_to: US2, US3
  - verify: 分别单独启用一个子任务测试，避免同时打开导致定位困难。

---

## 依赖与顺序

- Feature 1 应先完成，否则小号悬赏协作邀请大号仍可能没有消费方。
- T001-T003 必须先于 T004-T012。
- T008-T012 可逐个实现和验证，不需要一次性全部打开。
- T013-T014 应在实机长期使用前完成。

---

## 覆盖检查

| 场景 / 需求 | 对应任务 |
|-------------|----------|
| US1 scheduler 驱动小号任务 | T001-T008, T016 |
| US2 复用组队邀请大号 | T011, T012, T017 |
| US3 摸麒麟/买黑蛋 | T009, T010, T017 |
| FR-004 不重写组队 | T011, T012 |
| FR-007 简化配置 | T013, T014 |

| 架构决策 / 质量属性 | 对应任务 | 验证任务 |
|----------------------|----------|----------|
| 新增编排任务 | T001-T007 | T016 |
| 组队只调用现有任务 | T011, T012 | T017 |
| 默认低风险子任务 | T003 | T016 |
| 可用性 | T005, T007 | T016 |
| 可配置性 | T001, T003, T013 | T013 |

---

## Stage Readiness

- 推荐下一步：`execute-plan`
- 阻塞项：Feature 1 未完成前，不建议把小号悬赏协作视为已闭环；御魂/探索次数可实施后再由用户配置。
