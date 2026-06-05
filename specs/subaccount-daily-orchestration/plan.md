# Implementation Plan: Subaccount Daily Orchestration

**Workspace**: `subaccount-daily-orchestration` | **Date**: 2026-06-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/subaccount-daily-orchestration/spec.md`

---

## Summary

新增一个账号轮换层，复用全局 scheduler 和现有 `SwitchAccount`、`FindJade/WantedQuests`、`Hunt`、`MysteryShop`、`Orochi`、`Exploration` 能力。第一版目标不是新增一个大而全任务，而是在 scheduler 启动指定小号任务前切换到正确小号。

---

## Architecture Overview

```text
Global scheduler
  -> choose next pending task as usual
  -> if task is configured as rotated small-account task:
       AccountRotation selects next due account for that task
       SwitchAccount(account)
       LoginHandler / HARVEST keeps courtyard affairs
       run original task unchanged
       update rotation history for task/account
       if more due accounts for this task:
         call/schedule the same task again immediately
  -> if task is not rotated:
       run original task unchanged
```

---

## Producer-Consumer Matrix

| Producer | Artifact | Consumer | Consumption Proof |
|---|---|---|---|
| Global scheduler | 待执行任务 | AccountRotation 层 | 日志显示 task 被判定为 rotated 或 normal |
| AccountRotation 层 | 选中的小号账号 | `SwitchAccount` | 日志显示当前 task 绑定的角色/服务器 |
| `SwitchAccount` | 当前模拟器登录态切到指定小号 | 原任务模块 | 日志显示切号成功后进入原 task |
| 原任务模块 | 任务完成/失败结果 | AccountRotation history | 配置中该 task/account 的完成时间更新 |
| AccountRotation history | 仍有到期账号的同一 task | Global scheduler | 同一 task 被立即重新置为 pending，下一轮切换到下一个账号 |
| `Orochi` / `Exploration` | 组队邀请 | 大号现有邀请接受逻辑 | 小号日志显示房间等待、邀请、开战 |

**孤儿 artifact 处理**: 不新增“子任务执行器”这个中间 artifact。scheduler 仍是任务 producer，原 task 仍是 consumer；账号轮换层只处理登录态前置条件。

---

## Key Design Decisions

### Decision 1: 使用 scheduler 前置账号轮换，而不是新增大而全编排任务

- **背景**: OAS 已经有 scheduler、enable、next_run、priority、failure interval 等能力；用户指出“日程本身支持，只是额外加一层账号切换”。
- **选项**:
  - A: 新增 `SubAccountDaily` 大任务，自己循环账号并调用子任务。闭环强，但重复 scheduler 语义，偏重。
  - B: 保持全局 scheduler，只在指定任务执行前注入账号轮换。更贴近现有架构，改动更小。
  - C: 只手工配置多个任务，不加账号轮换。最简单，但任务会落在当前登录账号上。
- **结论**: 推荐 B。它避免过度设计，同时解决“当前登录账号不一定是目标小号”的问题。
- **影响**: 需要在 `script.py` 任务启动前或 `Config` 任务选择后增加一个账号轮换 hook。
- **来源**: 当前代码 `tasks/FindJade/script_task.py` 已证明账号循环和动态调用任务可行。

### Decision 2: 组队功能只调用现有任务

- **背景**: 用户已有组队功能，仓库中 `Orochi`、`Exploration` 已复用 `GeneralInvite`。
- **选项**:
  - A: 在编排器里重写邀请和房间等待。风险高且重复。
  - B: 编排器只负责切号和调用现有任务，并临时覆写/读取对应配置。
- **结论**: 选择 B。
- **影响**: 编排器需要在调用前确保相关任务配置为小号队长、大号为 `friend_1`、次数/时长有限。
- **来源**: `tasks/Orochi/script_task.py`、`tasks/Exploration/solo.py`、`tasks/Component/GeneralInvite/general_invite.py`。

### Decision 3: 默认先启用低风险子任务

- **背景**: 小号切号刚稳定，组队会占用大号且更容易因为大号忙碌失败。
- **选项**:
  - A: 第一版全部启用。
  - B: 默认启用庭院事务和悬赏协作，`Hunt`/`MysteryShop` 按时间启用，御魂/探索默认关闭。
- **结论**: 选择 B。
- **影响**: 用户可以逐步打开组队子任务，便于定位问题。
- **来源**: 当前实机调试历史。

---

## Module Design

### Module: `tasks/SubAccountRotation/config.py`

**职责**: 定义哪些 scheduler task 需要账号轮换，以及账号池和完成历史。

**改动概述**: 新增账号轮换配置，不新增子任务 scheduler。

**关键接口 / 行为**:

```text
SubAccountRotation:
  account_source = "find_jade"
  rotated_tasks = ["FindJade", "Hunt", "MysteryShop", "Orochi", "Exploration"]
  default_enabled_tasks = ["FindJade"]
  continue_on_switch_failure = true
  per_task_account_history = true
```

**注意事项**:

- 可先共享 `find_jade.sup_account_list`，避免维护两套账号列表。
- 后续如果需要独立小号列表，再抽出通用账号配置。

### Module: scheduler account-rotation hook

**职责**: 在原任务启动前为指定任务切换到应执行的小号。

**改动概述**: 在 `script.py` 启动 task 前，根据 task 名判断是否需要账号轮换；需要则选择下一个 due account 并调用 `SwitchAccount`。

**关键行为**:

```text
task = scheduler_selected_task
if rotation.is_rotated(task):
    account = rotation.next_account(task)
    if account:
        SwitchAccount(config, device, account).switchAccount()
run_original_task(task)
if task_success and rotation.is_rotated(task):
    rotation.update_history(task, account)
    if rotation.has_due_account(task):
        config.task_call(task, force_call=True)
```

**注意事项**:

- 不复制原 task 的 `next_run` 逻辑；只在同一 task 还有到期账号时，把原 task 立即放回 scheduler。
- 失败日志必须带 task 和 account。

### Module: configuration helper scripts

**职责**: 简化配置多个小号和 rotated task 列表。

**改动概述**: 扩展现有 `scripts/configure_findjade_accounts.py` 或新增 `scripts/configure_subaccount_rotation.py`，设置账号、大号昵称、轮换任务和组队 friend。

**注意事项**:

- 继续支持 `--add "昵称:账号"`。
- 可增加 `--rotate Hunt`、`--rotate MysteryShop`、`--rotate Orochi`、`--rotate Exploration`。
- 御魂/探索默认不启用。

### Module: `module/config/config_model.py` and menu

**职责**: 将账号轮换配置接入 OAS 配置模型和 UI 菜单。

**改动概述**: 新增 `sub_account_rotation` 字段；菜单可放在 Script 或 Liver Emperor Exclusive。

---

## Data Model

需要新增轻量配置模型，但不需要单独 `data-model.md`，因为实体关系简单：

- `SubAccountRotationConfig`: 账号来源、轮换任务列表、失败策略。
- `RotatedTaskHistory`: task/account 最近完成时间。
- 账号列表复用 `FindJade.sup_account_list`。

---

## Project Structure

```text
tasks/SubAccountRotation/
  config.py
scripts/
  configure_subaccount_rotation.py
specs/subaccount-daily-orchestration/
  spec.md
  plan.md
```

---

## Risks and Tradeoffs

- 注入 scheduler hook 比新增任务侵入 `script.py` 更多，需要保持 normal task 完全不受影响。
- 复用现有任务意味着会继承现有任务的 OCR/路径问题，账号轮换层只负责切号和历史。
- 大号组队接受依赖另一个 OAS 实例的空闲状态，不能由小号编排器完全保证。

---

## Evolution Path

- **MVP**: 新增账号轮换 hook，默认只轮换 `FindJade`；保留庭院事务；可选打开 `Hunt` 和 `MysteryShop`。
- **成长期**: 稳定后启用 `Orochi`、`Exploration`，增加每账号次数/时间配置。
- **成熟期**: 抽象通用多账号任务框架，支持不同小号不同任务模板和阵容配置。

---

## Verification Strategy

- 配置级：运行配置脚本后，确认账号列表、大号昵称和子任务开关写入正确。
- 单账号实机：只启用一个小号和一个低风险 rotated task，验证 scheduler 启动前切号并更新完成时间。
- 多账号实机：启用两个小号，验证同一 rotated task 的下次运行切到第二个。
- 组队实机：单独启用 `Orochi` 或 `Exploration`，验证小号使用现有组队逻辑邀请大号。
- 回归：确认 `FindJade` 单独运行仍可用。

---

## Stage Readiness

- 是否需要 `data-model.md`：不需要。配置模型简单，可直接在 plan/tasks 中描述。
- 下一步建议：`tasks`
- 阻塞项：御魂/探索每日次数需用户后续决定；不阻塞 MVP，因为默认关闭。

---

## Design Artifacts

| 产物 | 是否需要 | 说明 |
|------|---------|------|
| plan.md | 必须 | 当前文件 |
| data-model.md | 不需要 | 配置实体简单 |
| tasks.md | 后续阶段生成 | 拆具体实现步骤 |
| acceptance.md | 后续阶段生成 | 记录实机验证结论 |
