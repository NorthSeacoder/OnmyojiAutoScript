# Implementation Plan: Subaccount Daily Orchestration

**Workspace**: `subaccount-daily-orchestration` | **Date**: 2026-06-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/subaccount-daily-orchestration/spec.md`

---

## Summary

新增一个小号日常编排任务，复用现有 `SwitchAccount`、`Orochi`、`FindJade/WantedQuests`、`DailyTrifles` 商店日常礼包、`Hunt`、`TalismanPass`、`Exploration`、`AreaBoss` 能力。因为本仓库是基于开源脚本维护的本地 patch，第一版不改全局 scheduler 主循环，不在 `script.py` 注入通用账号轮换 hook，而是把改动集中到新增 `tasks/SubAccountRotation/`、配置模型和配置脚本中，降低后续同步上游时的冲突概率。此前 `MysteryShop` 神秘商店适配器来自需求误读，不再作为当前商店日常目标。

---

## Architecture Overview

```text
Global scheduler
  -> choose SubAccountRotation as a normal scheduled task
  -> SubAccountRotation loads account list and enabled sub-tasks
  -> for each due account:
       SwitchAccount(account)
       LoginHandler / HARVEST keeps courtyard affairs
       run configured sub-task adapter or existing task entry
       update SubAccountRotation history for account/sub-task
  -> SubAccountRotation sets its own next_run
  -> all other upstream tasks keep their original scheduler behavior
```

---

## Producer-Consumer Matrix

| Producer | Artifact | Consumer | Consumption Proof |
|---|---|---|---|
| Global scheduler | `SubAccountRotation` 到期任务 | `tasks/SubAccountRotation/script_task.py` | 日志进入 `SUBACCOUNTROTATION` |
| SubAccountRotation | 选中的小号账号 | `SwitchAccount` | 日志显示当前子任务绑定的角色/服务器 |
| `SwitchAccount` | 当前模拟器登录态切到指定小号 | 子任务适配器 / 现有任务模块 | 日志显示切号成功后进入子任务 |
| 子任务适配器 / 现有任务模块 | 任务完成/失败结果 | SubAccountRotation history | 配置中该 account/sub-task 的完成时间更新 |
| `Orochi` / `Exploration` | 组队邀请 | 大号现有邀请接受逻辑 | 小号日志显示房间等待、邀请、开战 |
| `FindJade` | 悬赏协作邀请 | 大号 `WantedQuests` 闭环 | 小号发出协作，大号日志进入悬赏协作处理 |
| `DailyTrifles.store_sign` / `Hunt` / `TalismanPass` / `AreaBoss` | 当前小号登录态 | 对应现有任务模块 | 子任务日志显示在当前账号执行或按窗口跳过 |

**孤儿 artifact 处理**: 不修改全局 scheduler 的 task artifact。`SubAccountRotation` 作为普通任务消费自己的到期计划，并把账号登录态交给现有任务能力消费。

---

## Key Design Decisions

### Decision 1: 第一版使用独立编排任务，而不是 scheduler 前置 hook

- **背景**: OAS 已经有 scheduler、enable、next_run、priority、failure interval 等能力；用户指出“日程本身支持，只是额外加一层账号切换”。
- **选项**:
  - A: 新增 `SubAccountRotation` 编排任务，自己循环账号并调用子任务。会重复一部分调度语义，但 patch 面集中，后续上游更新冲突更少。
  - B: 保持全局 scheduler，只在指定任务执行前注入账号轮换。架构更通用，但需要改 `script.py`/调度核心，后续同步上游风险高。
  - C: 只手工配置多个任务，不加账号轮换。最简单，但任务会落在当前登录账号上。
- **结论**: 第一版选择 A。它更符合本地 patch 的长期维护目标；如果未来证明需求稳定，再考虑把账号轮换抽象为上游友好的 hook。
- **影响**: `SubAccountRotation` 需要负责自己的 `next_run`、子任务启用、账号/子任务 history；不改变普通任务的 scheduler 行为。
- **来源**: 当前代码 `tasks/FindJade/script_task.py` 已证明账号循环和动态调用任务可行。

### Decision 2: 组队功能只调用现有任务

- **背景**: 用户已有组队功能，仓库中 `Orochi`、`Exploration` 已复用 `GeneralInvite`。
- **选项**:
  - A: 在编排器里重写邀请和房间等待。风险高且重复。
  - B: 编排器只负责切号和调用现有任务，并临时覆写/读取对应配置。
- **结论**: 选择 B。
- **影响**: 编排器需要在调用前确保相关任务配置为小号队长、大号为 `friend_1`、次数/时长有限。若直接调用完整 task 会触发其自身 `set_next_run`，适配器需要明确是否允许改写原 task 调度时间；`FindJade` 纳入轮换前必须拆出“当前账号悬赏协作”入口，不能复用其完整账号循环。
- **来源**: `tasks/Orochi/script_task.py`、`tasks/Exploration/solo.py`、`tasks/Component/GeneralInvite/general_invite.py`。

### Decision 3: 默认只启用 `LoginOnly`，业务子任务按优先级逐个实现

- **背景**: 小号切号已经通过双账号验证，但业务子任务会消耗资源、占用大号或依赖时间窗口；用户已明确当前优先级和排除范围。
- **选项**:
  - A: 第一版全部启用。收益最大，但容易同时触发多个未知路径，定位困难。
  - B: 默认只 `LoginOnly`；业务子任务仅作为配置占位，按 `Orochi`、`FindJade`、`DailyTrifles.store_sign`、`Hunt`、`TalismanPass`、`Exploration`、`AreaBoss` 顺序逐个接入和验证。
- **结论**: 选择 B。
- **影响**: 当前配置可以表达目标范围，但非 `LoginOnly` 子任务在适配器实现和验证前不得标记为完成，也不得默认启用。
- **来源**: 当前实机调试历史和用户 2026-06-07 明确的任务优先级。

---

## Module Design

### Module: `tasks/SubAccountRotation/`

**职责**: 作为一个普通 OAS 任务执行小号日常编排，定义账号池、子任务开关、完成历史和下一次运行时间。

**改动概述**: 新增任务目录，包含 `config.py`、`script_task.py` 和必要的子任务适配器。不修改 `script.py` 主循环。

**关键接口 / 行为**:

```text
SubAccountRotation:
  account_source = "find_jade"
  enabled_sub_tasks = ["LoginOnly"]
  continue_on_switch_failure = true
  per_account_sub_task_history = true
  next_run_policy = "fixed_windows"
```

**注意事项**:

- 可先共享 `find_jade.sup_account_list`，避免维护两套账号列表。
- 现有 `FindJade` 已经包含小号循环；MVP 先保留它作为独立既有任务，不由 `SubAccountRotation` 直接调用，避免两层账号循环互相影响。后续若把悬赏纳入轮换，必须先拆出“当前账号模式”的薄适配器。
- 后续如果需要独立小号列表，再抽出通用账号配置。

### Module: sub-task adapters

**职责**: 在 `SubAccountRotation` 内部复用现有任务能力，避免重写底层 OCR/点击/邀请逻辑。

**改动概述**: 为每个子任务提供薄适配层：选择当前账号、调用已有任务或已有组件、捕获 `TaskEnd`、更新本编排任务的 history。适配层不得改全局 scheduler。

**关键行为**:

```text
for account in due_accounts:
    if SwitchAccount(account):
        for sub_task in enabled_sub_tasks:
            run_adapter(sub_task, account)
            update_history(account, sub_task, success)
set_next_run("SubAccountRotation", next_window)
```

**注意事项**:

- 不在 `script.py` 或 `module/config/config.py` 注入 hook。
- 不把普通 OAS task 标记为 rotated task；`SubAccountRotation` 自己决定子任务顺序。
- 失败日志必须带 task 和 account。

### Module: configuration helper scripts

**职责**: 简化配置多个小号和子任务开关。

**改动概述**: 扩展现有 `scripts/configure_findjade_accounts.py` 或新增 `scripts/configure_subaccount_rotation.py`，设置账号、大号昵称、子任务开关和组队 friend。

**注意事项**:

- 继续支持 `--add "昵称:账号"`。
- 可增加或保留 `--sub-task Orochi`、`--sub-task FindJade`、商店日常礼包子任务、`--sub-task Hunt`、`--sub-task TalismanPass`、`--sub-task Exploration`、`--sub-task AreaBoss`。`MysteryShop` 可作为历史误读下的 dormant adapter 保留，但不应计入当前商店日常礼包需求。
- 默认只写入 `LoginOnly`，业务子任务必须显式开启；脚本只负责配置表达，不代表适配器已经实现。

### Module: `module/config/config_model.py` and menu

**职责**: 将账号轮换配置接入 OAS 配置模型和 UI 菜单。

**改动概述**: 新增 `sub_account_rotation` 字段；菜单加入 `SubAccountRotation`。这是少数必要的上游文件改动，应保持机械、局部、容易重放。

---

## Data Model

需要新增轻量配置模型，但不需要单独 `data-model.md`，因为实体关系简单：

- `SubAccountRotationConfig`: 账号来源、子任务开关、失败策略、下一轮窗口。
- `SubTaskHistory`: account/sub-task 最近完成时间。
- 账号列表复用 `FindJade.sup_account_list`。

---

## Project Structure

```text
tasks/SubAccountRotation/
  config.py
  script_task.py
scripts/
  configure_subaccount_rotation.py
specs/subaccount-daily-orchestration/
  spec.md
  plan.md
```

---

## Risks and Tradeoffs

- 独立编排任务会重复一部分 scheduler 语义，但能避免修改 `script.py` 主循环，后续同步上游更稳。
- 直接调用完整既有任务可能改写该任务自身 `next_run`；适配器需要显式约束这个副作用，必要时先只接可控子任务。
- 复用现有任务意味着会继承现有任务的 OCR/路径问题，账号轮换层只负责切号和历史。
- 大号组队接受依赖另一个 OAS 实例的空闲状态，不能由小号编排器完全保证。
- 明确不接入 `Pets`、独立 `DemonEncounter`、`Delegation`、`WeeklyTrifles`、结界卡、阴阳寮突破、道馆、斗技、整理御魂和活动类任务，避免把长流程和易冲突任务塞进轮换。

---

## Evolution Path

- **MVP**: 新增 `SubAccountRotation` 普通任务，默认只 `LoginOnly`，验证切号、登录收取、庭院事务和 history；不改 `script.py`。
- **成长期**: 按优先级逐个接入 `Orochi`、`FindJade`、`DailyTrifles.store_sign`、`Hunt`、`TalismanPass`、`Exploration`、`AreaBoss`，每个子任务单独验证后再进入默认配置候选。可选扩展为寄售屋指定式神碎片兑换，但现有 `RichMan.consignment` 只买寄售券，不能直接标为完成。
- **成熟期**: 如果长期稳定且值得 upstream 化，再抽象通用多账号 hook，支持不同小号不同任务模板和阵容配置。

---

## Verification Strategy

- 配置级：运行配置脚本后，确认账号列表、大号昵称和子任务开关写入正确。
- 单账号实机：只启用一个小号和 `LoginOnly`，验证 `SubAccountRotation` 内部切号并更新完成时间。
- 多账号实机：启用两个小号，验证同一子任务在两个账号上依次执行。
- 子任务实机：按优先级单独启用 `Orochi`、`FindJade`、商店日常礼包、`Hunt`、`TalismanPass`、`Exploration`、`AreaBoss` 中的一个，验证成功/跳过/失败日志都绑定当前小号。
- 组队实机：单独启用 `Orochi` 或 `Exploration`，验证小号使用现有组队逻辑邀请大号；`Exploration` 限定困难28，次数/时长沿用现有探索配置。
- 回归：确认 `FindJade` 单独运行仍可用。

---

## Stage Readiness

- 是否需要 `data-model.md`：不需要。配置模型简单，可直接在 plan/tasks 中描述。
- 下一步建议：`execute-plan`
- 阻塞项：御魂每日目标次数需后续配置；探索已明确为困难28，但次数/时长沿用现有 `Exploration` 配置。业务子任务不阻塞 MVP，因为默认只启用 `LoginOnly`。

---

## Design Artifacts

| 产物 | 是否需要 | 说明 |
|------|---------|------|
| plan.md | 必须 | 当前文件 |
| data-model.md | 不需要 | 配置实体简单 |
| tasks.md | 已生成 | 拆具体实现步骤 |
| acceptance.md | 后续阶段生成 | 记录实机验证结论 |
