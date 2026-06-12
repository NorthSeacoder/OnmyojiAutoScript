# Tasks: Subaccount Daily Orchestration

**Workspace**: `subaccount-daily-orchestration` | **Date**: 2026-06-05
**Input**: `specs/subaccount-daily-orchestration/spec.md` + `plan.md`
**Prerequisites**: spec.md, plan.md

---

## 执行原则

- 保留全局 scheduler，不修改 `script.py` 主循环。
- 新增 `SubAccountRotation` 作为普通任务；账号轮换、子任务顺序和 history 都收敛在该任务内部。
- 每个子任务日志必须包含当前小号和当前 sub-task。
- 本仓库是上游开源脚本的本地 patch；实现优先新增文件和局部配置入口，避免核心调度冲突。

---

## Phase 1: 配置模型和轮换入口

**目标**: 让 OAS 能把 `SubAccountRotation` 作为普通任务加载，并保存小号编排配置。

- [x] T001 [US1] 新增 `SubAccountRotation` 配置模型
  - scope: `tasks/SubAccountRotation/config.py`
  - maps_to: FR-001, FR-003, Quality 可配置性
  - verify: `ConfigModel` 能加载默认配置。

- [x] T002 [US1] 接入配置模型和菜单
  - scope: `module/config/config_model.py`, `module/config/config_menu.py`
  - maps_to: FR-001
  - verify: OASX 配置中能看到或至少配置文件能保存 `sub_account_rotation`。

- [x] T003 [US1] 定义子任务开关、账号来源和失败策略
  - scope: `tasks/SubAccountRotation/config.py`
  - maps_to: FR-003, FR-006
  - verify: 默认只启用 `LoginOnly`；`Orochi`/`FindJade`/商店日常礼包/`Hunt`/`TalismanPass`/`Exploration`/`AreaBoss` 由配置显式加入。

---

## Phase 2: 独立编排任务

**目标**: 在 `SubAccountRotation` 内部完成逐账号切换、子任务调用和完成历史更新。

- [x] T004 [US1] 实现账号列表加载和 per-task `need_run` 判断
  - scope: `tasks/SubAccountRotation/`, `tasks/FindJade/config.py`
  - maps_to: FR-001, FR-005
  - verify: 能复用 `find_jade.sup_account_list`，并按 account/sub-task history 跳过近期已完成账号。

- [x] T005 [US1] 复用 `SwitchAccount` 完成逐账号登录
  - scope: `tasks/SubAccountRotation/`, `tasks/Component/SwitchAccount/`
  - maps_to: US1-1, US1-3
  - verify: 两个已配置小号能依次切换，登录失败账号被跳过。

- [x] T006 [US1] 保留登录收取和庭院事务
  - scope: `tasks/SubAccountRotation/`, `tasks/Restart/login.py`
  - maps_to: US1-2, FR-002
  - verify: Windows 单账号实机日志已出现 `HARVEST` 和 `courtyard affairs completed`。

- [x] T007 [US1] 实现 `SubAccountRotation` 主任务入口
  - scope: `tasks/SubAccountRotation/script_task.py`
  - maps_to: FR-001, FR-006, Quality 可演进性
  - verify: scheduler 启动 `SubAccountRotation` 后，日志显示账号循环、子任务循环和最终 `SubAccountRotation.next_run` 更新；不修改 `script.py`。

- [x] T007A [US1] 实现 account/sub-task 完成历史更新
  - scope: `tasks/SubAccountRotation/config.py`, `tasks/SubAccountRotation/script_task.py`
  - maps_to: US1-2, FR-002
  - verify: 两个小号都到期时，`SubAccountRotation` 在同一次运行中依次处理两个小号，并分别更新完成时间。

---

## Phase 3: 复用现有子任务

**目标**: 在 `SubAccountRotation` 内通过薄适配器复用现有任务能力，而不是重写底层 OCR/点击/组队逻辑。

**当前优先级**: 御魂 > 悬赏协作 > 商店日常礼包（50 天黑蛋进度） > 麒麟/阴界 > 花合战/收菜 > 困难28探索（次数沿用现有配置） > 地域鬼王。可选后续：商店寄售屋每周兑换一个指定式神碎片。

- [x] T008 [US1] 明确 `FindJade` 与 `SubAccountRotation` 的职责边界
  - scope: `tasks/SubAccountRotation/`, `tasks/FindJade/`
  - maps_to: FR-003, Feature 1 handoff
  - verify: 保留完整 `FindJade.run()` 作为独立任务；`SubAccountRotation` 不调用完整账号循环，只能通过当前账号薄入口接入。配置 helper 提供 `--disable-find-jade` 只用于隔离验证，避免同一 scheduler pass 中出现两层小号循环。

- [x] T009 [US2] 接入 `Orochi` 组队子任务适配器
  - scope: `tasks/SubAccountRotation/`, `tasks/Orochi/`
  - maps_to: US2-1, FR-004
  - verify: 小号作为 leader 调用现有邀请逻辑邀请 `不知庭院`；次数/时长由现有 `Orochi` 配置控制，建议验证时先设小值，避免长时间占用大号。
  - current: 2026-06-07 Windows 实机验证通过。`SubAccountRotation` 以小号 `最后的黄泉 / bmkfh1992@126.com` 登录后调用现有 `Orochi` leader 流程，成功邀请大号 `不知庭院`，双方进入战斗并胜利结束；日志显示 `SubAccountRotation captured Orochi next_run`，确认普通 `Orochi.scheduler.next_run` 未被轮换子任务污染。验证时仅为隔离御魂流程临时关闭小号 `restart.harvest_config.enable_courtyard_affairs`，验证后已恢复开启。

- [ ] T010 [US1] 接入 `FindJade` 当前账号悬赏协作适配器
  - scope: `tasks/SubAccountRotation/`, `tasks/FindJade/`
  - maps_to: Feature 1 handoff, FR-004
  - verify: 小号在当前账号上发起悬赏协作邀请，大号通过已完成的 `WantedQuests` 闭环消费；不得再次由 `FindJade` 自身循环账号列表。
  - current: 2026-06-07 适配器已实现。`FindJade.run_current_account()` 只执行当前已登录账号的 cooperation-only `WantedQuests` 流程，旧 `FindJade.run()` 继续保留自己的账号循环；`SubAccountRotation` 分发 `FindJade` 时调用该薄入口，不启动旧循环。本地和 Windows `py_compile`/导入检查通过；Windows 临时配置验证 `--sub-task FindJade --disable-find-jade` 通过且未改真实配置。23:45 实机尝试已进入 `SubAccountRotation` 且 sub-task 为 `FindJade`，但停在切号阶段，未进入悬赏界面；已停止脚本并恢复 `oas_findjade.json` 备份。2026-06-08 00:04 重跑通过当前账号 skip path：小号切号成功，进入 `FindJade`，悬赏界面检测到 `there is no cooperation quest` 后正常结束。实机“发出协作邀请并由大号消费”仍需在小号存在可邀请悬赏协作且大号 `WantedQuests.scheduler.enable = True` 时单独验证。

- [ ] T011 [US3] 接入商店日常礼包子任务适配器
  - scope: `tasks/SubAccountRotation/`, `tasks/DailyTrifles/`
  - maps_to: US3-2
  - verify: 小号在当前账号登录态进入商店礼包屋，执行 `DailyTrifles.run_store_sign()`，推进免费一抽/50 天黑蛋进度；不得执行 `DailyTrifles` 里的召唤、友情点、吉闻或购买体力等其他日常杂项。
  - current: 2026-06-08 用户澄清：目标不是 `MysteryShop` 神秘商店，而是商店日常礼包 50 天黑蛋进度。现有代码已有 `DailyTrifles.trifles_config.store_sign` 和 `run_store_sign()`。`DailyTriflesStoreSign` 子任务已实现为当前账号薄适配器：临时开启 `store_sign`、临时禁用 `buy_sushi_count`，只调用 `DailyTrifles.run_store()` 的礼包屋路径，结束后恢复原配置，避免触发召唤、友情点、吉闻或买体力。本地和 Windows `py_compile` 通过；Windows helper 临时配置 `--sub-task DailyTriflesStoreSign --disable-find-jade` 通过且真实 `oas_findjade.json` 未改。Windows 实机礼包屋路径仍待验证。此前实现并验证过 `SubAccountRotation -> MysteryShop` 非神秘商店日 skip path，但这是需求误读下的历史适配器，不计入 T011 完成。

- [ ] T012 [US3] 接入 `Hunt` 子任务适配器
  - scope: `tasks/SubAccountRotation/`, `tasks/Hunt/`
  - maps_to: US3-1
  - verify: 非时间窗口能跳过，时间窗口能进入麒麟/阴界流程。
  - current: 2026-06-08 适配器已实现。`SubAccountRotation` 调用现有 `Hunt` 流程，并拦截 `Hunt.scheduler.next_run`，避免轮换子任务污染普通 `Hunt` 调度。本地和 Windows `py_compile`/导入级检查通过。00:27 Windows 实机非战斗时间窗口 skip path 通过：小号切号成功，进入 `Hunt`，日志显示 `Today is the Kirin day`，随后捕获 `SubAccountRotation captured Hunt next_run success=None; keep Hunt scheduler unchanged`。时间窗口内麒麟/阴界战斗路径仍待验证。

- [x] T012A [US4] 接入 `TalismanPass` 花合战/收菜子任务适配器
  - scope: `tasks/SubAccountRotation/`, `tasks/TalismanPass/`
  - maps_to: US4-1
  - verify: 小号领取花合战/可收取奖励，不执行额外日常杂项扩展。
  - current: 2026-06-08 适配器已实现并通过 Windows 隔离实机验证。`SubAccountRotation` 调用现有 `TalismanPass` 流程，并拦截 `TalismanPass.scheduler.next_run`，避免轮换子任务污染普通 `TalismanPass` 调度。本地和 Windows `py_compile` 通过。00:48-00:49 Windows 实机隔离验证通过：小号 `最后的黄泉 / bmkfh1992@126.com` 登录后进入 `TalismanPass`，领取花合战等级奖励，日志显示 `SubAccountRotation captured TalismanPass next_run`，随后 `Scheduler: End task SubAccountRotation`。普通 `talisman_pass.scheduler` 未被改动。正常 harvest 开启的首次验证被登录收取里的 `Harvest mail` 等待超时/app restart 阻断，未到达 TalismanPass；这属于前置登录收取流程干扰，已恢复真实配置为 harvest 开启、轮换关闭。

- [ ] T012B [US2] 接入 `Exploration` 困难28子任务适配器
  - scope: `tasks/SubAccountRotation/`, `tasks/Exploration/`
  - maps_to: US2-2, FR-004
  - verify: 小号按现有探索配置跑困难28，并按现有探索邀请逻辑邀请大号；次数/时长由 `Exploration` 配置手动控制，轮换层不得硬编码。
  - current: 2026-06-08 适配器已实现。`SubAccountRotation` 调用现有 `Exploration` 流程，并拦截 `Exploration.scheduler.next_run`，避免轮换子任务污染普通 `Exploration` 调度。由于现有探索在绘卷/突破票阈值命中时会顺手调度 `RealmRaid` 和 `MemoryScrolls`，轮换适配器显式忽略这些 side-effect `next_run`，保持不接入阴阳寮突破/绘卷类任务的范围边界。探索章节、次数、限时和邀请好友仍由现有 `exploration` 配置控制；配置 helper 可用 `--configure-exploration --main-friend 不知庭院 --exploration-minions-count <n> --exploration-limit-time 00:05:00` 做低风险验证。本地和 Windows `py_compile` 通过。第一次 Windows 实机验证进入 `SubAccountRotation run Exploration` 后，在现有 `Exploration.run_leader()` 的 `WORLD` 场景暴露 `wait_until_stable(..., timeout=5)` 类型错误，已最小修复为 `timeout=Timer(5)` 并同步到 Windows；重跑后小号成功进入 `LEADER` 并越过原报错点，但当前小号等级不到 54，无法进入困难28真实路径，因此 hard-28 邀请/战斗路径被账号等级阻塞。后续需要使用满足等级的小号重跑，或仅为验证适配器通路临时降低探索章节。

- [ ] T012C [US4] 接入 `AreaBoss` 地域鬼王子任务适配器
  - scope: `tasks/SubAccountRotation/`, `tasks/AreaBoss/`
  - maps_to: US4-2
  - verify: 小号执行地域鬼王，失败只记录当前账号，不影响后续小号。
  - current: 2026-06-08 代码层适配器已实现。`SubAccountRotation` 调用现有 `AreaBoss` 流程，并拦截 `AreaBoss.scheduler.next_run`，避免轮换子任务污染普通 `AreaBoss` 调度；同时恢复 `AreaBoss.run()` 会强制改动的 `area_boss.general_battle.lock_team_enable` 内存值，避免本次轮换保存 history 时把该副作用写入普通地域鬼王配置。本地 `py_compile` 通过；真机地域鬼王路径按用户要求后续统一验证。

**明确不接入**: `Pets`、`DemonEncounter`、`Delegation`、`WeeklyTrifles`、`KekkaiUtilize`、`KekkaiActivation`、`RealmRaid`、`RyouToppa`、`Dokan`、`Duel`、`SoulsTidy`、活动类任务。逢魔只保留现有登录/庭院事务里的顺手处理，不作为 `SubAccountRotation` 子任务。

---

## Phase 4: 配置脚本和验证

**目标**: 降低后续新增小号和启用子任务的配置成本。

- [x] T013 [US1] 新增或扩展小号轮换配置脚本
  - scope: `scripts/configure_subaccount_rotation.py` 或 `scripts/configure_findjade_accounts.py`
  - maps_to: FR-007
  - verify: 支持 `--enable`、`--run-now`、`--sub-task <TaskName>`、`--max-accounts-per-run`、`--disable-find-jade`，账号列表复用 `FindJade`。
  - current: 支持 `--configure-orochi`、`--main-friend`、`--orochi-limit-count`，用于验证前把御魂设为小号队长和邀请大号；支持 `--configure-exploration`、`--exploration-minions-count`、`--exploration-limit-time`，用于验证前把探索设为小号队长、困难28、邀请大号并关闭探索内绘卷/突破票联动；支持 `--disable-harvest` 做隔离验证，也支持 `--enable-harvest` 在验证后恢复登录收取和庭院事务。Windows 临时配置文件验证通过，真实 `oas_findjade.json` 未改动。

- [x] T014 [US1] 更新 `AGENTS.md`
  - scope: `AGENTS.md`
  - maps_to: FR-007
  - verify: 后续 agent 能按文档配置小号和启用子任务。

- [x] T015 [US1] 本地静态验证
  - scope: changed files
  - maps_to: NFR-001
  - verify: 语法/导入级检查通过。

- [x] T016 [US1] Windows 双小号实机验证
  - scope: `oas_findjade`
  - maps_to: US1-1, US1-2, Quality 可用性
  - verify: `SubAccountRotation` 启动后两个小号依次切换，执行默认子任务，并更新完成时间。
  - current: 2026-06-07 22:02 Windows 隔离验证通过。`最后的黄泉` 和 `破晓的森林 / CRfalling` 依次完成 `LoginOnly`、登录收取和庭院事务，并分别写入 `history_list_1/2`；`--disable-find-jade` 确认不会继续进入旧 `FindJade`。

- [ ] T017 [US2/US3] 可选实机验证
  - scope: `Orochi`, `FindJade`, 商店日常礼包, `Hunt`, `TalismanPass`, `Exploration`, `AreaBoss`
  - maps_to: US2, US3, US4
  - verify: 分别单独启用一个子任务测试，避免同时打开导致定位困难。
  - current: `Orochi` 已于 2026-06-07 通过 Windows 单小号邀请大号实机验证；`FindJade` 已通过无协作 skip path；`Hunt` 已通过非战斗时间窗口 skip path；`TalismanPass` 已通过隔离实机奖励领取路径。`DailyTriflesStoreSign` 商店日常礼包已实现并通过本地/Windows 静态与 helper 临时配置检查，仍待实机礼包屋路径验证。`Exploration` 已通过 Windows 静态检查，并修复现有探索 leader 分支的 `timeout` 类型错误；hard-28 实机路径当前被小号等级不足阻塞。`AreaBoss` 已完成代码层适配器并通过本地静态检查，真机路径后续统一验证。历史 `MysteryShop` 非神秘商店日 skip path 已通过，但不代表商店日常礼包需求。

---

## 依赖与顺序

- Feature 1 应先完成，否则小号悬赏协作邀请大号仍可能没有消费方。
- T001-T003 必须先于 T004-T012。
- T007/T007A 是 MVP 闭环，必须先于 T009-T012C。
- T008 必须在 T010 前完成，避免与现有 `FindJade` 双重循环冲突。
- T009-T012C 按当前优先级逐个实现和验证，不需要一次性全部打开。
- T013-T014 应在实机长期使用前完成。

---

## 覆盖检查

| 场景 / 需求 | 对应任务 |
|-------------|----------|
| US1 scheduler 驱动小号任务 | T001-T007A, T016 |
| US2 复用组队邀请大号 | T009, T012B, T017；其中 T009 已实机验证 |
| US3 摸麒麟/商店日常礼包 | T011, T012, T017 |
| US4 小号轻量日常 | T012A, T012C, T017 |
| FR-004 不重写组队 | T009, T012B |
| FR-007 简化配置 | T013, T014 |

| 架构决策 / 质量属性 | 对应任务 | 验证任务 |
|----------------------|----------|----------|
| 新增编排任务 | T001-T007A | T016 |
| 组队只调用现有任务 | T009, T012B | T017 |
| 默认只启用 `LoginOnly` | T003 | T016 |
| 可用性 | T005, T007, T007A | T016 |
| 可配置性 | T001, T003, T013 | T013 |

---

## Stage Readiness

- 推荐下一步：代码层面评估并实现可选的商店寄售屋指定式神碎片兑换，或进入本 feature 的静态收口检查；真机层面后续统一验证 T011 商店日常礼包、T012C 地域鬼王、T010 悬赏协作邀请闭环、T012 麒麟/阴界有效窗口路径。T012B `Exploration` 困难28实机验证需等有 54 级以上小号，或明确允许临时降章节只验证适配器通路。
- 阻塞项：T010 邀请闭环依赖小号存在可邀请的悬赏协作，且大号侧 `WantedQuests.scheduler.enable = True`。T012 战斗路径依赖狩猎战/阴界有效时间窗口。T012B 困难28依赖小号等级达到 54。御魂/探索次数沿用现有任务配置，适配器只负责在正确小号登录态下调用。寄售屋指定式神碎片兑换需要先确认现有 UI/assets 是否能选定目标碎片；当前 `RichMan.consignment` 只覆盖购买寄售券。
