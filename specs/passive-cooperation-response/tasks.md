# Implementation Tasks: Passive Cooperation Response

**Workspace**: `passive-cooperation-response`
**Created**: 2026-06-13
**Status**: Draft

---

## Task Breakdown

### Phase 1: 基础架构和御魂邀请 (MVP)

#### T1.1 配置模型实现 ⚙️

**Priority**: P0  
**Estimated**: 4 hours  
**Dependencies**: None

**Tasks**:
1. 在 `module/config/config_model.py` 中新增配置类：
   - `PassiveTaskConfig`
   - `PassiveCooperationConfig`
   - `PassiveConfigModel`
   - `PassiveCooperationResponseConfig`
2. 在 `Config` 顶层添加 `passive_cooperation_response` 字段
3. 运行配置生成脚本，更新 `config_generated.py`
4. 创建默认配置文件 `tasks/PassiveCooperationResponse/config/passive_cooperation_response.yaml`

**验证**:
- [ ] 配置文件可以正常加载
- [ ] 访问 `config.passive_cooperation_response.passive_config.orochi.enable` 不报错
- [ ] 默认配置文件语法正确

**风险**: 配置生成脚本可能需要调整
**缓解**: 参考 `SubAccountRotation` 的配置模型实现

---

#### T1.2 邀请检测模块 - 基础框架 🔍

**Priority**: P0  
**Estimated**: 6 hours  
**Dependencies**: None

**Tasks**:
1. 创建 `tasks/PassiveCooperationResponse/invite_detector.py`
2. 实现 `InviteDetector` 类基础框架：
   ```python
   class InviteDetector:
       def __init__(self, device):
           self.device = device
       
       def detect_invite(self) -> Optional[InviteInfo]:
           pass
       
       def _infer_invite_type(self) -> str:
           pass
       
       def accept_invite(self) -> bool:
           pass
   ```
3. 定义 `InviteInfo` 数据类
4. 添加日志记录框架

**验证**:
- [ ] `InviteDetector` 可以实例化
- [ ] 方法签名正确

---

#### T1.3 邀请弹窗资产准备 🎨

**Priority**: P0  
**Estimated**: 4 hours  
**Dependencies**: T1.2

**Tasks**:
1. 创建 `tasks/PassiveCooperationResponse/assets/` 目录
2. 从 `tasks/Orochi/assets/` 或 `tasks/GeneralInvite/assets/` 复用现有邀请弹窗资产：
   - `INVITE_POPUP`: 通用邀请弹窗检测框
   - `INVITE_ACCEPT_BUTTON`: 接受按钮位置
   - `INVITE_INVITER_NAME_REGION`: OCR 识别邀请者昵称的区域
3. 如需新增资产，使用 dev_tools 截图并标注
4. 创建 `assets/__init__.py` 导出资产

**验证**:
- [ ] 资产文件存在且可导入
- [ ] 在实机截图上测试资产识别准确性

**风险**: 可能需要针对不同邀请类型准备多套资产
**缓解**: 先复用通用资产，Phase 2/3 再细化

---

#### T1.4 邀请检测逻辑实现 🔍

**Priority**: P0  
**Estimated**: 8 hours  
**Dependencies**: T1.2, T1.3

**Tasks**:
1. 实现 `InviteDetector.detect_invite()`：
   - 检测 `INVITE_POPUP` 是否出现
   - OCR 解析邀请者昵称
   - 调用 `_infer_invite_type()` 判断类型
   - 返回 `InviteInfo` 或 `None`
2. 实现 `InviteDetector._infer_invite_type()`：
   - 获取当前页面 `ui_get_current_page()`
   - 根据页面上下文返回邀请类型（御魂/探索/协作）
   - 添加 `unknown` 类型处理
3. 实现 `InviteDetector.accept_invite()`：
   - 点击 `INVITE_ACCEPT_BUTTON`
   - 等待弹窗消失
   - 返回成功/失败

**验证**:
- [ ] 模拟邀请弹窗截图，测试检测准确性
- [ ] OCR 识别邀请者昵称正确
- [ ] 不同上下文页面返回正确的邀请类型

**风险**: OCR 识别可能误识别昵称
**缓解**: 添加白名单过滤，降低误识别影响

---

#### T1.5 主任务框架搭建 🏗️

**Priority**: P0  
**Estimated**: 4 hours  
**Dependencies**: T1.1, T1.2

**Tasks**:
1. 创建 `tasks/PassiveCooperationResponse/__init__.py`
2. 创建 `tasks/PassiveCooperationResponse/script_task.py`
3. 实现 `ScriptTask` 类基础框架：
   ```python
   class ScriptTask(OasScriptTask):
       def __init__(self, config, device):
           super().__init__(config, device)
           self.detector = InviteDetector(device)
           self.accept_counts = {}
       
       def run(self):
           pass
       
       def _should_accept_invite(self, invite) -> bool:
           pass
       
       def _get_rejection_reason(self, invite) -> str:
           pass
       
       def _execute_task(self, invite) -> bool:
           pass
   ```
4. 添加基础日志输出

**验证**:
- [ ] `ScriptTask` 可以实例化
- [ ] 可以从全局 scheduler 启动（通过手动触发测试）

---

#### T1.6 邀请验证逻辑实现 ✅

**Priority**: P0  
**Estimated**: 4 hours  
**Dependencies**: T1.5

**Tasks**:
1. 实现 `_should_accept_invite()`：
   - 检查 `passive_config[task_type].enable`
   - 检查 `max_accept_count` 限制
   - 检查 `allowed_inviters` 白名单
   - 返回 `True/False`
2. 实现 `_get_rejection_reason()`：
   - 返回拒绝原因字符串（用于日志）
3. 实现 `_get_enabled_tasks()` 辅助方法：
   - 返回已启用的任务类型列表

**验证**:
- [ ] 单元测试：不同配置下的验证结果正确
- [ ] 边界情况：空白名单、`max_accept_count=-1`、`max_accept_count=0`

---

#### T1.7 御魂 member 模式接口调研 📚

**Priority**: P0  
**Estimated**: 2 hours  
**Dependencies**: None

**Tasks**:
1. 阅读 `tasks/Orochi/script_task.py` 源码：
   - 确认 `run()` 方法是否根据 `user_status` 自动选择 `run_member()`
   - 确认 `run_member()` 的方法签名和行为
2. 记录调研结果到 `plan.md` 的 "Open Implementation Questions"
3. 决定调用方式：
   - 方式 A: 设置 `user_status=member` 后调用 `run()`
   - 方式 B: 直接调用 `run_member()`

**验证**:
- [ ] 调研结论明确，无歧义

---

#### T1.8 御魂 member 执行逻辑实现 🎯

**Priority**: P0  
**Estimated**: 6 hours  
**Dependencies**: T1.5, T1.7

**Tasks**:
1. 实现 `_execute_orochi_member()`：
   - 保存原始配置（`user_status`, `soul_buff_enable`）
   - 临时修改配置为 member 模式和被动响应加成配置
   - 实例化 `OrochiTask(config, device)`
   - 拦截 `set_next_run` 方法（避免污染 scheduler）
   - 调用 `runner.run()` 或 `runner.run_member()`
   - `finally` 块恢复原始配置
2. 处理 `TaskEnd` 异常（视为成功）
3. 处理 `RequestHumanTakeover` 异常（向上抛出）
4. 添加详细日志

**验证**:
- [ ] 模拟御魂邀请，测试执行流程
- [ ] 验证配置恢复正确（打印恢复后的配置值）
- [ ] 验证 `set_next_run` 被拦截（日志中出现拦截记录）

**风险**: 配置恢复可能在异常时失败
**缓解**: 使用 `try-finally` 确保恢复

---

#### T1.9 主循环实现 🔄

**Priority**: P0  
**Estimated**: 4 hours  
**Dependencies**: T1.4, T1.6, T1.8

**Tasks**:
1. 实现 `ScriptTask.run()` 主循环：
   ```python
   def run(self):
       logger.info("PassiveCooperationResponse: Start listening")
       enabled_tasks = self._get_enabled_tasks()
       logger.info(f"Listening for: {', '.join(enabled_tasks)}")
       
       while True:
           self.screenshot()
           
           # 检测邀请
           invite = self.detector.detect_invite()
           if invite is None:
               sleep(1)
               continue
           
           logger.info(f"Detected {invite.task_type} invite from {invite.inviter_name}")
           
           # 验证配置
           if not self._should_accept_invite(invite):
               logger.info(f"Rejected: {self._get_rejection_reason(invite)}")
               continue
           
           # 接受邀请
           if not self.detector.accept_invite():
               logger.warning("Failed to accept invite")
               continue
           
           # 执行任务
           success = self._execute_task(invite)
           
           # 更新状态
           if success:
               self.accept_counts[invite.task_type] += 1
               logger.info(f"Accepted {invite.task_type} ({self.accept_counts[invite.task_type]})")
           
           # 返回待命态
           self.ui_goto_main()
   ```
2. 添加循环中断条件（如配置变更、手动停止）

**验证**:
- [ ] 主循环可以持续运行
- [ ] 检测到邀请时正确触发执行流程
- [ ] 执行完成后正确返回待命态

---

#### T1.10 端到端测试（御魂） 🧪

**Priority**: P0  
**Estimated**: 4 hours  
**Dependencies**: T1.9

**Tasks**:
1. 准备测试环境：
   - 大号配置：`passive_cooperation_response.passive_config.orochi.enable=true`
   - 小号配置：`SubAccountRotation` 配置 `Orochi` 子任务
2. 手动测试流程：
   - 启动大号 OAS（`PassiveCooperationResponse` 启用）
   - 启动小号 OAS（`SubAccountRotation` 触发御魂邀请）
   - 观察日志和游戏画面
3. 验证检查点：
   - 大号检测到邀请并记录日志
   - 大号接受邀请
   - 大号进入御魂战斗
   - 战斗完成后大号返回主界面
   - 大号继续监听下一次邀请
   - 大号 `orochi.scheduler.next_run` 未被修改

**验证**:
- [ ] 所有检查点通过
- [ ] 无异常或错误日志
- [ ] 配置恢复正确

**风险**: 实机测试可能遇到意外错误
**缓解**: 详细记录日志，逐步调试

---

#### T1.11 加成管理实现（御魂） 🎁

**Priority**: P0  
**Estimated**: 4 hours  
**Dependencies**: T1.8

**Tasks**:
1. 在 `_execute_orochi_member()` 中添加加成管理逻辑：
   - 接受邀请后，检测当前御魂加成状态
   - 如果 `buff_enable=true` 且加成未开启，点击开启
   - 添加日志记录加成状态
2. 从 `tasks/Orochi/assets/` 复用加成按钮和指示器资产
3. 实现 `_ensure_buff_enabled(buff_type, buff_enable)` 辅助方法

**验证**:
- [ ] 配置 `buff_enable=true` 时，加成自动开启
- [ ] 配置 `buff_enable=false` 时，不操作加成
- [ ] 加成已开启时，不重复点击

---

#### T1.12 Phase 1 实机验证和文档 📝

**Priority**: P0  
**Estimated**: 4 hours  
**Dependencies**: T1.10, T1.11

**Tasks**:
1. 编写实机验证脚本（参考 `scripts/verify_orochi.sh`）
2. 完整端到端验证：
   - 单次邀请流程
   - 多轮邀请流程（小号 `limit_count=3`）
   - 次数限制生效（大号 `max_accept_count=2`）
   - 白名单过滤生效
   - 加成自动开启
3. 记录验证结果到 `acceptance.md`
4. 更新 `CLAUDE.md` 或 `AGENTS.md`，说明新功能

**验证**:
- [ ] 所有验证场景通过
- [ ] 文档更新完整

---

### Phase 2: 探索邀请支持

#### T2.1 探索 member 模式接口调研 📚

**Priority**: P1  
**Estimated**: 2 hours  
**Dependencies**: Phase 1 完成

**Tasks**:
1. 阅读 `tasks/Exploration/script_task.py` 源码
2. 确认 member 模式接口
3. 记录调研结果

**验证**:
- [ ] 调研结论明确

---

#### T2.2 探索邀请检测增强 🔍

**Priority**: P1  
**Estimated**: 2 hours  
**Dependencies**: T2.1

**Tasks**:
1. 更新 `InviteDetector._infer_invite_type()`，添加探索邀请识别
2. 从 `tasks/Exploration/assets/` 复用或新增探索邀请资产
3. 添加单元测试

**验证**:
- [ ] 探索邀请上下文识别正确

---

#### T2.3 探索 member 执行逻辑实现 🎯

**Priority**: P1  
**Estimated**: 4 hours  
**Dependencies**: T2.1

**Tasks**:
1. 实现 `_execute_exploration_member()`
2. 添加经验加成管理逻辑
3. 拦截 `set_next_run`

**验证**:
- [ ] 探索 member 流程正确执行
- [ ] 配置恢复正确

---

#### T2.4 探索端到端测试 🧪

**Priority**: P1  
**Estimated**: 4 hours  
**Dependencies**: T2.3

**Tasks**:
1. 准备测试环境
2. 实机验证探索邀请流程
3. 记录验证结果

**验证**:
- [ ] 探索邀请流程通过

---

### Phase 3: 协作邀请支持

#### T3.1 协作邀请检测实现 🔍

**Priority**: P1  
**Estimated**: 2 hours  
**Dependencies**: Phase 1 完成

**Tasks**:
1. 更新 `InviteDetector._infer_invite_type()`，添加协作邀请识别
2. 复用协作邀请独特资产

**验证**:
- [ ] 协作邀请识别正确

---

#### T3.2 协作 member 执行逻辑实现 🎯

**Priority**: P1  
**Estimated**: 4 hours  
**Dependencies**: T3.1

**Tasks**:
1. 实现 `_execute_cooperation_member()`
2. 复用 `cooperation_only` 模式
3. 拦截 `set_next_run`

**验证**:
- [ ] 协作 member 流程正确执行

---

#### T3.3 协作端到端测试 🧪

**Priority**: P1  
**Estimated**: 4 hours  
**Dependencies**: T3.2

**Tasks**:
1. 准备测试环境
2. 实机验证协作邀请流程
3. 记录验证结果

**验证**:
- [ ] 协作邀请流程通过

---

### Phase 4: 完善和文档

#### T4.1 历史记录功能 📊

**Priority**: P2  
**Estimated**: 4 hours  
**Dependencies**: Phase 1-3 完成

**Tasks**:
1. 实现 `InviteHistoryRecord` 数据类
2. 在主循环中记录每次邀请的历史（接受/拒绝、完成状态）
3. 限制历史记录数量（最近 50 条）
4. 添加日志输出历史摘要

**验证**:
- [ ] 历史记录正确保存
- [ ] 历史记录数量限制生效

---

#### T4.2 配置热更新支持 🔄

**Priority**: P2  
**Estimated**: 2 hours  
**Dependencies**: Phase 1 完成

**Tasks**:
1. 在主循环中定期检查配置变更
2. 如配置变更，重新加载 `enabled_tasks` 和 `passive_config`
3. 添加日志记录配置重载

**验证**:
- [ ] 修改配置文件后，任务在下一个检测周期生效

---

#### T4.3 用户文档编写 📚

**Priority**: P2  
**Estimated**: 4 hours  
**Dependencies**: Phase 1-3 完成

**Tasks**:
1. 编写用户配置指南：
   - 如何启用被动响应任务
   - 如何配置白名单和次数限制
   - 如何从 `cooperation_only` 迁移
2. 编写故障排查指南：
   - 邀请未检测到怎么办
   - 加成未开启怎么办
   - 如何查看历史记录
3. 更新 README 或 AGENTS.md

**验证**:
- [ ] 文档完整、清晰

---

#### T4.4 代码审查和清理 🧹

**Priority**: P2  
**Estimated**: 2 hours  
**Dependencies**: Phase 1-3 完成

**Tasks**:
1. 审查代码风格和一致性
2. 移除调试日志和注释
3. 确保所有 TODO 已解决
4. 运行 linter 和格式化工具

**验证**:
- [ ] 代码审查通过
- [ ] 无 linter 警告

---

#### T4.5 最终实机验证 ✅

**Priority**: P2  
**Estimated**: 4 hours  
**Dependencies**: T4.1, T4.2

**Tasks**:
1. 完整功能验证：
   - 御魂、探索、协作三种邀请类型
   - 多轮邀请
   - 次数限制
   - 白名单过滤
   - 加成管理
   - 历史记录
   - 配置热更新
2. 长期稳定性测试（运行 1 小时）
3. 更新 `acceptance.md`

**验证**:
- [ ] 所有功能验证通过
- [ ] 无内存泄漏或性能问题

---

## Task Summary

| Phase | Tasks | Estimated Time |
|---|---|---|
| Phase 1: 基础架构和御魂邀请 | T1.1 - T1.12 | 50 hours (~6 days) |
| Phase 2: 探索邀请支持 | T2.1 - T2.4 | 12 hours (~1.5 days) |
| Phase 3: 协作邀请支持 | T3.1 - T3.3 | 10 hours (~1.2 days) |
| Phase 4: 完善和文档 | T4.1 - T4.5 | 16 hours (~2 days) |
| **总计** | | **88 hours (~11 days)** |

---

## Critical Path

```
T1.1 (配置) → T1.5 (框架) → T1.6 (验证) → T1.9 (主循环) → T1.10 (测试)
                    ↓
              T1.2 (检测器) → T1.3 (资产) → T1.4 (检测逻辑)
                    ↓
              T1.7 (调研) → T1.8 (御魂执行) → T1.11 (加成)
                    ↓
              T1.12 (验证) → Phase 2 → Phase 3 → Phase 4
```

---

## Daily Checklist

在每日开发结束时，检查以下项目：

- [ ] 今日完成的任务已标记为完成
- [ ] 代码已提交到 git，commit message 清晰
- [ ] 遇到的问题和决策已记录到 `plan.md`
- [ ] 如有配置变更，已更新配置文件和文档
- [ ] 如有资产新增，已提交到 git
- [ ] 如有实机测试，已记录结果到 `acceptance.md`

---

## Milestone Checklist

### Milestone 1: Phase 1 完成

- [ ] T1.1 - T1.12 全部完成
- [ ] 御魂邀请端到端流程验证通过
- [ ] 加成管理验证通过
- [ ] `acceptance.md` 更新
- [ ] 代码已推送到 fork

### Milestone 2: Phase 2 完成

- [ ] T2.1 - T2.4 全部完成
- [ ] 探索邀请端到端流程验证通过
- [ ] 代码已推送到 fork

### Milestone 3: Phase 3 完成

- [ ] T3.1 - T3.3 全部完成
- [ ] 协作邀请端到端流程验证通过
- [ ] 代码已推送到 fork

### Milestone 4: Phase 4 完成

- [ ] T4.1 - T4.5 全部完成
- [ ] 用户文档编写完成
- [ ] 最终实机验证通过
- [ ] 准备合并到 master（或创建 PR）

---

**Status**: Ready for implementation
**Next**: 开始 T1.1（配置模型实现）
